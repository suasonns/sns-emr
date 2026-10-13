import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

import {
  getMissingProductAuthorizedRequirements,
  type RespiratoryProductAuthorizedValues,
} from "./respiratoryProductRequirements";

/**
 * Aggregate enforcement test for docs/governance/SNS_RETIRED_FEATURES.json.
 *
 * PRODUCT-OWNER DECISION ("Permanent Retirement Enforcement -- No Silent
 * Field Reactivation"): "Add one aggregate test that enumerates every
 * retirement entry and checks all supported enforcement layers. Do not
 * rely only on individual hand-written tests that can be forgotten in
 * another worktree."
 *
 * This test reads the registry directly (not a hand-copied list) so a
 * future worktree merge/rebase/cherry-pick that silently re-adds a
 * registry entry's field to an active completion path fails here, even if
 * the field-specific test elsewhere was dropped.
 *
 * Scope: this file enforces the "completion requirement" layer (never
 * appears as a product-authorized unresolved requirement, regardless of
 * draft field values) for every Respiratory registry entry whose id maps
 * to a known draft property. Active-UI/tab-order enforcement for these
 * same entries lives in RespiratoryPanel.test.tsx (LEGACY_HIDDEN_FIELD_IDS
 * is a private, unexported module constant by design -- see that file's
 * "never renders ..." tests).
 */

const REGISTRY_PATH = path.resolve(__dirname, "../../../../docs/governance/SNS_RETIRED_FEATURES.json");

// PRODUCT-OWNER DIRECTIVE ("Reversible Retired Feature Pool With Explicit
// Reactivation Authorization", schemaVersion 2): field names renamed from
// the schemaVersion-1 registry (id -> featureId, label -> clinicianLabel,
// section -> owningSection); status enum expanded with REACTIVATION_APPROVED
// / REACTIVATED / ACTIVE (not expected in this file's entries today, but
// accepted so a future reactivation doesn't fail JSON parsing here).
interface RetiredFeatureEntry {
  featureId: string;
  clinicianLabel: string;
  owningSection: string;
  status:
    | "ACTIVE"
    | "RETIRED_FROM_ACTIVE_WORKFLOW"
    | "DEFERRED_FROM_ACTIVE_WORKFLOW"
    | "REACTIVATION_APPROVED"
    | "REACTIVATED";
}

interface Registry {
  retiredFeatures: RetiredFeatureEntry[];
}

function loadRegistry(): Registry {
  const raw = readFileSync(REGISTRY_PATH, "utf-8");
  return JSON.parse(raw) as Registry;
}

// Maps a registry entry's dotted id suffix (camelCase) to the draft
// property/fieldId pair the product-requirements engine actually keys on.
// Only entries that ever had a completion-requirement push are listed --
// several registry entries (e.g. Cough Action Description/Response/
// Date-Time) never had their own push() and are enforced purely at the
// UI-rendering layer (RespiratoryPanel.test.tsx), not here.
const COMPLETION_ENGINE_CHECKS: Record<string, (missing: string[]) => void> = {
  "respiratory.comfortFunctionEvidence": (missing) => {
    expect(missing).not.toContain("respiratory_comfort_function_evidence");
  },
};

describe("SNS_RETIRED_FEATURES.json registry enforcement (Respiratory)", () => {
  const registry = loadRegistry();
  const respiratoryEntries = registry.retiredFeatures.filter((entry) => entry.owningSection === "Respiratory");

  it("registry file is non-empty and well-formed", () => {
    expect(Array.isArray(registry.retiredFeatures)).toBe(true);
    expect(registry.retiredFeatures.length).toBeGreaterThan(0);
    for (const entry of registry.retiredFeatures) {
      expect(entry.featureId).toBeTruthy();
      expect([
        "ACTIVE",
        "RETIRED_FROM_ACTIVE_WORKFLOW",
        "DEFERRED_FROM_ACTIVE_WORKFLOW",
        "REACTIVATION_APPROVED",
        "REACTIVATED",
      ]).toContain(entry.status);
      // Every entry committed to this file today predates any approved
      // reactivation -- if this ever fails, a reactivation workflow step
      // (registry status change) ran without the corresponding dedicated
      // reactivation commit/tests this file also enforces.
      expect(["RETIRED_FROM_ACTIVE_WORKFLOW", "DEFERRED_FROM_ACTIVE_WORKFLOW"]).toContain(entry.status);
    }
  });

  it("every Respiratory registry entry with a known completion-engine mapping never reappears as an unresolved requirement", () => {
    // Exercise the engine across the input shapes most likely to
    // historically have triggered each retired field, so a regression
    // that re-adds a push() call fails here regardless of which specific
    // draft state triggers it.
    const probeInputs: RespiratoryProductAuthorizedValues[] = [
      {},
      { assessmentContext: "CURRENT_CONCERNS_ASSESSED", comfortFunctionImpact: "IMPACT_PRESENT" },
      { assessmentContext: "CURRENT_CONCERNS_ASSESSED", comfortFunctionImpact: "UNABLE_TO_ASSESS" },
      { coughType: "Productive", hemoptysisPresent: true },
      { respiratorySupportStatus: "IN_USE" },
    ];

    let checkedAtLeastOne = false;
    for (const entry of respiratoryEntries) {
      const check = COMPLETION_ENGINE_CHECKS[entry.featureId];
      if (!check) continue;
      checkedAtLeastOne = true;
      for (const input of probeInputs) {
        const missing = getMissingProductAuthorizedRequirements(input).map((gap) => gap.fieldId);
        check(missing);
      }
    }
    expect(checkedAtLeastOne).toBe(true);
  });
});
