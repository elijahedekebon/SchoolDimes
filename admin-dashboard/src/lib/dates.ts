import { TIMEZONE } from "./config";

/** Today's date (YYYY-MM-DD) in Africa/Kampala. */
export function kampalaToday(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
}

export function shiftDay(day: string, delta: number): string {
  const d = new Date(`${day}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + delta);
  return d.toISOString().slice(0, 10);
}

export function formatDateTime(iso: string | null | undefined, locale = "en"): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat(locale === "en" ? "en-GB" : "en-GB", {
    timeZone: TIMEZONE,
    dateStyle: "medium",
    timeStyle: "short",
  }).format(d);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) return iso;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat("en-GB", { timeZone: TIMEZONE, dateStyle: "medium" }).format(d);
}

export function hoursSince(iso: string | null | undefined, now = Date.now()): number | null {
  if (!iso) return null;
  return (now - new Date(iso).getTime()) / 3_600_000;
}
