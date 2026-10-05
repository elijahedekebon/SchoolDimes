import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { forward } from "./forward";

function jwt(claims: Record<string, unknown>): string {
  const b = (o: unknown) => Buffer.from(JSON.stringify(o)).toString("base64url");
  return `${b({ alg: "HS256" })}.${b(claims)}.sig`;
}
const now = () => Math.floor(Date.now() / 1000);

describe("API proxy token refresh", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://backend:8000";
  });
  afterEach(() => vi.unstubAllGlobals());

  it("refreshes an expired access token once, retries, and rotates both cookies", async () => {
    const expired = jwt({ role: "school_admin", exp: now() - 10 });
    const fresh = jwt({ role: "school_admin", exp: now() + 1800 });
    const newRefresh = jwt({ token_type: "refresh", exp: now() + 86400 });
    const calls: Array<{ url: string; auth?: string }> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init: RequestInit) => {
        const auth = (init.headers as Record<string, string>)?.Authorization;
        calls.push({ url, auth });
        if (url.endsWith("/auth/refresh")) {
          return new Response(JSON.stringify({ access: fresh, refresh: newRefresh }), { status: 200 });
        }
        return new Response(JSON.stringify({ ok: auth === `Bearer ${fresh}` }), {
          status: auth === `Bearer ${fresh}` ? 200 : 401,
          headers: { "content-type": "application/json" },
        });
      }),
    );
    const req = new NextRequest("http://localhost:3000/api/proxy/students/?page=2", {
      headers: { cookie: `sd_access=${expired}; sd_refresh=old-refresh` },
    });
    const res = await forward(req, "/api/proxy");
    expect(res.status).toBe(200);
    expect(calls[0].url).toBe("http://backend:8000/api/v1/auth/refresh");
    expect(calls[1]).toEqual({ url: "http://backend:8000/api/v1/students/?page=2", auth: `Bearer ${fresh}` });
    expect(res.cookies.get("sd_access")?.value).toBe(fresh);
    expect(res.cookies.get("sd_refresh")?.value).toBe(newRefresh);
  });

  it("clears cookies and flags the session as expired when refresh fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ detail: "no" }), { status: 401 })),
    );
    const req = new NextRequest("http://localhost:3000/api/proxy/me", {
      headers: { cookie: `sd_access=${jwt({ exp: now() + 600 })}; sd_refresh=bad-refresh` },
    });
    const res = await forward(req, "/api/proxy");
    expect(res.status).toBe(401);
    expect(res.headers.get("x-session-expired")).toBe("1");
    expect(res.cookies.get("sd_access")?.value).toBe("");
  });

  it("public pass-through never sends credentials", async () => {
    const seen: Array<Record<string, string>> = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: string, init: RequestInit) => {
        seen.push(init.headers as Record<string, string>);
        return new Response("{}", { status: 200 });
      }),
    );
    const req = new NextRequest("http://localhost:3000/api/public/topup-links/tok/", {
      headers: { cookie: `sd_access=${jwt({ exp: now() + 600 })}` },
    });
    await forward(req, "/api/public");
    expect(seen[0].Authorization).toBeUndefined();
  });
});
