// PRODUCT OWNER FINAL DIRECTIVE "Structured Anatomical Location Library"
// (Phase A) Section 14: Playwright verification is mandatory. This spec
// exercises a focused subset of the directive's acceptance tests (A1,
// A7, A8, A12) against the real app through the Skin Impairment
// Workspace's Anatomical Site selector.
//
// Reuses the same stable seeded patient fixture used by other RNICA
// Playwright verification tooling (chart ID supplied via
// E2E_TEST_PATIENT_ID, not hardcoded -- see note below).
//
// Radix's <Select> here (see src/components/ui/select) does not wire an
// aria-label/aria-labelledby back to its own `label` text (its
// accessible name is just the placeholder, "— Select —", until a value
// is chosen) -- so a field is located by its visible `<label>` text and
// then its sibling combobox within the same field group, not by
// `getByRole("combobox", { name })`.
//
// RNICA RECONCILIATION UPDATE (2026-10-23): the Skin Impairment
// Workspace's wound-selection model changed under "PRODUCT OWNER
// APPROVAL WITH TRACE CORRECTIONS (2026-10-20) 'FINAL Controlled
// Values'" -- the former left-panel inventory list (per-row "Open" /
// "Remove" buttons, an "ACTIVE (N)" badge) and the separate
// "+ Pressure Injury" / "+ Skin Condition" entry points were removed in
// favor of ONE "+ Add Wound" action (every new record starts pending
// classification, answering "Condition Type" first) plus a single
// "Select Wound" dropdown and one always-visible detail editor.
// Separately, under "PRODUCT OWNER REVIEW (2026-12-02) 'Remove Body
// Region From The Clinician Workflow'", the former cascading Body
// Region -> Anatomical Site selector was collapsed into ONE flat
// "Anatomical Site" combobox (the chosen site already implies its body
// region, which is still derived/stored internally, just never
// RN-selected). This spec was failing its own `beforeEach`
// (`getByText(/ACTIVE \(0\)/)` never renders -- that badge no longer
// exists) and then its first real step (no "Body Region" field is
// rendered to click anymore) because it still targeted the superseded
// UI, not because of
// stale/dirty shared chart data. Helpers and test bodies below are
// updated to match the current,
// approved single-editor model; the underlying clinical acceptance
// assertions (A1, A7, A8, A12, etc.) are unchanged.
import { test, expect, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));

// Never hardcode a chart/patient identifier in a committed test file --
// set E2E_TEST_PATIENT_ID in the local environment (e.g. alongside
// backend/.env) to the seeded fixture patient's chart ID before running
// this spec.
const PATIENT_ID = process.env.E2E_TEST_PATIENT_ID;
if (!PATIENT_ID) {
  throw new Error(
    "[e2e] E2E_TEST_PATIENT_ID is not set. structured-wound-location.spec.ts " +
      "requires a known seeded fixture patient chart ID; set it in the " +
      "environment rather than hardcoding a patient identifier in source.",
  );
}

// `skin_impairments` is a lifecycle identity table, separate from the
// clinical detail in `RnicaAssessment.form_data`, that the backend uses
// to automatically carry forward any non-"Resolved" wound into every
// subsequent assessment load for a patient -- by design (see
// backend/app/models/skin_impairment.py), so a real unresolved wound
// can never silently disappear between visits. The Skin Impairment
// Workspace's "Remove" button only edits the current assessment's local
// draft `wounds` array -- it has no path to mark that identity row
// "Resolved" -- so once ANY test (e.g. A12, which intentionally leaves
// an incomplete record persisted to assert the "Require Completion"
// badge) lets a wound autosave, that record keeps getting carried
// forward and re-rendered on every subsequent load no matter how many
// times `removeAllWoundRecords` clicks "Remove" in the UI. Resolving
// those stale identity rows directly (never deleting -- resolved rows
// must stay searchable/auditable) before each test is the only way to
// give this shared e2e fixture patient a truly convergent, deterministic
// starting state.
function resetSkinImpairmentFixture() {
  const scriptPath = resolve(HERE, "../../backend/scripts/reset_e2e_skin_impairments.py");
  execFileSync("python", [scriptPath, PATIENT_ID as string], { stdio: "inherit" });
}

