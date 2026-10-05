import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test("student portal shows only the student's own summary", async ({ page }) => {
  await login(page, { email: "student.amina@kampaladps.schooldimes.test", password: "pw123456" });
  await page.waitForURL("**/student");
  await expect(page.getByText("Hello, Amina!")).toBeVisible();
  await expect(page.getByTestId("portal-balance")).toContainText("UGX");
  await page.goto("/school");
  await page.waitForURL("**/student");
});
