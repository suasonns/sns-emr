import { chromium } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const LOGIN_EMAIL = "rsuason@loveandfaithhospice.com";
const LOGIN_PASSWORD = "LoveFaithHospice2026!";
const ASSESSMENT_ID = "84234eb9-bfb9-4222-8287-4f4e8475c593";

const BASELINE = {
  cardiovascularOverview: "Unable to Assess", cardiovascularUnableToAssessReason: "Patient unresponsive",
  cardiovascularUnableToAssessOther: "", cardiovascularFindingsConfirmedThisVisit: false,
  pulseRhythm: "", pulseRate: "", pulseStrength: "", pulseSites: [], pulseQuality: "",
  skinColor: "", skinColorOther: "", heartSounds: "", heartSoundsOther: "",
  coolExtremities: false, varicoseVeins: false, stasisUlcer: false,
  jvd: "", peripheralCirculation: "", peripheralCirculationOther: "",
  edema: { present: "No", location: [], severity: "", pitting: "" },
  chestPain: { present: "", type: "", frequency: "" },
  bpStatus: "", bpSymptoms: [], orthostaticFinding: "", dizziness: "", fatigue: "", syncope: "",
  cardiacDyspnea: false, heartFailurePresent: false, heartFailureType: [],
  pacemaker: false, internalDefibrillator: false, centralVenousLine: false,
  clinicalStatusChange: "Initial Assessment", notes: "",
};

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(LOGIN_EMAIL);
  await page.getByLabel(/^password/i).fill(LOGIN_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForTimeout(2000);

  const status = await page.evaluate(async ({ assessmentId, cardiovascular }) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const getRes = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    if (!getRes.ok) return { step: "GET", status: getRes.status, body: await getRes.text() };
    const full = await getRes.json();
    const newFormData = { ...full.formData, cardiovascular };
    const putRes = await fetch(`/visits/rnica/${assessmentId}`, {
      method: "PUT", credentials: "include",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ formData: newFormData, fieldProvenance: full.fieldProvenance || [] }),
    });
    return { step: "PUT", status: putRes.status, body: putRes.ok ? "OK" : await putRes.text() };
  }, { assessmentId: ASSESSMENT_ID, cardiovascular: BASELINE });

  console.log("Save result:", JSON.stringify(status));

  const verify = await page.evaluate(async (assessmentId) => {
    const token = localStorage.getItem("sns-hospice-solutions-access-token");
    const res = await fetch(`/visits/rnica/${assessmentId}`, { credentials: "include", headers: { Authorization: `Bearer ${token}` } });
    const full = await res.json();
    return full.formData.cardiovascular;
  }, ASSESSMENT_ID);

  console.log("Verified cardiovascular after restore:\n", JSON.stringify(verify, null, 2));
  await browser.close();
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
