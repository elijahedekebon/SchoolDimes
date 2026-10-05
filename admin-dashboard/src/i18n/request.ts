import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";

import { isLocale, LOCALE_COOKIE } from "@/lib/config";

/**
 * Locale without URL prefixes: read from the NEXT_LOCALE cookie, which the
 * login handler sets from the user's preferred_language and the language
 * switcher updates (and PATCHes /me so the backend agrees).
 */
export default getRequestConfig(async () => {
  const store = await cookies();
  const cookieLocale = store.get(LOCALE_COOKIE)?.value;
  const locale = isLocale(cookieLocale) ? cookieLocale : "en";
  const en = (await import("../../messages/en.json")).default;
  const own = locale === "en" ? en : (await import(`../../messages/${locale}.json`)).default;
  return { locale, messages: deepMerge(en, own), timeZone: "Africa/Kampala" };
});

// Missing lg/sw keys fall back to English (see docs/TRANSLATIONS_TODO.md).
function deepMerge(base: Record<string, unknown>, over: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = { ...base };
  for (const [k, v] of Object.entries(over)) {
    out[k] =
      v && typeof v === "object" && !Array.isArray(v) && typeof base[k] === "object"
        ? deepMerge(base[k] as Record<string, unknown>, v as Record<string, unknown>)
        : v;
  }
  return out;
}
