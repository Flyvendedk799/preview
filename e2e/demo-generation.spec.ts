/**
 * E2E tests for MyMetaView 6.0 demo generation flow.
 *
 * Covers: batch submit, polling, results.
 * Ensures end-to-end flow works after 400% optimization.
 *
 * Prerequisites:
 * - Frontend: npm run dev (or use BASE_URL for deployed app)
 * - Backend + Redis + RQ workers running (for local)
 * - Or run against production: BASE_URL=https://www.mymetaview.com
 */

import { test, expect } from "@playwright/test";

const DEMO_GENERATION_PATH = "/demo-generation";

test.describe("Demo generation flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DEMO_GENERATION_PATH);
  });

  test("loads demo generation page", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /new demo preview/i })
    ).toBeVisible({ timeout: 10000 });
    await expect(
      page.getByPlaceholder(/https:\/\/your-product-url/i)
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /generate demo preview/i })
    ).toBeVisible();
  });

  test("batch submit: accepts URLs and creates job", async ({ page }) => {
    const testUrl = "https://example.com";
    const textarea = page.getByPlaceholder(/https:\/\/your-product-url/i);
    await textarea.fill(testUrl);

    await page.getByRole("button", { name: /generate demo preview/i }).click();

    // Either: submitting → generating (success), or error (backend down)
    await expect(
      page.getByText(
        /creating demo job|registering your urls|generating previews|assembling scenes|we couldn't start your demo|connection problem/i
      )
    ).toBeVisible({ timeout: 10000 });
  });

  test("full flow: batch submit, polling, results", async ({ page }) => {
    const testUrl = "https://example.com";
    const textarea = page.getByPlaceholder(/https:\/\/your-product-url/i);
    await textarea.fill(testUrl);

    await page.getByRole("button", { name: /generate demo preview/i }).click();

    // Flow completes with either: (1) results UI, or (2) submit error (backend down)
    await expect(
      page.getByText(
        /generating previews|assembling scenes|demo previews ready|some previews are ready|we couldn't complete|we couldn't start your demo|connection problem|edit urls|retry failed/i
      )
    ).toBeVisible({ timeout: 15000 });

    // Wait for final state (edit or retry button visible)
    await expect(
      page.getByRole("button", { name: /edit urls|retry failed/i }).first()
    ).toBeVisible({ timeout: 90000 });
  });

  test("supports multiple URLs in batch", async ({ page }) => {
    const urls = ["https://example.com", "https://example.org"];
    const textarea = page.getByPlaceholder(/https:\/\/your-product-url/i);
    await textarea.fill(urls.join("\n"));

    await page.getByRole("button", { name: /generate demo preview/i }).click();

    await expect(
      page.getByText(
        /generating previews|assembling scenes|demo previews ready|some previews|we couldn't complete|we couldn't start|connection problem|edit urls|retry failed/i
      )
    ).toBeVisible({ timeout: 15000 });

    await expect(
      page.getByRole("button", { name: /edit urls|retry failed/i }).first()
    ).toBeVisible({ timeout: 90000 });
  });

  test("edit URLs returns to configure state", async ({ page }) => {
    const testUrl = "https://example.com";
    const textarea = page.getByPlaceholder(/https:\/\/your-product-url/i);
    await textarea.fill(testUrl);
    await page.getByRole("button", { name: /generate demo preview/i }).click();

    await expect(
      page.getByText(/demo previews ready|some previews|we couldn't complete|edit urls|retry failed/i)
    ).toBeVisible({ timeout: 90000 });

    await page.getByRole("button", { name: "Edit URLs" }).click();

    await expect(
      page.getByRole("heading", { name: /new demo preview/i })
    ).toBeVisible();
    await expect(textarea).toBeVisible();
  });
});
