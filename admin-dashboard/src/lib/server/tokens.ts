import type { NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl, REFRESH_COOKIE } from "@/lib/config";
import { decodeJwt } from "@/lib/jwt";

export type TokenPair = { access: string; refresh: string };

const secure = () => process.env.COOKIE_SECURE === "true";

function maxAgeFor(token: string, fallbackSeconds: number): number {
  const exp = decodeJwt(token)?.exp;
  if (!exp) return fallbackSeconds;
  return Math.max(0, Math.floor(exp - Date.now() / 1000));
}

/** httpOnly, SameSite=Lax cookies: JS in the page can never read the tokens. */
export function setAuthCookies(res: NextResponse, tokens: TokenPair) {
  const base = { httpOnly: true, sameSite: "lax" as const, secure: secure(), path: "/" };
  res.cookies.set(ACCESS_COOKIE, tokens.access, { ...base, maxAge: maxAgeFor(tokens.access, 1800) });
  res.cookies.set(REFRESH_COOKIE, tokens.refresh, { ...base, maxAge: maxAgeFor(tokens.refresh, 7 * 86400) });
}

export function clearAuthCookies(res: NextResponse) {
  res.cookies.set(ACCESS_COOKIE, "", { path: "/", maxAge: 0 });
  res.cookies.set(REFRESH_COOKIE, "", { path: "/", maxAge: 0 });
}

// Refresh tokens rotate (the old one is blacklisted on use), so concurrent
// requests that all see an expired access token must share ONE refresh call.
const inflight = new Map<string, Promise<TokenPair | null>>();

export function refreshTokens(refresh: string): Promise<TokenPair | null> {
  const existing = inflight.get(refresh);
  if (existing) return existing;
  const p = (async () => {
    try {
      const r = await fetch(`${apiBaseUrl()}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
        cache: "no-store",
      });
      if (!r.ok) return null;
      const data = (await r.json()) as TokenPair;
      return data.access && data.refresh ? data : null;
    } catch {
      return null;
    } finally {
      // keep the result briefly so late arrivals with the old token reuse it
      setTimeout(() => inflight.delete(refresh), 10_000);
    }
  })();
  inflight.set(refresh, p);
  return p;
}
