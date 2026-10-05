import { execSync } from "node:child_process";

import { expect, test } from "@playwright/test";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
// How to run the backend's mock_webhook command (override if not using docker compose).
const MOCK_WEBHOOK = process.env.E2E_MOCK_WEBHOOK_CMD || "docker compose exec -T web python manage.py mock_webhook";

test("contributor page: pay → mock_webhook confirm → balance and parent notification updated", async ({ page, request }) => {
  // the parent's own API session (as the mobile app would have)
  const tokens = await (await request.post(`${API}/api/v1/auth/login`, { data: { email: "parent1@schooldimes.test", password: "pw123456" } })).json();
  const auth = { Authorization: `Bearer ${tokens.access}` };
  const links = await (await request.get(`${API}/api/v1/payments/topup-links/`, { headers: auth })).json();
  const link = links.results.find((l: { active: boolean }) => l.active);
  const walletBefore = await (await request.get(`${API}/api/v1/wallets/${link.wallet}/`, { headers: auth })).json();
  const unreadBefore = (await (await request.get(`${API}/api/v1/notifications/?unread=true`, { headers: auth })).json()).unread_count;

  await page.goto(`/give/${link.token}`);
  await expect(page.getByRole("heading", { name: /Send money to/ })).toBeVisible();
  await page.getByTestId("give-name").fill("Jjajja E2E");
  await page.getByTestId("give-phone").fill("0701000222");
  await page.getByTestId("give-amount").fill("1500");
  await page.waitForTimeout(3100); // the page's minimum fill time (bot deterrent)
  await page.getByTestId("give-submit").click();
  await expect(page.getByTestId("give-status")).toHaveText("Waiting");
  const reference = (await page.locator(".mono").last().textContent())!.trim();

  execSync(`${MOCK_WEBHOOK} ${reference}`, { cwd: "..", stdio: "pipe" });
  await expect(page.getByTestId("give-status")).toHaveText("Paid", { timeout: 15_000 });

  const walletAfter = await (await request.get(`${API}/api/v1/wallets/${link.wallet}/`, { headers: auth })).json();
  expect(Number(walletAfter.balance) - Number(walletBefore.balance)).toBe(1500);
  const unreadAfter = (await (await request.get(`${API}/api/v1/notifications/?unread=true`, { headers: auth })).json()).unread_count;
  expect(unreadAfter).toBeGreaterThan(unreadBefore);
});

test("contributor page: invalid link shows a clear message", async ({ page }) => {
  await page.goto("/give/not-a-real-token");
  await expect(page.getByTestId("link-invalid")).toBeVisible();
});
