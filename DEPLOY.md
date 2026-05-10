# Deploying KeyRotate on the PatriAlta server

This guide walks through deploying KeyRotate as `keyrotate.patrialta.fr` next to your existing PatriAlta stack, sharing the same nginx for SSL termination.

Architecture:

```
Internet → PatriAlta nginx (port 443, SSL) ──┬──→ app.patrialta.fr → app-backend
                                              ├──→ beta.patrialta.fr → beta-backend
                                              └──→ keyrotate.patrialta.fr → keyrotate-nginx (internal :80)
                                                                                ├──→ static frontend
                                                                                └──→ /api/, /rotate/ → keyrotate-backend
```

KeyRotate runs its own internal nginx so it stays a fully self-contained project. PatriAlta's nginx only proxies the subdomain through.

## 1. DNS (one-time)

Add an A record:

```
keyrotate.patrialta.fr.   A   <your-server-IP>
```

Wait for propagation (`dig keyrotate.patrialta.fr` should return your IP).

## 2. Create the shared Docker network (one-time, on server)

```bash
sudo docker network create web
```

This network lets PatriAlta's nginx talk to KeyRotate's nginx.

## 3. Clone KeyRotate on the server

```bash
cd ~
git clone <your-github-url-here> keyrotate
```

## 4. Create production `.env` for KeyRotate backend

```bash
cd ~/keyrotate/backend
cp .env.example .env
nano .env
```

Set these values:

```env
APP_PASSWORD=<a-strong-password>
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_urlsafe(48))">
APP_BASE_URL=https://keyrotate.patrialta.fr
BACKEND_BASE_URL=https://keyrotate.patrialta.fr
RESEND_API_KEY=re_xxxxxxxxxxx
RESEND_FROM=KeyRotate <onboarding@resend.dev>
NOTIFY_EMAIL=your.email@example.com
SLACK_WEBHOOK_URL=
CRON_HOUR=8
```

## 5. Update PatriAlta config (additive — non-breaking)

### a) `~/patrialta/docker-compose.yml`

Add the nginx service to the shared `web` network:

```yaml
  nginx:
    # ... existing config ...
    networks:
      - default
      - web

# At the bottom, add:
networks:
  default:
  web:
    external: true
```

### b) `~/patrialta/nginx/nginx.conf`

**Modify the existing HTTP→HTTPS redirect block** (around line 5) to include `keyrotate.patrialta.fr`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name patrialta.fr www.patrialta.fr app.patrialta.fr beta.patrialta.fr keyrotate.patrialta.fr;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

**Add a new HTTPS server block at the end of the file:**

```nginx
# ── keyrotate.patrialta.fr — Key expiration reminders ────
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name keyrotate.patrialta.fr;

    ssl_certificate /etc/letsencrypt/live/keyrotate.patrialta.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/keyrotate.patrialta.fr/privkey.pem;

    location / {
        proxy_pass http://keyrotate-nginx:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

## 6. Restart PatriAlta nginx (picks up the new network)

```bash
cd ~/patrialta
sudo docker compose up -d nginx
```

PatriAlta's nginx will now be on both `patrialta_default` AND `web` networks. The new HTTPS server block will fail to load (no cert yet for the new subdomain) — temporarily comment it out or proceed to step 7 right away. Actually nginx will refuse to reload if cert is missing — see step 7 first.

**Alternative order (safer):** comment out the HTTPS server block for `keyrotate.patrialta.fr` in step 5b for now (keep only the HTTP redirect update), then do step 7, then uncomment and reload.

## 7. Get the SSL cert via certbot

With PatriAlta nginx serving the HTTP redirect for the new subdomain (and the ACME challenge location):

```bash
sudo docker run --rm \
  -v patrialta_certbot_conf:/etc/letsencrypt \
  -v patrialta_certbot_www:/var/www/certbot \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d keyrotate.patrialta.fr \
  --email your.email@example.com \
  --agree-tos --no-eff-email
```

(Volume names use the `patrialta_` prefix because that's how compose names them — verify with `sudo docker volume ls`.)

Once the cert is in place, uncomment the HTTPS block (if you commented it) and reload nginx:

```bash
sudo docker compose -f ~/patrialta/docker-compose.yml exec nginx nginx -s reload
```

## 8. Start KeyRotate

```bash
cd ~/keyrotate
sudo docker compose up -d --build
```

Verify:

```bash
sudo docker ps | grep keyrotate
sudo docker logs keyrotate-backend --tail 50
```

You should see the scheduler announce its next run.

## 9. Test

Open `https://keyrotate.patrialta.fr`, log in with `APP_PASSWORD`, add a key with an expiration in ~5 days, then click "Trigger check". You should get an email within a minute.

## Re-deploying after code changes

After pushing changes to the KeyRotate GitHub repo:

```bash
cd ~/keyrotate && sudo ./deploy.sh
```

It pulls, rebuilds, restarts. The SQLite DB at `~/keyrotate/backend/data/keyrotate.db` persists across deploys (bind-mounted).

## Backup the SQLite DB

```bash
# One-off backup
cp ~/keyrotate/backend/data/keyrotate.db ~/keyrotate-backup-$(date +%F).db

# Or set up a daily cron
echo "0 3 * * * cp ~/keyrotate/backend/data/keyrotate.db ~/keyrotate-backup-\$(date +\%F).db" | crontab -
```

## Troubleshooting

- **`keyrotate.patrialta.fr` returns 502** → KeyRotate's nginx is not reachable from PatriAlta's nginx. Check both are on the `web` network: `sudo docker network inspect web` should show both `patrialta-nginx` and `keyrotate-nginx`.
- **Cert acquisition fails** → DNS not propagated, or PatriAlta's nginx isn't responding on port 80 for the new subdomain.
- **`keyrotate-backend` exits immediately** → check `sudo docker logs keyrotate-backend`. Most often a missing env var or malformed `.env`.
- **Emails not arriving** → check `sudo docker logs keyrotate-backend | grep -i resend`. Look for the 401/403 → see README troubleshooting.
