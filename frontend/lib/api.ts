// Small fetch wrapper that attaches the JWT and handles common error cases.

export async function apiFetch(path: string, token: string | null, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`/api${path}`, { ...options, headers });

  if (res.status === 401) {
    // Token expired/invalid — clear it and force re-login.
    localStorage.removeItem("decisio_token");
    localStorage.removeItem("decisio_user");
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  return res;
}
