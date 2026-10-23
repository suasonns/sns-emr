import { describe, it, expect } from "vitest";
import {
  isN0520Applicable,
  bowelRegimenCmsCode,
  legacyBowelRegimenResponse,
  BOWEL_REGIMEN_RESPONSE_YES,
  BOWEL_REGIMEN_RESPONSE_NO_REASON_DOCUMENTED,
  BOWEL_REGIMEN_RESPONSE_NO_NO_REASON,
} from "./n0520.js";

// PRODUCT OWNER IMPLEMENTATION DIRECTIVE (2026-10-21) "GI Cleanup and
// HOPE N0520" Sections 7-12/17 -- proves the ONE authoritative
// applicability selector is driven strictly by N0500A/N0510A
// (Scheduled/PRN Opioid "initiated or continued"), never by pain
// severity, a GI symptom, or an opioid merely present, and that the CMS
// code mapping (2/1/0, plus the "9 - Not applicable" skip-logic
// convention already used elsewhere in the HOPE export) is correct.

describe("isN0520Applicable", () => {
  it("is false with no medications data at all", () => {
    expect(isN0520Applicable({})).toBe(false);
    expect(isN0520Applicable(undefined)).toBe(false);
  });

  it("is true when Scheduled Opioid (N0500A) was initiated/continued", () => {
    expect(isN0520Applicable({ scheduledOpioid: true })).toBe(true);
  });

  it("is true when PRN Opioid (N0510A) was initiated/continued", () => {
    expect(isN0520Applicable({ prnOpioid: true })).toBe(true);
  });

  it("is NOT triggered by an opioid merely present with no initiated/continued flag", () => {
    // "merely present" would be a field like `opioidOnMedList: true` --
    // the selector only ever reads scheduledOpioid/prnOpioid.
    expect(isN0520Applicable({ opioidOnMedList: true, scheduledOpioid: false, prnOpioid: false })).toBe(false);
  });
});

describe("bowelRegimenCmsCode", () => {
  it("returns CMS code 9 / 'Not applicable' when N0520 does not apply", () => {
    expect(bowelRegimenCmsCode({}, "")).toEqual(["9", "Not applicable"]);
  });

  it("returns null (caller renders the incomplete placeholder) when applicable but unanswered", () => {
    expect(bowelRegimenCmsCode({ scheduledOpioid: true }, "")).toBeNull();
  });

  it("maps Yes -> CMS code 2", () => {
    expect(bowelRegimenCmsCode({ scheduledOpioid: true }, BOWEL_REGIMEN_RESPONSE_YES)[0]).toBe("2");
  });

  it("maps No - Reason Documented -> CMS code 1", () => {
    expect(bowelRegimenCmsCode({ prnOpioid: true }, BOWEL_REGIMEN_RESPONSE_NO_REASON_DOCUMENTED)[0]).toBe("1");
  });

  it("maps No - No Documented Reason -> CMS code 0", () => {
    expect(bowelRegimenCmsCode({ prnOpioid: true }, BOWEL_REGIMEN_RESPONSE_NO_NO_REASON)[0]).toBe("0");
  });
});

describe("legacyBowelRegimenResponse", () => {
  it("maps a legacy bowelRegimen=true to Yes", () => {
    expect(legacyBowelRegimenResponse({ bowelRegimen: true })).toBe(BOWEL_REGIMEN_RESPONSE_YES);
  });

  it("maps a legacy bowelRegimen=false (with an opioid trigger) to No - No Documented Reason", () => {
    expect(legacyBowelRegimenResponse({ bowelRegimen: false, scheduledOpioid: true })).toBe(BOWEL_REGIMEN_RESPONSE_NO_NO_REASON);
  });

  it("returns '' when there is no legacy data to derive from", () => {
    expect(legacyBowelRegimenResponse({})).toBe("");
  });
});
