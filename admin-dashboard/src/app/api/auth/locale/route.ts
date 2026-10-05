import { type NextRequest, NextResponse } from "next/server";

import { isLocale, LOCALE_COOKIE } from "@/lib/config";

/** POST {locale}: switches the UI language cookie. The client also PATCHes
 * /me {preferred_language} through the proxy so the backend agrees. */
export async function POST(req: NextRequest) {
  const { locale } = await req.json().catch(() => ({}));
  if (!isLocale(locale)) return NextResponse.json({ code: "locale_invalid" }, { status: 400 });
  const res = NextResponse.json({ locale });
  res.cookies.set(LOCALE_COOKIE, locale, { path: "/", sameSite: "lax", maxAge: 365 * 86400 });
  return res;
}
