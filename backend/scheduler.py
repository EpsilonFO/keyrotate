import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from auth import create_rotation_token
from config import settings
from db import engine
from models import APIKey
from notifications.email import render_email, send_email
from notifications.slack import send_slack
from providers import PROVIDERS

logger = logging.getLogger(__name__)


def _build_mark_rotated_url(key_id: int, threshold: int) -> str:
    token = create_rotation_token(key_id, threshold)
    return f"{settings.backend_base_url}/rotate/{token}"


def _process_key(session: Session, key: APIKey) -> None:
    days_left = (key.expires_at - date.today()).days
    provider_name = PROVIDERS.get(key.provider, {}).get("name", key.provider)
    rotation_url = key.rotation_url or PROVIDERS.get(key.provider, {}).get("rotation_url")

    if days_left < 0 and key.status != "expired":
        key.status = "expired"
        session.add(key)

    for threshold in key.thresholds():
        if days_left <= threshold and not key.already_notified(threshold):
            mark_rotated_url = _build_mark_rotated_url(key.id, threshold)
            logger.info("Notifying for key id=%s threshold=%s days_left=%s", key.id, threshold, days_left)

            channels = key.notify_channel.split(",")
            email_sent = False
            if "email" in channels or "both" in channels:
                if settings.notify_email:
                    subject, html = render_email(key.name, provider_name, max(days_left, 0), rotation_url, mark_rotated_url)
                    try:
                        send_email(settings.notify_email, subject, html)
                        email_sent = True
                    except Exception as exc:
                        logger.error("Email send failed for key id=%s: %s", key.id, exc)
                        return  # don't cascade through other thresholds when email is broken
                else:
                    logger.warning("NOTIFY_EMAIL not set; skipping email for key id=%s", key.id)
            if "slack" in channels or "both" in channels:
                send_slack(key.name, provider_name, max(days_left, 0), rotation_url, mark_rotated_url)

            if email_sent or "slack" in channels or "both" in channels:
                key.mark_notified(threshold)
                session.add(key)
            break  # one notification per run is enough — next thresholds will fire on later days


def run_daily_check() -> None:
    logger.info("Running daily key check...")
    with Session(engine) as session:
        keys = list(session.exec(select(APIKey).where(APIKey.status == "active")).all())
        for key in keys:
            try:
                _process_key(session, key)
            except Exception as exc:
                logger.exception("Failed processing key id=%s: %s", key.id, exc)
        session.commit()
    logger.info("Daily key check done. %d active keys processed.", len(keys))


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_daily_check,
        CronTrigger(hour=settings.cron_hour, minute=0),
        id="daily_key_check",
        replace_existing=True,
    )
    scheduler.start()
    next_run = scheduler.get_job("daily_key_check").next_run_time
    logger.info("Scheduler started. Next check scheduled at %s.", next_run)

    # Catch up immediately on startup so missed notifications fire after restart.
    try:
        run_daily_check()
    except Exception as exc:
        logger.exception("Initial startup check failed: %s", exc)

    return scheduler
