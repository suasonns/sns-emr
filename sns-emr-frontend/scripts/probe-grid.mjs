import { chromium } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const PATIENT_ID = "53fe69e1-fcd5-4b49-8203-9b890b18b7d6";

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);
  await page.evaluate((patientId) => {
    window.sessionStorage.setItem("sns-hospice-solutions-active-patient", patientId);
  }, PATIENT_ID);
  await page.goto(`${BASE_URL}/nursing-assessment`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.locator(".rnica-rail__label", { hasText: "Body Systems" }).first().click();
  await page.waitForTimeout(600);
  await page.locator(".rnica-bodysystems__trigger", { hasText: "Cardiovascular" }).first().click();
  await page.waitForTimeout(600);
  await page.getByText("New or Worsening Cardiovascular Findings", { exact: false }).first().click();
  await page.waitForTimeout(1000);

  const measurement = await page.evaluate(() => {
    const circCard = document.querySelector('[data-section="cardiovascular"] [data-card-title="Circulation & Perfusion"]');
    const symCard = document.querySelector('[data-section="cardiovascular"] [data-card-title="Cardiovascular Symptoms"]');
    const overviewCard = document.querySelector('[data-section="cardiovascular"] [data-card-title="Cardiovascular Overview"]');
    function describe(el) {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return {
        width: Math.round(r.width),
        display: cs.display,
        gridColumn: cs.gridColumn,
        gridTemplateColumns: cs.gridTemplateColumns,
        columnGap: cs.columnGap,
        rowGap: cs.rowGap,
        containerType: cs.containerType,
        containerName: cs.containerName,
      };
    }
    // find the actual fields grid wrapper inside the card
    const allDivs = circCard ? Array.from(circCard.querySelectorAll("div")) : [];
    const candidateGrids = allDivs
      .filter((d) => getComputedStyle(d).display === "grid")
      .map((d) => ({ cls: d.className, ...describe(d) }));

    const chain = [];
    let el = circCard;
    while (el && el.tagName !== "BODY") {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      chain.push({
        tag: el.tagName,
        cls: (el.className || "").toString().slice(0, 70),
        width: Math.round(r.width),
        display: cs.display,
        containerType: cs.containerType,
        containerName: cs.containerName,
      });
      el = el.parentElement;
    }

    return {
      viewportWidth: window.innerWidth,
      circCardDescribe: describe(circCard),
      symCardDescribe: describe(symCard),
      overviewCardDescribe: describe(overviewCard),
      candidateGrids,
      chain,
    };
  });
  console.log(JSON.stringify(measurement, null, 2));
  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
