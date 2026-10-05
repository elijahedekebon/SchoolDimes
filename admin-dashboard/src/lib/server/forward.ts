import { type NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl, LOCALE_COOKIE, REFRESH_COOKIE } from "@/lib/config";
import { decodeJwt, isExpired } from "@/lib/jwt";

import { clearAuthCookies, refreshTokens, setAuthCookies, type TokenPair } from "./tokens";

const PASS_RESPONSE_HEADERS = ["content-type", "content-disposition", "retry-after"];

/**
 * Forwards a browser request on /api/proxy/<rest> to <backend>/api/v1/<rest>,
 * adding the Bearer token from the httpOnly cookie. If the access token is
 * expired (or the backend answers 401) it refreshes once and retries.
 * When /api/public/<rest> is used, no credentials are attached at all.
 */
export async function forward(req: NextRequest, prefix: "/api/proxy" | "/api/public"): Promise<NextResponse> {
  const rest = req.nextUrl.pathname.slice(prefix.length) || "/";
  const target = `${apiBaseUrl()}/api/v1${prefix === "/api/public" ? "/public" : ""}${rest}${req.nextUrl.search}`;
  const body = ["GET", "HEAD"].includes(req.method) ? undefined : await req.arrayBuffer();
  const locale = req.cookies.get(LOCALE_COOKIE)?.value;

  const send = (access?: string) => {
    const headers: Record<string, string> = { Accept: req.headers.get("accept") || "application/json" };
    const ct = req.headers.get("content-type");
    if (ct) headers["Content-Type"] = ct;
    if (locale) headers["Accept-Language"] = locale;
    if (access) headers["Authorization"] = `Bearer ${access}`;
    const fwd = req.headers.get("x-forwarded-for");
    if (fwd) headers["X-Forwarded-For"] = fwd;
    return fetch(target, { method: req.method, headers, body, cache: "no-store", redirect: "manual" });
  };

  if (prefix === "/api/public") return toNext(await send());

  let access = req.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = req.cookies.get(REFRESH_COOKIE)?.value;
  let rotated: TokenPair | null = null;

  if ((!access || isExpired(decodeJwt(access))) && refresh) {
    rotated = await refreshTokens(refresh);
    access = rotated?.access;
  }
  let upstream = await send(access);
  if (upstream.status === 401 && refresh && !rotated) {
    rotated = await refreshTokens(refresh);
    if (rotated) upstream = await send(rotated.access);
  }
  const res = toNext(upstream);
  if (rotated) setAuthCookies(res, rotated);
  else if (upstream.status === 401) {
    clearAuthCookies(res);
    res.headers.set("x-session-expired", "1");
  }
  return res;
}

function toNext(upstream: Response): NextResponse {
  const headers = new Headers();
  for (const h of PASS_RESPONSE_HEADERS) {
    const v = upstream.headers.get(h);
    if (v) headers.set(h, v);
  }
  return new NextResponse(upstream.status === 204 || upstream.status === 205 ? null : upstream.body, {
    status: upstream.status,
    headers,
  });
}
