const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  auth: {
    register: (data: { name: string; email: string; password: string }) =>
      request<{ access_token: string; user: any }>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    login: (email: string, password: string) => {
      const form = new URLSearchParams({ username: email, password });
      return request<{ access_token: string; user: any }>("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });
    },
    me: () => request<any>("/api/auth/me"),
  },

  sessions: {
    list: () => request<any[]>("/api/sessions/"),
    get: (id: string) => request<any>(`/api/sessions/${id}`),
    create: (data: { domain: string; difficulty: string; mode: string }) =>
      request<any>("/api/sessions/", { method: "POST", body: JSON.stringify(data) }),
    domains: () => request<any[]>("/api/sessions/domains"),
  },

  recordings: {
    upload: async (sessionId: string, blob: Blob) => {
      const token = getToken();
      const form = new FormData();
      form.append("file", blob, `${sessionId}.webm`);
      const res = await fetch(`${BASE_URL}/api/recordings/${sessionId}/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      });
      if (!res.ok) throw new Error("Upload failed");
      return res.json();
    },
    url: (filename: string) => {
      const token = getToken();
      return `${BASE_URL}/api/recordings/${filename}${token ? `?token=${token}` : ""}`;
    },
  },

  admin: {
    stats: () => request<any>("/api/admin/stats"),
    users: () => request<any[]>("/api/admin/users"),
    promoteUser: (id: string) =>
      request<any>(`/api/admin/users/${id}/promote`, { method: "POST" }),
    demoteUser: (id: string) =>
      request<any>(`/api/admin/users/${id}/demote`, { method: "POST" }),
    deleteUser: (id: string) =>
      request<any>(`/api/admin/users/${id}`, { method: "DELETE" }),
    sessions: (userId?: string) =>
      request<any[]>(`/api/admin/sessions${userId ? `?user_id=${userId}` : ""}`),
    session: (id: string) => request<any>(`/api/admin/sessions/${id}`),
    deleteSession: (id: string) =>
      request<any>(`/api/admin/sessions/${id}`, { method: "DELETE" }),
    recordings: () => request<any[]>("/api/admin/recordings"),
    deleteRecording: (filename: string) =>
      request<any>(`/api/admin/recordings/${filename}`, { method: "DELETE" }),
    recordingUrl: (filename: string) => {
      const token = getToken();
      return `${BASE_URL}/api/admin/recordings/${filename}${token ? `?token=${token}` : ""}`;
    },
  },
};
