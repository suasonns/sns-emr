import { describe, expect, it } from "vitest";

import {
  buildVisitNoteComparisonState,
  buildVisitNoteNavItems,
  createEmptySupervisoryReview,
  validateSupervisoryReview,
  VISIT_NOTE_SECTION_ITEMS,
} from "./visitNoteHelpers";

function baseContent(overrides = {}) {
  return {
    visit_date: "2026-04-01",
    time_in: "09:00",
    pain: { pain_level: 1 },
    vitals: { weight: "140", mac: "24.0", bmi: "22.1" },
    functional_decline: { pps: 40, kps: 50, fast: "6d", nyha: "III" },
    signs_symptoms: {
      nutrition: { severity: "MODERATE", selected_findings: ["appetite_decline"] },
      mobility: { severity: "MODERATE", ambulatory_status: "LIMITED" },
      adl_assessment: { adl_total_score: 12 },
      fall_incidence: { assessed_no_issues: true },
      safety_issues: { assessed_no_issues: true },
    },
    supervisory_review: createEmptySupervisoryReview(),
    ...overrides,
  };
}

describe("buildVisitNoteComparisonState", () => {
  it("uses the most recent prior comparable visit before the current date", () => {
    const history = [
      {
        visit_id: "future",
        visit_date: "2026-05-01",
        visit_datetime: "2026-05-01T09:00:00Z",
        form_type: "ASSESS",
        content_snapshot: baseContent({ pain: { pain_level: 0 } }),
      },
      {
        visit_id: "match",
        visit_date: "2026-03-15",
        visit_datetime: "2026-03-15T09:00:00Z",
        form_type: "ASSESS",
        content_snapshot: baseContent({ pain: { pain_level: 3 }, functional_decline: { pps: 50 } }),
      },
      {
        visit_id: "older",
        visit_date: "2026-02-01",
        visit_datetime: "2026-02-01T09:00:00Z",
        form_type: "ASSESS",
        content_snapshot: baseContent({ pain: { pain_level: 6 } }),
      },
    ];

    const result = buildVisitNoteComparisonState(baseContent(), history);
    expect(result.previousEntry.visit_id).toBe("match");
    expect(result.groups.pain[0].statusLabel).toBe("Improved");
    expect(result.groups.function.find((item) => item.key === "pps").statusLabel).toBe("Worsened");
  });

  it("never treats blank current values as stable or zero", () => {
    const history = [
      {
        visit_id: "prior",
        visit_date: "2026-03-15",
        visit_datetime: "2026-03-15T09:00:00Z",
        form_type: "ASSESS",
        content_snapshot: baseContent({ vitals: { weight: "140" } }),
      },
    ];

    const result = buildVisitNoteComparisonState(baseContent({ vitals: { weight: "" } }), history);
    const weight = result.groups.nutrition.find((item) => item.key === "weight");
    expect(weight.statusLabel).toBe("Not comparable");
    expect(weight.currentDisplay).toBe("");
  });

  it("builds since-last summary items only from documented comparable values", () => {
    const history = [
      {
        visit_id: "prior",
        visit_date: "2026-03-15",
        visit_datetime: "2026-03-15T09:00:00Z",
        form_type: "ASSESS",
        content_snapshot: baseContent({
          pain: { pain_level: 3 },
          vitals: { weight: "141", mac: "", bmi: "" },
          functional_decline: { pps: 40, kps: 40 },
        }),
      },
    ];

    const result = buildVisitNoteComparisonState(baseContent(), history);
    expect(result.summaryItems.find((item) => item.key === "pain-level")).toMatchObject({
      statusLabel: "Improved",
      sectionId: "pain",
    });
    expect(result.summaryItems.find((item) => item.key === "pps")).toMatchObject({
      statusLabel: "Stable",
      sectionId: "function",
    });
    expect(result.summaryItems.some((item) => item.key === "mac")).toBe(false);
  });
});

describe("validateSupervisoryReview", () => {
  it("requires concern details and follow-up detail fields only when triggered", () => {
    const content = baseContent({
      supervisory_review: {
        hha: {
          assigned_staff_user_id: "staff-1",
          supervision_type: "PRESENT",
          observation_datetime: "2026-04-01T10:00",
          rn_supervisor_name: "RN Supervisor",
          services_meet_patient_needs: "NO",
          follows_care_plan: "YES",
          demonstrates_competency: "YES",
          communication_appropriate: "YES",
          infection_control_safety: "YES",
          patient_family_concerns: "YES",
          corrective_action_required: "YES",
          notification_documented: "YES",
          follow_up_required: "YES",
        },
      },
    });
    const context = {
      hha: { applicable: true },
      lvn_lpn: { applicable: false },
    };

    const errors = validateSupervisoryReview(content, context);
    expect(errors.map((item) => item.message)).toEqual(expect.arrayContaining([
      "HHA concern details is required.",
      "HHA corrective action details is required.",
      "HHA person notified is required.",
      "HHA notification date/time is required.",
      "HHA follow-up due date is required.",
    ]));
  });
});

describe("VISIT_NOTE_SECTION_ITEMS", () => {
  it("lists every full-body visit-note anchor in clinical navigation order", () => {
    expect(VISIT_NOTE_SECTION_ITEMS.map((item) => item.id)).toEqual([
      "top",
      "since-last",
      "vitals",
      "pain",
      "nutrition",
      "neuro",
      "cardiovascular",
      "respiratory",
      "immunological",
      "gi",
      "endocrine",
      "gu",
      "sleep-rest",
      "musculoskeletal",
      "skin",
      "function",
      "mobility",
      "adl",
      "falls-safety",
      "narrative",
      "care-provided",
      "checklist",
      "rn-supervision",
      "death-disposal",
    ]);
  });
});

describe("buildVisitNoteNavItems", () => {
  it("includes conditional visit-note sections only when they render", () => {
    expect(buildVisitNoteNavItems({
      isFullBody: true,
      isSpiritualVisit: false,
      isMswVisit: false,
      isContinuousCare: false,
      showSupervision: false,
      isDeathVisit: false,
    }).map((item) => item.id)).not.toContain("rn-supervision");

    expect(buildVisitNoteNavItems({
      isFullBody: true,
      isSpiritualVisit: false,
      isMswVisit: false,
      isContinuousCare: false,
      showSupervision: true,
      isDeathVisit: true,
    }).map((item) => item.id)).toEqual(expect.arrayContaining(["rn-supervision", "death-disposal", "immunological", "sleep-rest", "musculoskeletal"]));
  });
});
