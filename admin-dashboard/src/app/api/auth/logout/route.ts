import { type NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, apiBaseUrl, REFRESH_COOKIE } from "@/lib/config";
import { clearAuthCookies } from "@/lib/server/tokens";

/** Blacklists the refresh token on the backend and clears the cookies. */
export async function POST(req: NextRequest) {
  const access = req.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = req.cookies.get(REFRESH_COOKIE)?.value;
  if (refresh) {
    await fetch(`${apiBaseUrl()}/api/v1/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(access ? { Authorization: `Bearer ${access}` } : {}) },
      body: JSON.stringify({ refresh }),
    }).catch(() => undefined);
  }
  const res = NextResponse.json({ ok: true });
  clearAuthCookies(res);
  return res;
}
