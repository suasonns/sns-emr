// HOPE-E2E-RNICA-001: minimal, data-independent smoke coverage for the
// tenant portal and the RNICA route. Deliberately does NOT depend on any
// specific seeded patient existing -- different local dev databases have
// different patients -- so this only proves: login worked, the tenant
// portal shell and the RNICA route both render through the real app
// (routing, auth guard, and the new React.lazy() route-splitting all
// wired correctly end-to-end), and neither screen leaks an internal
// identifier as visible text.
//
// Patient-specific RNICA workflow specs (Visit Header persistence,
// draft/lock behavior) belong in a separate spec file once a known,
// stable seeded patient fixture exists for this environment -- adding
// one is out of scope for this infrastructure change.
import { test, expect } from "@playwright/test";
import { assertNoUuidLeak } from "./support/noUuidLeak";

test.describe("authenticated tenant routes", () => {
  test("tenant portal loads for the signed-in RN after the real login flow", async ({ page }) => {
    await page.goto("/portal");
    await expect(page).toHaveURL(/\/portal$/);

    const bodyText = await page.locator("body").innerText();
    assertNoUuidLeak(bodyText, "/portal");
  });

  test("RNICA route renders through the real app without a selected patient", async ({ page }) => {
    await page.goto("/rnica");
    await expect(page).toHaveURL(/\/rnica$/);

    // No active patient is selected by navigating here directly, so
    // RNICA.jsx renders its explicit "No patient selected" state (see
    // src/components/RNICA.jsx) rather than crashing or showing a blank
    // screen -- this is itself the regression check that the route and
    // its React.lazy() chunk load correctly.
    await expect(page.getByText("No patient selected")).toBeVisible();

    const bodyText = await page.locator("body").innerText();
    assertNoUuidLeak(bodyText, "/rnica");
  });
});
