import { type NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/config";
import { decodeJwt } from "@/lib/jwt";
import { decideRoute, type Role } from "@/lib/roles";

/**
 * Optimistic route protection (Next.js 16 "proxy", formerly middleware).
 * The role comes from the token claims; the backend still authorises every
 * API call, so a forged cookie gets a page shell with no data.
 */
export function proxy(req: NextRequest) {
  const token = req.cookies.get(ACCESS_COOKIE)?.value || req.cookies.get(REFRESH_COOKIE)?.value;
  const role = (decodeJwt(token)?.role ?? null) as Role | null;
  const decision = decideRoute(role, req.nextUrl.pathname);
  if (decision.kind === "redirect") return NextResponse.redirect(new URL(decision.to, req.url));
  if (decision.kind === "refuse") return NextResponse.redirect(new URL("/login?refused=1", req.url));
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/).*)"],
};
