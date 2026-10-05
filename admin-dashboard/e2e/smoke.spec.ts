import { expect, test } from "@playwright/test";

import { expectRendered, login, PARENT, SCHOOL_ADMIN } from "./helpers";

const SCHOOL_PAGES = ["/school", "/school/sales", "/school/reconciliation", "/school/shortfalls", "/school/analytics", "/school/students", "/school/students/1", "/school/guardians", "/school/cards"];

test("parents are refused at login", async ({ page }) => {
  await login(page, PARENT);
  await expect(page.getByTestId("login-error")).toContainText("mobile app");
});

test("school admin: main pages render against the seeded backend", async ({ page }) => {
  await login(page, SCHOOL_ADMIN);
  await page.waitForURL("**/school");
  await expect(page.getByTestId("school-name")).toHaveText("Kampala Demo Primary School");
  for (const path of SCHOOL_PAGES) await expectRendered(page, path);
  // school_admin can't reach the platform back-office
  await page.goto("/platform");
  await page.waitForURL("**/school");
});
