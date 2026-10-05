/**
 * Money is a decimal string from the API ("5000.00"). No floating point:
 * parsing goes to integer cents as BigInt, formatting is string-based.
 */
const RE = /^(-)?(\d+)(?:\.(\d{1,2}))?$/;

export function toCents(value: string | number | null | undefined): bigint | null {
  if (value === null || value === undefined || value === "") return null;
  const s = typeof value === "number" ? String(value) : value.trim();
  const m = RE.exec(s);
  if (!m) return null;
  const cents = BigInt(m[2]) * 100n + BigInt((m[3] ?? "").padEnd(2, "0") || "0");
  return m[1] ? -cents : cents;
}

export function fromCents(c: bigint): string {
  const neg = c < 0n;
  const a = neg ? -c : c;
  return `${neg ? "-" : ""}${a / 100n}.${(a % 100n).toString().padStart(2, "0")}`;
}

function group(intPart: string): string {
  return intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/** "15000.50" -> "UGX 15,000.50"; "15000.00" -> "UGX 15,000". */
export function formatUGX(value: string | number | null | undefined, opts: { prefix?: boolean } = {}): string {
  const c = toCents(value);
  if (c === null) return "—";
  const neg = c < 0n;
  const a = neg ? -c : c;
  const whole = group((a / 100n).toString());
  const frac = a % 100n;
  const body = frac === 0n ? whole : `${whole}.${frac.toString().padStart(2, "0")}`;
  return `${neg ? "-" : ""}${opts.prefix === false ? "" : "UGX "}${body}`;
}

export function sumMoney(values: Array<string | null | undefined>): string {
  return fromCents(values.reduce<bigint>((acc, v) => acc + (toCents(v ?? "0") ?? 0n), 0n));
}

export function compareMoney(a: string, b: string): number {
  const x = toCents(a) ?? 0n;
  const y = toCents(b) ?? 0n;
  return x < y ? -1 : x > y ? 1 : 0;
}

/** Validates user input for an amount field (positive, ≤ 2 dp). */
export function isValidAmount(input: string): boolean {
  const c = toCents(input);
  return c !== null && c > 0n;
}
