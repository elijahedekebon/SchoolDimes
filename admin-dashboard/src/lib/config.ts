/** Backend origin, e.g. http://localhost:8000 (never hardcoded elsewhere). */
export function apiBaseUrl(): string {
  const url = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!url) throw new Error("Set NEXT_PUBLIC_API_BASE_URL (see admin-dashboard/.env.example)");
  return url.replace(/\/+$/, "");
}

export const ACCESS_COOKIE = "sd_access";
export const REFRESH_COOKIE = "sd_refresh";
export const LOCALE_COOKIE = "NEXT_LOCALE";
export const LOCALES = ["en", "lg", "sw"] as const;
export type Locale = (typeof LOCALES)[number];
export const TIMEZONE = "Africa/Kampala";

export function isLocale(v: string | undefined | null): v is Locale {
  return !!v && (LOCALES as readonly string[]).includes(v);
}
