import { describe, it, expect } from "vitest";
import { computeGastrointestinalDocumentationCoverage, computeGastrointestinalRequiresFollowUp } from "./RNICA.jsx";

// PRODUCT OWNER IMPLEMENTATION DIRECTIVE (2026-10-21) "GI Cleanup and
// HOPE N0520" Section 5/13/17.L -- "Bowel Program coverage" tests: proves
// every valid Bowel Program response (including "Unable To Determine",
// the value most likely to be mistaken for "unanswered") clears the
// general "Document bowel program status" warning, and that the
// Abdominal Girth item is never marked complete by an empty value alone
// (the visible "cm" unit label is UI-only and is never read by
// `check`/`summarize`).

function findItem(coverage, key) {
  return coverage.find((item) => item.key === key);
}

describe("computeGastrointestinalDocumentationCoverage -- Bowel Program (Section 5/13)", () => {
  it("flags Bowel Program unresolved when nothing has been selected", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({}), "bowelProgram");
    expect(item.complete).toBe(false);
    expect(item.unresolvedHint).toBe("Document bowel program status");
  });

  it.each([
    ["No Bowel Program"],
    ["Bowel Program Active"],
    ["Unable To Determine"],
  ])("clears the warning when Bowel Program = %s", (value) => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({ bowelProgram: value }), "bowelProgram");
    expect(item.complete).toBe(true);
    expect(item.unresolvedHint).toBeNull();
    expect(item.value).toBe(value);
  });
});

describe("computeGastrointestinalDocumentationCoverage -- Abdominal Girth (Section 4/13)", () => {
  it("is unresolved when empty, regardless of the visible 'cm' unit label (UI-only, never stored/read)", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({}), "abdominalGirth");
    expect(item.complete).toBe(false);
    expect(item.unresolvedHint).toBe("Document abdominal girth");
  });

  it("is complete once a bare numeric value is stored", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({ abdominalGirth: "120" }), "abdominalGirth");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("120");
  });
});

describe("computeGastrointestinalDocumentationCoverage -- Vomiting Occurrences (Section 3/13)", () => {
  it("is unresolved when no occurrence count has been recorded", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({ vomiting: "Moderate" }), "vomitingOccurrences24h");
    expect(item.complete).toBe(false);
  });

  it("is complete once a whole-number occurrence count is recorded", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({ vomiting: "Moderate", vomitingOccurrences24h: "3" }), "vomitingOccurrences24h");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("3");
  });
});

