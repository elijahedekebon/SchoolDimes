import { type NextRequest, NextResponse } from "next/server";

import { apiBaseUrl, isLocale, LOCALE_COOKIE } from "@/lib/config";
import { decodeJwt } from "@/lib/jwt";
import { homeFor, type Role } from "@/lib/roles";
import { setAuthCookies, type TokenPair } from "@/lib/server/tokens";

/**
 * POST {email, password}. Logs in against the backend, refuses roles that
 * don't use the web dashboard (parents -> mobile app, canteen/merchant staff
 * -> POS app) and stores the tokens in httpOnly cookies.
 */
export async function POST(req: NextRequest) {
  const { email, password } = await req.json().catch(() => ({}));
  const upstream = await fetch(`${apiBaseUrl()}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(req.headers.get("x-forwarded-for") ? { "X-Forwarded-For": req.headers.get("x-forwarded-for")! } : {}),
    },
    body: JSON.stringify({ email, password }),
    cache: "no-store",
  });
  const data = await upstream.json().catch(() => ({}));
  if (!upstream.ok) return NextResponse.json(data, { status: upstream.status });

  const tokens = data as TokenPair;
  const claims = decodeJwt(tokens.access);
  const role = (claims?.role ?? null) as Role | null;
  const home = homeFor(role);
  if (!home) {
    // Don't leave a usable session behind for a refused role.
    await fetch(`${apiBaseUrl()}/api/v1/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${tokens.access}` },
      body: JSON.stringify({ refresh: tokens.refresh }),
    }).catch(() => undefined);
    return NextResponse.json({ code: "role_not_allowed", role }, { status: 403 });
  }
  const res = NextResponse.json({ role, home });
  setAuthCookies(res, tokens);
  if (isLocale(claims?.preferred_language)) {
    res.cookies.set(LOCALE_COOKIE, claims!.preferred_language!, { path: "/", sameSite: "lax", maxAge: 365 * 86400 });
  }
  return res;
}
