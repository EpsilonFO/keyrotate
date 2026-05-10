export type Provider = { id: string; name: string; rotation_url: string | null };

export type APIKey = {
  id: number;
  name: string;
  provider: string;
  expires_at: string;
  rotation_url: string | null;
  notify_days_before: string;
  notify_channel: string;
  status: string;
  notes: string | null;
  notified_thresholds: string;
  created_at: string;
  last_rotated_at: string | null;
};

export type KeyInput = {
  name: string;
  provider: string;
  expires_at: string;
  rotation_url?: string | null;
  notify_days_before?: string;
  notify_channel?: string;
  notes?: string | null;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  if (res.status === 401) {
    throw new Error("UNAUTHORIZED");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json();
}

export const api = {
  login: (password: string) => request<{ ok: true }>("/api/auth/login", { method: "POST", body: JSON.stringify({ password }) }),
  logout: () => request<{ ok: true }>("/api/auth/logout", { method: "POST" }),
  me: () => request<{ authenticated: true }>("/api/auth/me"),
  listKeys: () => request<APIKey[]>("/api/keys"),
  createKey: (input: KeyInput) => request<APIKey>("/api/keys", { method: "POST", body: JSON.stringify(input) }),
  getKey: (id: number) => request<APIKey>(`/api/keys/${id}`),
  updateKey: (id: number, input: Partial<KeyInput>) =>
    request<APIKey>(`/api/keys/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
  deleteKey: (id: number) => request<void>(`/api/keys/${id}`, { method: "DELETE" }),
  rotateKey: (id: number, new_expires_at: string) =>
    request<APIKey>(`/api/keys/${id}/rotate`, { method: "POST", body: JSON.stringify({ new_expires_at }) }),
  listProviders: () => request<Provider[]>("/api/providers"),
  triggerCheck: () => request<{ ok: true }>("/api/_run_check", { method: "POST" }),
};

export function daysUntil(dateStr: string): number {
  const target = new Date(dateStr + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.floor((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}
