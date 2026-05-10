import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { api, daysUntil, type APIKey, type Provider } from "../lib/api";

function statusBadge(days: number): { label: string; cls: string } {
  if (days < 0) return { label: "Expired", cls: "bg-terracotta/15 text-terracotta-dark" };
  if (days <= 7) return { label: `${days} day${days === 1 ? "" : "s"} left`, cls: "bg-terracotta/15 text-terracotta-dark" };
  if (days <= 30) return { label: `${days} days left`, cls: "bg-amber-100 text-amber-800" };
  return { label: `${days} days left`, cls: "bg-emerald-100 text-emerald-800" };
}

export function Dashboard() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    const [keysData, providersData] = await Promise.all([api.listKeys(), api.listProviders()]);
    setKeys(keysData);
    setProviders(providersData);
    setLoading(false);
  };

  useEffect(() => {
    refresh();
  }, []);

  const providerName = (id: string) => providers.find((p) => p.id === id)?.name ?? id;

  const handleDelete = async (key: APIKey) => {
    if (!confirm(`Delete "${key.name}"?`)) return;
    await api.deleteKey(key.id);
    refresh();
  };

  const handleRotate = async (key: APIKey) => {
    const next = prompt("New expiration date (YYYY-MM-DD):", key.expires_at);
    if (!next) return;
    await api.rotateKey(key.id, next);
    refresh();
  };

  const handleTest = async () => {
    try {
      await api.triggerCheck();
      alert("Daily check triggered. Look at backend logs to see what happened.");
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed");
    }
  };

  if (loading) {
    return (
      <Layout>
        <p className="text-muted">Loading…</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl text-royal mb-1">Your keys</h1>
          <p className="text-muted text-sm">
            {keys.length === 0 ? "No keys tracked yet." : `${keys.length} key${keys.length === 1 ? "" : "s"} being tracked.`}
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleTest} className="btn-secondary">
            Trigger check
          </button>
          <Link to="/new" className="btn-primary">
            + Add key
          </Link>
        </div>
      </div>

      {keys.length === 0 ? (
        <div className="card-panel p-12 text-center">
          <h2 className="text-2xl text-royal mb-2">Add your first key</h2>
          <p className="text-muted mb-6">Track expiration dates and get reminded before they die.</p>
          <Link to="/new" className="btn-primary">
            Add a key
          </Link>
        </div>
      ) : (
        <div className="card-panel divide-y divide-line">
          {keys.map((key) => {
            const days = daysUntil(key.expires_at);
            const badge = statusBadge(days);
            return (
              <div key={key.id} className="p-5 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-medium text-ink truncate">{key.name}</h3>
                    <span className="text-xs uppercase tracking-wider text-muted font-medium">{providerName(key.provider)}</span>
                  </div>
                  <p className="text-sm text-muted mt-0.5">
                    Expires {key.expires_at} · notify J−{key.notify_days_before} via {key.notify_channel}
                  </p>
                </div>
                <span className={`text-xs font-medium px-2.5 py-1 rounded-full whitespace-nowrap ${badge.cls}`}>{badge.label}</span>
                <div className="flex gap-2">
                  <button onClick={() => handleRotate(key)} className="btn-secondary text-xs">
                    Rotated
                  </button>
                  <Link to={`/keys/${key.id}`} className="btn-secondary text-xs">
                    Edit
                  </Link>
                  <button onClick={() => handleDelete(key)} className="btn-secondary text-xs hover:!bg-terracotta/10 hover:!text-terracotta-dark">
                    Delete
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Layout>
  );
}