function fieldCombobox(page: Page, labelText: string) {
  // The workspace's inventory can contain pre-existing wound records
  // left open from earlier manual verification sessions (each with its
  // own, already-expanded field group). `.last()` targets the field
  // belonging to the record this spec just created (always the
  // most-recently-appended card), never an unrelated pre-existing
  // record's identically-labeled field.
  return page.locator("label", { hasText: labelText }).locator("xpath=..").getByRole("combobox").last();
}

// FormSegmented (Side / Surface / Device-Related, etc.) is a Radix
// ToggleGroup rendered with `aria-label={label}` directly on its root --
// targeting that attribute is more robust than text-walking from the
// <label> element, since the visible <label> and the ToggleGroup root
// are siblings, not parent/child.
function clickSegmentedOption(page: Page, labelText: string, optionText: string) {
  return page.locator(`[aria-label="${labelText}"]`).last().getByText(optionText, { exact: true }).click();
}

function fieldInput(page: Page, labelText: string) {
  return page.locator("label", { hasText: labelText }).locator("xpath=..").locator("input").last();
}

// `SelectWoundDropdown`'s compact header renders a <strong> caption
// ("Select Wound"), not a <label> -- it needs its own lookup, separate
// from `fieldCombobox` which only matches real <label> field groups.
function selectWoundCombobox(page: Page) {
  return page.locator("strong", { hasText: "Select Wound" }).locator("xpath=..").getByRole("combobox");
}

// A brand-new record (`+ Add Wound`) starts pending classification --
// its ONLY visible field is "Condition Type" (see
// `isPendingClassification` in WoundRecordCard) -- so adding a wound and
// choosing its type is always this same two-step gesture, replacing the
// former separate "+ Pressure Injury" / "+ Skin Condition" buttons.
async function addWound(page: Page, conditionTypeLabel: string) {
  await page.getByRole("button", { name: "+ Add Wound" }).click();
  await fieldCombobox(page, "Condition Type").click();
  await page.getByRole("option", { name: conditionTypeLabel, exact: true }).click();
}

// The record-level Remove button always renders in the detail card's
// own header (first in DOM order, alongside "View Timeline" once
// classified, or alone while pending classification). An extension's
// own "Remove" button (identical accessible name) only renders later,
// inside its own "Extends To" field row -- `.first()` reliably targets
// the record's header button, never an extension's.
function recordRemoveButton(page: Page) {
  return page.getByRole("button", { name: "Remove", exact: true }).first();
}

async function removeAllWoundRecords(page: Page) {
  let removedAny = false;
  // Bounded retry loop, not a single pass: clicking "Remove" swaps
  // `selectedWoundId` to the next remaining record and re-renders its
  // card, which can still be mid-flight the instant this helper re-
  // queries the DOM. A fixed short sleep plus a single `.count()` check
  // can therefore observe a stale "0" while a second (or later) leftover
  // record from a prior run/test is still present -- so this keeps
  // removing, re-checking after every click, until a real empty state is
  // confirmed, rather than trusting the first zero-count reading.
  for (let i = 0; i < 25; i++) {
    const removeButton = recordRemoveButton(page);
    if (!(await removeButton.count())) break;
    removedAny = true;
    await removeButton.click();
    await page.waitForTimeout(400);
  }
  const emptyState = page.getByText(/No skin impairments documented yet/);
  if (!(await emptyState.isVisible().catch(() => false))) {
    // Self-healing fallback: a prior test's wound can land its backend
    // save (the fixed 30s autosave interval, or an unmount/navigation
    // flush) AFTER this beforeEach's upfront resetSkinImpairmentFixture()
    // call already ran but BEFORE this page's own fetch -- in which case
    // no amount of clicking "Remove" here will ever converge, because
    // the record keeps getting re-synced back in from the still-
    // unresolved `skin_impairments` identity row (see
    // resetSkinImpairmentFixture's comment). Re-run the same reset and
    // reload once before trusting a final failure.
    resetSkinImpairmentFixture();
    await page.reload();
    await expect(page.getByText("Skin Impairment Workspace")).toBeVisible();
  }
  await expect(emptyState).toBeVisible({ timeout: 10000 });
  // Removal -- like every other edit to this workspace's wound inventory
  // -- is only an optimistic local-state change until the fixed 30s
  // background autosave timer actually commits it to the backend (see
  // waitForAutosaveTick below). Without waiting here, a record "removed"
  // by this call still exists server-side: the very next test's fresh
  // page.goto() refetches it from the backend and finds it again,
  // non-deterministically reintroducing a leftover record from a prior
  // test/run. Only pay this cost when something was actually removed.
  if (removedAny) {
    await waitForAutosaveTick(page);
  }
}

