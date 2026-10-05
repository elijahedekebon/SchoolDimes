/**
 * Role-based routing, shared by the Next.js proxy (route protection) and the
 * login handler. Pure functions so they can be unit-tested.
 *
 * - school_admin  -> /school/...
 * - platform_admin -> /platform/... (cross-tenant reads live under
 *   /platform/support; /school pages are for a single school's admin)
 * - student        -> /student (read-only portal)
 * - parent, canteen_staff, merchant_staff -> refused (they use the mobile
 *   parent app and the POS app).
 */
export type Role =
  | "parent"
  | "student"
  | "canteen_staff"
  | "merchant_staff"
  | "school_admin"
  | "platform_admin";

export const DASHBOARD_ROLES: readonly Role[] = ["school_admin", "platform_admin", "student"];

export const PUBLIC_PREFIXES = ["/login", "/give", "/api/auth", "/_next", "/favicon"];

export function homeFor(role: Role | null | undefined): string | null {
  switch (role) {
    case "school_admin":
      return "/school";
    case "platform_admin":
      return "/platform";
    case "student":
      return "/student";
    default:
      return null;
  }
}

export function isPublicPath(pathname: string): boolean {
  return pathname === "/" ? false : PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/") || pathname.startsWith(p + "?"));
}

function area(pathname: string): "school" | "platform" | "student" | "root" | "other" {
  if (pathname === "/") return "root";
  const seg = pathname.split("/")[1];
  if (seg === "school" || seg === "platform" || seg === "student") return seg;
  return "other";
}

export type RouteDecision =
  | { kind: "allow" }
  | { kind: "redirect"; to: string }
  | { kind: "refuse"; reason: "role_not_allowed" };

/** Decides what to do with a page request, given the signed-in role (or null). */
export function decideRoute(role: Role | null, pathname: string): RouteDecision {
  if (isPublicPath(pathname) || pathname.startsWith("/api/proxy")) return { kind: "allow" };
  if (!role) {
    return { kind: "redirect", to: `/login?next=${encodeURIComponent(pathname)}` };
  }
  const home = homeFor(role);
  if (!home) return { kind: "refuse", reason: "role_not_allowed" };
  const a = area(pathname);
  if (a === "root") return { kind: "redirect", to: home };
  if (a === "school") return role === "school_admin" ? { kind: "allow" } : { kind: "redirect", to: home };
  if (a === "platform") return role === "platform_admin" ? { kind: "allow" } : { kind: "redirect", to: home };
  if (a === "student") return role === "student" ? { kind: "allow" } : { kind: "redirect", to: home };
  // shared signed-in pages (e.g. /refused, /account) are allowed for dashboard roles
  return { kind: "allow" };
}
