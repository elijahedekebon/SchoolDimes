import { describe, expect, it } from "vitest";

import { decideRoute } from "./roles";

describe("decideRoute (role-based route protection)", () => {
  it("sends anonymous users to login, keeping the destination", () => {
    expect(decideRoute(null, "/school/students")).toEqual({ kind: "redirect", to: "/login?next=%2Fschool%2Fstudents" });
  });

  it("lets anyone reach public pages", () => {
    expect(decideRoute(null, "/login")).toEqual({ kind: "allow" });
    expect(decideRoute(null, "/give/abc123")).toEqual({ kind: "allow" });
  });

  it("school_admin reaches /school but never /platform", () => {
    expect(decideRoute("school_admin", "/school/devices")).toEqual({ kind: "allow" });
    expect(decideRoute("school_admin", "/platform")).toEqual({ kind: "redirect", to: "/school" });
    expect(decideRoute("school_admin", "/platform/audit-log")).toEqual({ kind: "redirect", to: "/school" });
  });

  it("platform_admin reaches /platform (incl. cross-school support), not a single school's admin pages", () => {
    expect(decideRoute("platform_admin", "/platform/support")).toEqual({ kind: "allow" });
    expect(decideRoute("platform_admin", "/school")).toEqual({ kind: "redirect", to: "/platform" });
  });

  it("students only reach the student portal", () => {
    expect(decideRoute("student", "/student")).toEqual({ kind: "allow" });
    expect(decideRoute("student", "/school")).toEqual({ kind: "redirect", to: "/student" });
  });

  it("refuses parents and canteen/merchant staff", () => {
    for (const role of ["parent", "canteen_staff", "merchant_staff"] as const) {
      expect(decideRoute(role, "/school")).toEqual({ kind: "refuse", reason: "role_not_allowed" });
      expect(decideRoute(role, "/")).toEqual({ kind: "refuse", reason: "role_not_allowed" });
    }
  });

  it("sends signed-in users from / to their home", () => {
    expect(decideRoute("school_admin", "/")).toEqual({ kind: "redirect", to: "/school" });
    expect(decideRoute("platform_admin", "/")).toEqual({ kind: "redirect", to: "/platform" });
  });
});