// The dedicated Skin Impairment Workspace (/skin-impairments) has no
// manual "Save" affordance of its own -- the only persistence path is
// the whole-RNICA-assessment background autosave timer, which runs on a
// fixed 30s `window.setInterval` (see useAssessmentAutosave.ts), not a
// per-edit debounce. A reload performed before that timer has ticked at
// least once loses every unsaved edit (the record reverts to
// ACTIVE (0)). Tests that must verify true backend persistence across a
// reload wait past one full interval before reloading, and raise their
// own test timeout accordingly since the default 30s Playwright test
// timeout cannot fit a wait this long.
const AUTOSAVE_INTERVAL_MS = 30000;
async function waitForAutosaveTick(page: Page) {
  await page.waitForTimeout(AUTOSAVE_INTERVAL_MS + 2000);
}

// After "Back to RNICA"/"Save & Close", the workspace launch-context
// snapshot is only captured by the real "Add / Manage Skin Impairments"
// button (see captureSkinImpairmentLaunchContext in RNICA.jsx) -- a test
// that jumps straight to /skin-impairments via page.goto() never wrote
// that snapshot, so "Back to RNICA" falls back to the bare "/rnica"
// default section (HOPE Administrative Review), not Body Systems. The
// Skin Impairment action bar/button only renders inside the Body
// Systems > Skin / Wounds subsection, so it must be opened explicitly
// before asserting on that button's text.
async function openBodySystemsSkinSection(page: Page) {
  await page.getByRole("button", { name: /Body Systems/i }).click();
  // Once a wound record exists, "Skin / Wounds" also appears as a findings
  // group label inside the section body, not just the subsection trigger
  // -- .first() avoids a strict-mode multi-match violation either way.
  await expect(page.getByText("Skin / Wounds").first()).toBeVisible();
}