// PRODUCT OWNER IMPLEMENTATION DIRECTIVE (2026-10-21) "GI Cleanup and HOPE
// N0520" Section 13 -- the N0520 coverage item is a SEPARATE item from the
// general "Bowel Program" item above, and is omitted entirely (not shown
// as perpetually unresolved) unless HOPE N0520 itself applies.
describe("computeGastrointestinalDocumentationCoverage -- HOPE N0520 (Section 13)", () => {
  it("is omitted entirely when N0520 does not apply (no opioid trigger)", () => {
    const coverage = computeGastrointestinalDocumentationCoverage({ medications: {} });
    expect(findItem(coverage, "bowelRegimenN0520")).toBeUndefined();
  });

  it("is unresolved when applicable but not yet answered", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({ medications: { scheduledOpioid: true } }), "bowelRegimenN0520");
    expect(item.complete).toBe(false);
  });

  it("is complete once a structured Yes response is recorded with its initiated date", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({
      medications: { prnOpioid: true },
      bowelRegimenResponse: "Yes",
      bowelRegimenInitiatedDate: "2026-02-01",
    }), "bowelRegimenN0520");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("Yes");
  });

  it("is complete once a structured No - No Documented Reason response is recorded", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({
      medications: { prnOpioid: true },
      bowelRegimenResponse: "No - No Documented Reason",
    }), "bowelRegimenN0520");
    expect(item.complete).toBe(true);
  });

  it("stays separate from the general Bowel Program item -- answering one does not resolve the other", () => {
    const coverage = computeGastrointestinalDocumentationCoverage({ medications: { scheduledOpioid: true }, bowelProgram: "No Bowel Program" });
    expect(findItem(coverage, "bowelProgram").complete).toBe(true);
    expect(findItem(coverage, "bowelRegimenN0520").complete).toBe(false);
  });

  // Section 13 -- three distinct exact-wording unresolved states, in the
  // order a nurse would naturally resolve them while filling out the
  // structured N0520 workflow. (PRODUCT OWNER CORRECTION 2026-10-21 "N0520
  // Reason -- One Fact, One Location" retired the multi-select reason
  // checklist + paired free-text field in favor of a single-select
  // dropdown -- there is no longer a 4th "enter other reason" state;
  // selecting any one reason, including "Other clinical contraindication",
  // completes this item. Further explanation belongs in the general,
  // optional GI Notes field.)
  it("hints to select a bowel-regimen response when unanswered", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({ medications: { scheduledOpioid: true } }), "bowelRegimenN0520");
    expect(item.unresolvedHint).toBe("HOPE N0520: Select bowel-regimen response.");
  });

  it("hints to enter the initiated date when Yes is selected but no date is recorded", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({
      medications: { scheduledOpioid: true },
      bowelRegimenResponse: "Yes",
    }), "bowelRegimenN0520");
    expect(item.unresolvedHint).toBe("HOPE N0520: Enter date initiated or continued.");
  });

  it("hints to select a documented reason when No - Reason Documented has no reason selected", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({
      medications: { scheduledOpioid: true },
      bowelRegimenResponse: "No - Reason Documented",
    }), "bowelRegimenN0520");
    expect(item.unresolvedHint).toBe("HOPE N0520: Select documented reason.");
  });

  it("is complete once a single reason is selected from the dropdown, including Other", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({
      medications: { scheduledOpioid: true },
      bowelRegimenResponse: "No - Reason Documented",
      bowelRegimenReason: "Other clinical contraindication",
    }), "bowelRegimenN0520");
    expect(item.complete).toBe(true);
    expect(item.unresolvedHint).toBeNull();
  });

  it("falls back to the first non-Other value in a historical multi-select array when the new singular field is empty", () => {
    const item = findItem(computeGastrointestinalDocumentationCoverage({
      medications: { scheduledOpioid: true },
      bowelRegimenResponse: "No - Reason Documented",
      bowelRegimenReasons: ["Diarrhea"],
    }), "bowelRegimenN0520");
    expect(item.complete).toBe(true);
    expect(item.value).toBe("No - Reason Documented");
  });
});

// PRODUCT OWNER IMPLEMENTATION DIRECTIVE (2026-10-21) "GI Cleanup and HOPE
// N0520" Section 15 -- an unanswered N0520 (documentation gap) must never
// by itself create a POC/follow-up candidate; only an explicit "No"
// response is a real clinical concern.
describe("computeGastrointestinalRequiresFollowUp -- HOPE N0520 gap vs. concern (Section 15)", () => {
  it("does NOT require follow-up merely because N0520 is unanswered", () => {
    expect(computeGastrointestinalRequiresFollowUp({ bowelRegimenResponse: "" })).toBe(false);
  });

  it("does NOT require follow-up when the response is Yes", () => {
    expect(computeGastrointestinalRequiresFollowUp({ bowelRegimenResponse: "Yes" })).toBe(false);
  });

  it("requires follow-up when the response is No - Reason Documented", () => {
    expect(computeGastrointestinalRequiresFollowUp({ bowelRegimenResponse: "No - Reason Documented", bowelRegimenReasons: ["Patient/Family Declined"] })).toBe(true);
  });

  it("requires follow-up when the response is No - No Documented Reason", () => {
    expect(computeGastrointestinalRequiresFollowUp({ bowelRegimenResponse: "No - No Documented Reason" })).toBe(true);
  });

  it("falls back to the historical freeform-reason signal only when no structured response was ever recorded", () => {
    expect(computeGastrointestinalRequiresFollowUp({ reasonBowelRegimenNotInitiated: "Patient declined due to GI upset" })).toBe(true);
  });
});
