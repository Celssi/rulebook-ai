const API = "/api";

export function parseErrorBody(text: string, fallback: string): string {
  try {
    const body = JSON.parse(text) as { detail?: string | { msg: string }[] };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d) => d.msg).join("; ");
    }
  } catch {
    /* plain text */
  }
  return text || fallback;
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(parseErrorBody(text, res.statusText));
  }
  return res.json() as Promise<T>;
}

export { API };
