/**
 * Typed API client for the browser. Every call goes to the dashboard's own
 * /api/proxy, which attaches the httpOnly-cookie JWT and refreshes it.
 * Paths are written exactly as in docs/API_CONTRACTS.md, e.g. "/students/".
 */
export type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] } & Record<
  string,
  unknown
>;

export class ApiError extends Error {
  status: number;
  code: string | null;
  detail: string | null;
  fields: Record<string, string[]>;
  violations: string[];
  body: unknown;

  constructor(status: number, body: unknown) {
    const b = (body && typeof body === "object" ? body : {}) as Record<string, unknown>;
    const code = typeof b.code === "string" ? b.code : null;
    const detail = typeof b.detail === "string" ? b.detail : null;
    const fields: Record<string, string[]> = {};
    for (const [k, v] of Object.entries(b)) {
      if (["code", "detail", "violations"].includes(k)) continue;
      if (Array.isArray(v) && v.every((x) => typeof x === "string")) fields[k] = v as string[];
    }
    super(detail || code || Object.values(fields).flat()[0] || `HTTP ${status}`);
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.fields = fields;
    this.violations = Array.isArray(b.violations) ? (b.violations as string[]) : [];
    this.body = body;
  }

  /** Human-readable message: the backend's own (already translated) text. */
  get display(): string {
    if (this.detail) return this.detail;
    const f = Object.entries(this.fields).map(([k, v]) => (k === "non_field_errors" ? v.join(" ") : `${k}: ${v.join(" ")}`));
    if (f.length) return f.join(" · ");
    return this.code || this.message;
  }
}

export type Query = Record<string, string | number | boolean | null | undefined>;

export function buildQuery(q?: Query): string {
  if (!q) return "";
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(q)) {
    if (v === undefined || v === null || v === "") continue;
    p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

type Options = { method?: string; body?: unknown; query?: Query; base?: "/api/proxy" | "direct"; raw?: boolean };

let onSessionExpired: (() => void) | null = null;
export function setSessionExpiredHandler(fn: () => void) {
  onSessionExpired = fn;
}

export async function apiFetch<T = unknown>(path: string, opts: Options = {}): Promise<T> {
  const base = opts.base ?? "/api/proxy";
  // "direct": unauthenticated public endpoints, called from the browser so the
  // backend's per-IP throttle sees each contributor's own IP (see DECISIONS.md).
  const prefix = base === "direct" ? `${(process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/+$/, "")}/api/v1` : base;
  const url = `${prefix}${path}${buildQuery(opts.query)}`;
  const init: RequestInit = {
    method: opts.method ?? "GET",
    headers: { Accept: "application/json" },
    credentials: base === "direct" ? "omit" : "same-origin",
  };
  if (opts.body !== undefined) {
    (init.headers as Record<string, string>)["Content-Type"] = "application/json";
    init.body = JSON.stringify(opts.body);
  }
  const res = await fetch(url, init);
  if (res.status === 401 && base === "/api/proxy" && res.headers.get("x-session-expired")) {
    onSessionExpired?.();
  }
  if (opts.raw) {
    if (!res.ok) throw new ApiError(res.status, await res.json().catch(() => ({})));
    return res as unknown as T;
  }
  if (res.status === 204 || res.status === 205) return undefined as T;
  const text = await res.text();
  let data: unknown = undefined;
  try {
    data = text ? JSON.parse(text) : undefined;
  } catch {
    data = { detail: text.slice(0, 200) };
  }
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

export const api = {
  get: <T>(path: string, query?: Query) => apiFetch<T>(path, { query }),
  post: <T>(path: string, body?: unknown, query?: Query) => apiFetch<T>(path, { method: "POST", body: body ?? {}, query }),
  patch: <T>(path: string, body: unknown) => apiFetch<T>(path, { method: "PATCH", body }),
  put: <T>(path: string, body: unknown) => apiFetch<T>(path, { method: "PUT", body }),
  del: <T>(path: string) => apiFetch<T>(path, { method: "DELETE" }),
};

/** Fetches every page of a paginated list (for CSV exports). */
export async function fetchAll<T>(path: string, query?: Query, maxPages = 50): Promise<T[]> {
  const out: T[] = [];
  for (let page = 1; page <= maxPages; page++) {
    const data = await api.get<Paginated<T>>(path, { ...query, page, page_size: 100 });
    out.push(...data.results);
    if (!data.next) break;
  }
  return out;
}

export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}
