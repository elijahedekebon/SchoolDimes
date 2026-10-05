import { expect, test } from "@playwright/test";

import { expectRendered, login, PLATFORM_ADMIN } from "./helpers";

const PLATFORM_PAGES = ["/platform", "/platform/onboard", "/platform/referrals", "/platform/support?school=1", "/platform/payment-issues", "/platform/audit-log", "/platform/tips"];

test("platform admin: back-office pages render; /school redirects to /platform", async ({ page }) => {
  await login(page, PLATFORM_ADMIN);
  await page.waitForURL("**/platform");
  for (const path of PLATFORM_PAGES) await expectRendered(page, path);
  await page.goto("/school");
  await page.waitForURL("**/platform");
});

test("onboarding wizard creates a school whose admin can sign in", async ({ page, browser }) => {
  const stamp = Date.now();
  await login(page, PLATFORM_ADMIN);
  await page.waitForURL("**/platform");
  await page.goto("/platform/onboard");
  await page.getByTestId("onboard-name").fill(`E2E School ${stamp}`);
  await page.getByTestId("onboard-next").click();
  await page.getByTestId("onboard-next").click();
  await page.getByTestId("onboard-next").click();
  await page.getByTestId("onboard-admin-email").fill(`admin${stamp}@e2e.test`);
  await page.getByTestId("onboard-admin-password").fill("longpassword1");
  await page.getByTestId("onboard-next").click();
  await page.getByTestId("onboard-submit").click();
  await expect(page.getByText(`E2E School ${stamp} is ready`)).toBeVisible();

  const ctx = await browser.newContext();
  const admin = await ctx.newPage();
  await login(admin, { email: `admin${stamp}@e2e.test`, password: "longpassword1" });
  await admin.waitForURL("**/school");
  await expect(admin.getByTestId("school-name")).toHaveText(`E2E School ${stamp}`);
  await ctx.close();
});
