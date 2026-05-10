import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Layout } from "../components/Layout";
import { api, type Provider } from "../lib/api";

type Mode = "create" | "edit";

export function KeyForm({ mode }: { mode: Mode }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [name, setName] = useState("");
  const [provider, setProvider] = useState("anthropic");
  const [expiresAt, setExpiresAt] = useState(() => {
    const d = new Date();
    d.setMonth(d.getMonth() + 3);
    return d.toISOString().slice(0, 10);
  });
  const [rotationUrl, setRotationUrl] = useState("");
  const [notifyDaysBefore, setNotifyDaysBefore] = useState("14,7,1");
  const [notifyChannel, setNotifyChannel] = useState("email");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listProviders().then(setProviders);
    if (mode === "edit" && id) {
      api.getKey(parseInt(id)).then((k) => {
        setName(k.name);
        setProvider(k.provider);
        setExpiresAt(k.expires_at);
        setRotationUrl(k.rotation_url ?? "");
        setNotifyDaysBefore(k.notify_days_before);
        setNotifyChannel(k.notify_channel);
        setNotes(k.notes ?? "");
      });
    }
  }, [mode, id]);

  const selectedProvider = providers.find((p) => p.id === provider);
  const placeholderUrl = selectedProvider?.rotation_url ?? "";

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const payload = {
        name,
        provider,
        expires_at: expiresAt,
        rotation_url: rotationUrl.trim() || null,
        notify_days_before: notifyDaysBefore,
        notify_channel: notifyChannel,
        notes: notes.trim() || null,
      };
      if (mode === "create") {
        await api.createKey(payload);
      } else if (id) {
        await api.updateKey(parseInt(id), payload);
      }
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <h1 className="text-4xl text-royal mb-8">{mode === "create" ? "Add a key" : "Edit key"}</h1>
      <form onSubmit={onSubmit} className="card-panel p-8 space-y-5 max-w-2xl">
        <div>
          <label className="label">Name</label>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Anthropic prod" required />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Provider</label>
            <select className="input" value={provider} onChange={(e) => setProvider(e.target.value)}>
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Expires on</label>
            <input className="input" type="date" value={expiresAt} onChange={(e) => setExpiresAt(e.target.value)} required />
          </div>
        </div>
        <div>
          <label className="label">Rotation URL (optional override)</label>
          <input
            className="input"
            value={rotationUrl}
            onChange={(e) => setRotationUrl(e.target.value)}
            placeholder={placeholderUrl || "https://..."}
          />
          <p className="text-xs text-muted mt-1.5">Leave empty to use the default for {selectedProvider?.name ?? "this provider"}.</p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Notify days before</label>
            <input
              className="input"
              value={notifyDaysBefore}
              onChange={(e) => setNotifyDaysBefore(e.target.value)}
              placeholder="14,7,1"
            />
            <p className="text-xs text-muted mt-1.5">Comma-separated thresholds.</p>
          </div>
          <div>
            <label className="label">Notify via</label>
            <select className="input" value={notifyChannel} onChange={(e) => setNotifyChannel(e.target.value)}>
              <option value="email">Email</option>
              <option value="slack">Slack</option>
              <option value="both">Both</option>
            </select>
          </div>
        </div>
        <div>
          <label className="label">Notes (optional)</label>
          <textarea
            className="input min-h-24"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. used by PatriAlta backend, IP-allowlisted"
          />
        </div>
        {error && <p className="text-sm text-terracotta">{error}</p>}
        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? "Saving…" : mode === "create" ? "Add key" : "Save changes"}
          </button>
          <button type="button" onClick={() => navigate("/")} className="btn-secondary">
            Cancel
          </button>
        </div>
      </form>
    </Layout>
  );
}