test.describe("Structured Anatomical Location Library (Phase A)", () => {
  // All tests in this file share one seeded patient fixture and each
  // beforeEach wipes/rebuilds that same patient's wound inventory --
  // running them concurrently (Playwright's default fullyParallel
  // behavior) lets one test's cleanup/edits race another's, which is
  // the actual cause of failures seen under multi-worker runs (not a
  // real app regression). Force this suite onto a single worker, in
  // declaration order, so each test sees a clean, uncontended fixture.
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    // Any test may discover a leftover persisted record from a prior
    // test/run and have to pay the one-time ~32s autosave-tick cost in
    // removeAllInventoryRecords to actually flush its deletion -- and
    // several tests below ALSO wait for their own autosave tick within
    // the test body. Set a timeout here (not per-test) with headroom for
    // both ticks plus normal step time; a later test.setTimeout call in
    // the test body would simply overwrite -- not add to -- this value,
    // so this is the single source of truth for this suite's timeout.
    test.setTimeout(150000);
    // Clear any backend-carried-forward unresolved skin impairment
    // before the page even loads -- see resetSkinImpairmentFixture above.
    // Doing this first (not after removeAllWoundRecords) means the
    // very first render of the workspace already has nothing to remove,
    // instead of racing a UI "Remove" loop against data that keeps
    // reappearing.
    resetSkinImpairmentFixture();
    // Visiting /rnica with ?patientId= sets the active patient (read by
    // SkinImpairmentWorkspacePage's getActivePatientId()) before we jump
    // to the dedicated workspace route.
    //
    // The sessionStorage write happens inside RNICA's own patientId-
    // resolution effect (runs after mount, not synchronously during
    // page.goto()). Firing the second goto() immediately risks a real
    // race: the first page's React effect hasn't committed the write
    // yet, so /skin-impairments' own RNICA instance finds nothing in
    // sessionStorage/URL and falls back to a patient-less state. Poll
    // sessionStorage directly so this is a deterministic wait, not a
    // fixed guess.
    await page.goto(`/rnica?patientId=${PATIENT_ID}`);
    await expect
      .poll(() => page.evaluate(() => sessionStorage.getItem("sns-hospice-solutions-active-patient")))
      .toBe(PATIENT_ID);
    await page.goto("/skin-impairments");
    await expect(page.getByText("Skin Impairment Workspace")).toBeVisible();

    // This shared seeded patient accumulates real, backend-persisted wound
    // records from prior manual/automated verification runs (the wound
    // inventory autosaves without an explicit Save click). Each acceptance
    // test needs a truly empty inventory so a freshly added wound record
    // is unambiguously the one under test, so remove every pre-existing
    // record first.
    await removeAllWoundRecords(page);
    await expect(page.getByText(/No skin impairments documented yet/)).toBeVisible();
  });

  test("A1: Pressure Injury site list includes nontraditional sites (e.g. temporal region)", async ({ page }) => {
    await addWound(page, "Pressure Injury");

    const siteCombo = fieldCombobox(page, "Anatomical Site");
    await siteCombo.click();
    await expect(page.getByRole("option", { name: /Temporal Region/i })).toBeVisible();
    await page.getByRole("option", { name: /Temporal Region/i }).first().click();

    await expect(page.getByText(/Location:\s*Temporal region/i)).toBeVisible();
  });

  test("A7: Coccyx is forced midline with no Side or Surface selector and renders as plain 'Coccyx'", async ({ page }) => {
    await addWound(page, "Pressure Injury");

    await fieldCombobox(page, "Anatomical Site").click();
    await page.getByRole("option", { name: "Coccyx", exact: true }).click();

    await expect(page.locator("label", { hasText: "Side" })).toHaveCount(0);
    await expect(page.getByText(/Location:\s*Coccyx\s*$/)).toBeVisible();
  });

  test("A8: Diabetic Foot Ulcer's Anatomical Site list excludes Coccyx", async ({ page }) => {
    await addWound(page, "Diabetic Foot Ulcer");

    await fieldCombobox(page, "Anatomical Site").click();
    await expect(page.getByRole("option", { name: "Coccyx", exact: true })).toHaveCount(0);
    await expect(page.getByRole("option", { name: /Toe/i }).first()).toBeVisible();
  });

  test("A12: Pressure Injury cannot be saved without a Stage/Category", async ({ page }) => {
    // Timeout headroom for this suite is set once in beforeEach, with
    // room for both its cleanup tick and this test's own tick below --
    // do not call test.setTimeout here too (it overwrites, not adds).
    await addWound(page, "Pressure Injury");
    await fieldCombobox(page, "Anatomical Site").click();
    await page.getByRole("option", { name: "Sacrum", exact: true }).click();

    // No Stage/Category selected -- the record must remain in a
    // not-yet-complete state (the workspace status badge must not show
    // "Complete").
    await expect(page.getByText("Complete", { exact: true })).toHaveCount(0);

    // Stronger signal (Review Correction Section 3 -- do not label a
    // weak check as the full acceptance test): the RNICA main page's
    // Skin Impairment action bar derives its label directly from
    // `isWoundRecordMissingRequiredDetails`/`computeSkinImpairmentWorkspaceStatus`,
    // so an incomplete Pressure Injury (no Stage/Category) must make that
    // button read "N Record(s) Require Completion" once we return there.
    // Wait for the background autosave tick first -- without it, the
    // just-created record was never persisted and "Back to RNICA" shows
    // zero records instead of an incomplete one.
    await waitForAutosaveTick(page);
    await page.getByRole("button", { name: "Back to RNICA" }).click();
    await openBodySystemsSkinSection(page);
    await expect(page.getByRole("button", { name: /Record.*Require Completion/i })).toBeVisible();
  });

  // ====================================================================
  // PRODUCT OWNER REVIEW AND CONTINUATION DIRECTIVE Section 2 --
  // mandatory atomic multi-field regression test. This is the exact
  // scenario that exposed the stale-closure bug: Anatomical Site, Side,
  // and Surface are all set by the SAME gesture-chain in one
  // record, then the page is reloaded so only backend-persisted data is
  // read back. The test must fail if only the last field survives.
  // ====================================================================
  test("Atomic update regression: Anatomical Site + Side + Surface all persist after reload", async ({ page }) => {
    // See timeout note on A12 above -- set once in beforeEach.
    await addWound(page, "Pressure Injury");

    await fieldCombobox(page, "Anatomical Site").click();
    await page.getByRole("option", { name: "Upper Arm", exact: true }).click();
    await clickSegmentedOption(page, "Side", "Left");
    await clickSegmentedOption(page, "Surface/Orientation", "Lateral");
    await fieldCombobox(page, "Stage / Category").click();
    await page.getByRole("option", { name: "Stage 2", exact: true }).click();

    await expect(page.getByText(/Location:\s*Left lateral upper arm/i)).toBeVisible();

    // Wait past a full background autosave tick (fixed 30s interval, not
    // a per-edit debounce -- see waitForAutosaveTick) before reloading,
    // then confirm only backend-persisted data survives. The single
    // always-visible editor auto-selects the first active wound on load
    // (see the workspace's selectedWoundId effect) -- there is no
    // separate "Open" affordance to re-expand a collapsed record.
    await waitForAutosaveTick(page);
    await page.reload();
    await expect(page.getByText("Skin Impairment Workspace")).toBeVisible();

    await expect(fieldCombobox(page, "Anatomical Site")).toHaveText(/Upper Arm/i);
    await expect(page.getByText(/Location:\s*Left lateral upper arm/i)).toBeVisible();
    await expect(fieldCombobox(page, "Stage / Category")).toHaveText(/Stage 2/i);
  });

  test("A2: Left lateral upper arm saves and reloads without substitution", async ({ page }) => {
    await addWound(page, "Pressure Injury");
    await fieldCombobox(page, "Anatomical Site").click();
    await page.getByRole("option", { name: "Upper Arm", exact: true }).click();
    await clickSegmentedOption(page, "Side", "Left");
    await clickSegmentedOption(page, "Surface/Orientation", "Lateral");
    await fieldCombobox(page, "Stage / Category").click();
    await page.getByRole("option", { name: "Stage 2", exact: true }).click();

    await expect(page.getByText(/Location:\s*Left lateral upper arm\s*$/i)).toBeVisible();
    await expect(page.getByText(/Shoulder|Acromion|Elbow|Forearm/i)).toHaveCount(0);
  });

  test("A9: Venous Ulcer location list excludes Head/Face, upper extremity, Sacrum and Coccyx", async ({ page }) => {
    await addWound(page, "Venous Ulcer");

    await fieldCombobox(page, "Anatomical Site").click();
    await expect(page.getByRole("option", { name: "Coccyx", exact: true })).toHaveCount(0);
    await expect(page.getByRole("option", { name: "Sacrum", exact: true })).toHaveCount(0);
    await expect(page.getByRole("option", { name: "Upper Arm", exact: true })).toHaveCount(0);
    await expect(page.getByRole("option", { name: /Calf/i }).first()).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(fieldCombobox(page, "Stage / Category")).toHaveCount(0);
  });

  test("A10: Arterial Ulcer location list excludes Coccyx and Sacrum", async ({ page }) => {
    await addWound(page, "Arterial Ulcer");

    await fieldCombobox(page, "Anatomical Site").click();
    await expect(page.getByRole("option", { name: "Coccyx", exact: true })).toHaveCount(0);
    await expect(page.getByRole("option", { name: "Sacrum", exact: true })).toHaveCount(0);
    await expect(page.getByRole("option", { name: /Heel/i }).first()).toBeVisible();
  });

  test("A11: Skin Tear has a broad location library and no Pressure Injury Stage/Category field", async ({ page }) => {
    await addWound(page, "Skin Tear");

    await fieldCombobox(page, "Anatomical Site").click();
    await expect(page.getByRole("option", { name: "Upper Arm", exact: true })).toBeVisible();
    await expect(page.getByRole("option", { name: "Forearm", exact: true })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(fieldCombobox(page, "Stage / Category")).toHaveCount(0);
  });

  test("A17: Unstageable does not require Depth and permits Slough/Eschar findings", async ({ page }) => {
    // See timeout note on A12 above -- set once in beforeEach.
    await addWound(page, "Pressure Injury");
    await fieldCombobox(page, "Anatomical Site").click();
    await page.getByRole("option", { name: "Sacrum", exact: true }).click();
    await fieldCombobox(page, "Stage / Category").click();
    await page.getByRole("option", { name: "Unstageable", exact: true }).click();

    // "Advanced Wound Findings" (Slough/Eschar/Undermining/Tunneling) is
    // a collapsed-by-default panel (see the `showAdvanced` toggle in
    // WoundRecordCard) -- it must be expanded before its fields are
    // visible.
    await page.getByText("Advanced Wound Findings").click();
    await expect(page.getByText("Slough Present?")).toBeVisible();
    await expect(page.getByText("Eschar Present?")).toBeVisible();

    // Provide Length/Width (Unstageable requires a surface measurement
    // or a documented reason) but deliberately leave Depth blank --
    // Depth must not block completion for this stage.
    await fieldInput(page, "Length (cm)").fill("2");
    await fieldInput(page, "Width (cm)").fill("2");
    await clickSegmentedOption(page, "Drainage Amount", "Moderate").catch(async () => {
      await clickSegmentedOption(page, "Drainage Amount", "None");
    });
    // Required for completion alongside Condition Type (see
    // isWoundRecordMissingRequiredDetails in RNICA.jsx, "FINAL Controlled
    // Values" Section 23) -- without it the record remains "missing
    // required details" regardless of every other field below being
    // filled in, which is exactly what this test needs to NOT be true.
    await clickSegmentedOption(page, "Present at Admission", "Yes");
    // Wait for the background autosave tick before leaving -- without it
    // this record was never persisted, so "Back to RNICA" would see
    // whatever was last actually saved (not necessarily this complete
    // edit) instead of the fully-filled-in record under test.
    await waitForAutosaveTick(page);
    await page.getByRole("button", { name: "Back to RNICA" }).click();
    await openBodySystemsSkinSection(page);
    await expect(page.getByRole("button", { name: /Record.*Require Completion/i })).toHaveCount(0);
  });

  test("A18: Deep Tissue Pressure Injury hides the Advanced Wound Findings panel", async ({ page }) => {
    await addWound(page, "Pressure Injury");
    await fieldCombobox(page, "Anatomical Site").click();
    await page.getByRole("option", { name: "Sacrum", exact: true }).click();
    await fieldCombobox(page, "Stage / Category").click();
    await page.getByRole("option", { name: "Deep Tissue Pressure Injury", exact: true }).click();

    await expect(page.getByText("Advanced Wound Findings")).toHaveCount(0);
    await expect(page.getByText("Skin Open or Intact")).toHaveCount(0);
  });

  test("A20: Five distinct Pressure Injury records keep separate locations and stages after independent edits", async ({ page }) => {
    const sites: Array<{ region: string; site: string; side?: string; surface?: string; label: RegExp }> = [
      { region: "Head and Face", site: "Temporal Region", side: "Left", label: /Left temporal region/i },
      { region: "Upper Extremity", site: "Upper Arm", side: "Left", surface: "Lateral", label: /Left lateral upper arm/i },
      { region: "Lower Extremity", site: "Thigh", side: "Left", surface: "Lateral", label: /Left lateral thigh/i },
      { region: "Lower Extremity", site: "Calf", side: "Left", surface: "Posterior", label: /Left posterior calf/i },
      { region: "Foot and Ankle", site: "Lateral Foot", side: "Left", label: /Left lateral foot/i },
    ];

    for (const s of sites) {
      await addWound(page, "Pressure Injury");
      await fieldCombobox(page, "Anatomical Site").click();
      await page.getByRole("option", { name: s.site, exact: true }).click();
      if (s.side) await clickSegmentedOption(page, "Side", s.side);
      if (s.surface) await clickSegmentedOption(page, "Surface/Orientation", s.surface);
      await fieldCombobox(page, "Stage / Category").click();
      await page.getByRole("option", { name: "Stage 2", exact: true }).click();
      await expect(page.getByText(s.label).first()).toBeVisible();
    }

    // All 5 records must coexist as distinct, independently selectable
    // wounds -- confirmed by the "Select Wound" dropdown listing exactly
    // 5 options, never by a selected-record's own caption (which, by
    // design, can only ever show the one currently open).
    await selectWoundCombobox(page).click();
    await expect(page.getByRole("option")).toHaveCount(5);
    await page.keyboard.press("Escape");
    // Every one of the 5 distinct labels must still be present
    // simultaneously in the inventory -- none overwrote another.
    for (const s of sites) {
      await selectWoundCombobox(page).click();
      await expect(page.getByRole("option", { name: s.label })).toBeVisible();
      await page.keyboard.press("Escape");
    }
  });

  // ====================================================================
  // PRODUCT OWNER REVIEW AND CONTINUATION DIRECTIVE Section 5 --
  // Extension / Contiguous Location.
  // ====================================================================
  test("Extension/Contiguous Location: adding and removing an extension never disturbs the primary location", async ({ page }) => {
    // See timeout note on A12 above -- set once in beforeEach.
    await addWound(page, "Pressure Injury");
    await fieldCombobox(page, "Anatomical Site").click();
    await page.getByRole("option", { name: "Calf", exact: true }).click();
    await clickSegmentedOption(page, "Side", "Left");
    await clickSegmentedOption(page, "Surface/Orientation", "Lateral");
    await fieldCombobox(page, "Stage / Category").click();
    await page.getByRole("option", { name: "Stage 2", exact: true }).click();
    await expect(page.getByText(/Location:\s*Left lateral calf/i)).toBeVisible();

    // The extension editor lives behind the "Clarification / Extensions"
    // disclosure toggle -- it is not rendered inline until expanded.
    await page.getByRole("button", { name: "Clarification / Extensions" }).click();
    await page.getByRole("button", { name: "+ Add Extension / Contiguous Location" }).click();
    await page.getByRole("button", { name: "+ Add Extension / Contiguous Location" }).click();

    const extendsToCombos = page.locator("label", { hasText: "Extends To" }).locator("xpath=..").getByRole("combobox");
    await extendsToCombos.nth(0).click();
    await page.getByRole("option", { name: "Ankle/Malleolus", exact: true }).click();
    await extendsToCombos.nth(1).click();
    await page.getByRole("option", { name: "Lateral Foot", exact: true }).click();

    // The extension editor is a modal Dialog -- it must be closed before
    // interacting with anything behind it (e.g. the wound selector),
    // since the open dialog's backdrop intercepts clicks outside it.
    await page.keyboard.press("Escape");

    // Primary location is untouched by adding extensions.
    await expect(page.getByText(/Location:\s*Left lateral calf/i)).toBeVisible();
    // Only one impairment record exists -- extensions never silently
    // split the wound into separate records.
    await selectWoundCombobox(page).click();
    await expect(page.getByRole("option")).toHaveCount(1);
    await page.keyboard.press("Escape");

    // Remove the FIRST extension (Ankle) -- the primary location and the
    // SECOND extension (Lateral Foot) must both survive untouched.
    // Reopen the dialog -- it was closed above and its content unmounts
    // entirely while closed.
    await page.getByRole("button", { name: "Clarification / Extensions" }).click();
    const extensionRemoveButtons = page.locator("label", { hasText: "Extends To" }).locator("xpath=../..").getByRole("button", { name: "Remove" });
    await extensionRemoveButtons.first().click();
    await expect(page.getByText(/Location:\s*Left lateral calf/i)).toBeVisible();
    await expect(page.locator("label", { hasText: "Extends To" })).toHaveCount(1);

    await page.waitForTimeout(1000);
    await waitForAutosaveTick(page);
    await page.reload();
    await expect(page.getByText("Skin Impairment Workspace")).toBeVisible();
    // The single always-visible editor auto-selects this patient's only
    // active wound on load -- no separate "Open" affordance exists.
    await expect(page.getByText(/Location:\s*Left lateral calf/i)).toBeVisible();
    // The "Clarification / Extensions" disclosure is local component
    // state (a Dialog's `open` flag) -- it always starts closed on a
    // fresh mount, so it must be reopened after reload to see the
    // persisted extension data, which is what's actually under test
    // here (not whether the dialog itself remembers being open).
    await page.getByRole("button", { name: "Clarification / Extensions" }).click();
    await expect(page.locator("label", { hasText: "Extends To" })).toHaveCount(1);
  });

  // ====================================================================
  // PRODUCT OWNER REVIEW AND CONTINUATION DIRECTIVE Section 6 --
  // Device-Related Pressure Injury.
  // ====================================================================
  test("Device-Related Pressure Injury: anatomical site is preserved, device description is required to complete", async ({ page }) => {
    // See timeout note on A12 above -- set once in beforeEach.
    await addWound(page, "Pressure Injury");
    await fieldCombobox(page, "Anatomical Site").click();
    await page.getByRole("option", { name: "Nose", exact: true }).click();
    await fieldCombobox(page, "Stage / Category").click();
    await page.getByRole("option", { name: "Stage 2", exact: true }).click();

    await clickSegmentedOption(page, "Device-Related Pressure Injury?", "Yes");
    // Inventory/label must show the real anatomical site, never a bare
    // "Device Related" substitute label.
    await expect(page.getByText(/Location:\s*Nose/i)).toBeVisible();
    await expect(page.getByText(/^Device Related$/)).toHaveCount(0);

    // Device description left blank -- record must remain incomplete.
    // Wait for the background autosave tick first -- without it, the
    // just-created record was never persisted and "Back to RNICA" shows
    // zero records instead of an incomplete one.
    await waitForAutosaveTick(page);
    await page.getByRole("button", { name: "Back to RNICA" }).click();
    await openBodySystemsSkinSection(page);
    await expect(page.getByRole("button", { name: /Record.*Require Completion/i })).toBeVisible();

    // Fill in the device description and confirm it persists after reload.
    await page.getByRole("button", { name: /Add \/ Manage Skin Impairments/i }).click();
    await fieldInput(page, "Device Description (required)").fill("Oxygen device contact");
    await page.waitForTimeout(1000);
    await waitForAutosaveTick(page);
    await page.reload();
    await expect(page.getByText("Skin Impairment Workspace")).toBeVisible();
    // The single always-visible editor auto-selects this patient's only
    // active wound on load -- no separate "Open" affordance exists.
    await expect(fieldInput(page, "Device Description (required)")).toHaveValue("Oxygen device contact");
    await expect(page.getByText(/Location:\s*Nose/i)).toBeVisible();
  });
});
