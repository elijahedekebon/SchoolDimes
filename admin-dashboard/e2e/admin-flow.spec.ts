import { expect, test } from "@playwright/test";

import { login, SCHOOL_ADMIN } from "./helpers";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

test("admin flow: register device (token once) → issue card → freeze → refund a dispute", async ({ page, request }) => {
  const stamp = Date.now();
  await login(page, SCHOOL_ADMIN);
  await page.waitForURL("**/school");

  // 1. register a device: the raw token is shown exactly once
  await page.goto("/school/devices");
  await page.getByTestId("register-device").click();
  await page.getByTestId("device-name").fill(`E2E till ${stamp}`);
  await page.getByTestId("confirm-register").click();
  const token = (await page.getByTestId("device-token").textContent())!.trim();
  expect(token.length).toBeGreaterThan(30);
  await page.getByTestId("token-saved").click();
  await expect(page.getByText(`E2E till ${stamp}`)).toBeVisible();
  expect(await page.content()).not.toContain(token); // never shown again

  // 2. add a student and issue a card with an NFC UID
  await page.goto("/school/students");
  await page.getByTestId("new-student").click();
  await page.getByLabel("Name").fill(`E2E Student ${stamp}`);
  await page.getByLabel("Class").fill("P3");
  await page.getByRole("button", { name: "Save" }).click();
  await page.waitForURL(/\/school\/students\/\d+$/);
  await page.getByRole("tab", { name: "Cards" }).click();
  await page.getByTestId("issue-card").click();
  const uid = stamp.toString(16).padStart(14, "0").slice(-14);
  await page.getByTestId("card-uid-input").fill(uid.match(/../g)!.join(":").toUpperCase());
  await page.getByRole("textbox", { name: "PIN", exact: true }).fill("2468");
  await page.getByRole("textbox", { name: "Repeat PIN" }).fill("2468");
  await page.getByTestId("confirm-issue").click();
  await expect(page.getByText(uid)).toBeVisible();

  // 3. freeze it
  await page.getByTestId("freeze-card").click();
  await page.getByTestId("confirm-button").click();
  await expect(page.getByText("frozen", { exact: true })).toBeVisible();

  // 4. a parent disputes a sale; the admin refunds 100 UGX and the balance moves
  const ptok = (await (await request.post(`${API}/api/v1/auth/login`, { data: { email: "parent1@schooldimes.test", password: "pw123456" } })).json()).access;
  const pauth = { Authorization: `Bearer ${ptok}` };
  const dash = await (await request.get(`${API}/api/v1/parent/dashboard/`, { headers: pauth })).json();
  let disputeId: number | null = null;
  let mainWallet = 0;
  for (const s of dash.students) {
    const rows = (await (await request.get(`${API}/api/v1/students/${s.id}/transactions/?direction=debit&entry_type=pos_purchase&page_size=50`, { headers: pauth })).json()).results;
    for (const r of rows) {
      if (!r.dispute_target) continue;
      const res = await request.post(`${API}/api/v1/disputes/`, { headers: pauth, data: { ...r.dispute_target, reason_category: "wrong_amount", description: "e2e" } });
      const body = await res.json();
      if (res.status() === 201 && Number(body.original_amount) - Number(body.refunded_total) >= 100) {
        disputeId = body.id;
        mainWallet = s.main_wallet.id;
        break;
      }
    }
    if (disputeId) break;
  }
  expect(disputeId, "a refundable sale to dispute").not.toBeNull();
  const before = (await (await request.get(`${API}/api/v1/wallets/${mainWallet}/`, { headers: pauth })).json()).balance;

  await page.goto(`/school/disputes?open=${disputeId}`);
  await page.getByTestId("resolve-dispute").click();
  await page.getByTestId("refund-amount").fill("100");
  await page.getByTestId("confirm-button").click();
  await expect(page.getByTestId("confirm-button")).toHaveCount(0); // dialog closed = request succeeded

  // test-only arithmetic on 2-dp strings (the app itself never uses floats for money)
  await expect
    .poll(async () => {
      const after = (await (await request.get(`${API}/api/v1/wallets/${mainWallet}/`, { headers: pauth })).json()).balance;
      return Math.round((Number(after) - Number(before)) * 100);
    })
    .toBe(10000);
});
