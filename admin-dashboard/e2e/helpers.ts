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

const watched = new WeakSet<Page>();
const i18nErrors = new WeakMap<Page, string[]>();

/** Page loaded its data: no error alert, and no missing/misformatted translation. */
export async function expectRendered(page: Page, path: string) {
  if (!watched.has(page)) {
    watched.add(page);
    i18nErrors.set(page, []);
    page.on("console", (m) => {
      if (m.type() === "error" && /MISSING_MESSAGE|FORMATTING_ERROR|INVALID_MESSAGE/.test(m.text())) i18nErrors.get(page)!.push(m.text());
    });
  }
  i18nErrors.get(page)!.length = 0;
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  await expect(page.getByTestId("error-alert"), `error on ${path}`).toHaveCount(0);
  await expect(page.locator("h2").first(), `heading on ${path}`).toBeVisible();
  expect(i18nErrors.get(page), `translation errors on ${path}`).toEqual([]);
}
