import { expect, type Page } from "@playwright/test";

export const SCHOOL_ADMIN = { email: "admin@kampaladps.schooldimes.test", password: "pw123456" };
export const PLATFORM_ADMIN = { email: "platform@schooldimes.test", password: "pw123456" };
export const PARENT = { email: "parent1@schooldimes.test", password: "pw123456" };

export async function login(page: Page, who: { email: string; password: string }) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(who.email);
  await page.getByRole("textbox", { name: "Password" }).fill(who.password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

/** Page loaded its data: no error alert and no spinner left after the network settles. */
export async function expectRendered(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  await expect(page.getByTestId("error-alert"), `error on ${path}`).toHaveCount(0);
  await expect(page.locator("h2").first(), `heading on ${path}`).toBeVisible();
}
