/**
 * Reads (does NOT verify) the claims of a SchoolDimes JWT. The backend
 * verifies every token on every call; the dashboard only uses the claims for
 * routing decisions and cookie lifetimes.
 */
export type Claims = {
  user_id?: number;
  role?: string;
  school_id?: number | null;
  preferred_language?: string;
  exp?: number;
  token_type?: string;
};

export function decodeJwt(token: string | undefined | null): Claims | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = b64 + "=".repeat((4 - (b64.length % 4)) % 4);
    const json =
      typeof atob === "function"
        ? decodeURIComponent(
            Array.from(atob(padded))
              .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
              .join(""),
          )
        : Buffer.from(padded, "base64").toString("utf8");
    return JSON.parse(json) as Claims;
  } catch {
    return null;
  }
}

export function isExpired(claims: Claims | null, skewSeconds = 30): boolean {
  if (!claims?.exp) return true;
  return claims.exp * 1000 <= Date.now() + skewSeconds * 1000;
}
