/**
 * SNS Body Systems Workspace — Nutrition pilot panel (Phase 6).
 *
 * Reuses the exact situation / requirement / Unable-to-Assess wiring
 * proven by every prior pilot (canonical state machine:
 * `getSituationRequirements`, `getMissingSituationRequirements`) and the
 * explicit symptom-detail + HOPE-guardrail field pattern proven by
 * Respiratory, Cardiovascular, Gastrointestinal, and Genitourinary. Adds
 * no fields beyond the ownership registry's `nutrition` fact keys (intake,
 * weight, weight_change, appetite, swallowing_nutritional_burden) — see
 * ownership.ts.
 *
 * CRITICAL RULE (Braden non-substitution — unique to this pilot): this
 * panel has no awareness of, and does not read, any Braden Scale
 * subscore. The Braden nutrition subscore lives under Integumentary's
 * `braden` fact key (see ownership.ts) and is a pressure-risk input only.
 * Explicit RN review of this panel's situation/requirements is the sole
 * way a Nutrition review is ever marked complete — see
 * `bradenNutritionSubscoreDoesNotCompleteNutritionReview` in
 * domain/body-systems/ownership.ts, exercised directly by this panel's
 * test file. Presence of any Braden data elsewhere in the chart can never
 * substitute for, pre-select, or auto-complete this panel's own situation
 * or requirements.
 *
 * CRITICAL RULE: HOPE comfort impact and HOPE function impact are each a
 * separate, explicit RN assessment field. Neither is derived, defaulted,
 * or pre-filled from any nutrition-status or severity field in this
 * component. Both default to "not yet assessed" and only change when the
 * RN explicitly selects a value.
 */
import * as React from "react";
import { useState } from "react";
import { ToggleGroup, ToggleGroupItem } from "../../../../components/ui/toggle-group";
import { Textarea } from "../../../../components/ui/textarea";
import { Checkbox } from "../../../../components/ui/checkbox";
import { Input } from "../../../../components/ui/input";
import { Button } from "../../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";
import { Badge } from "../../../../components/ui/badge";
import {
  OWNERSHIP_REGISTRY,
  getSituationRequirements,
  type AssessmentLimitation,
  type AssessmentSituation,
} from "../../../../domain/body-systems";

const NUTRITION_FACT_KEYS = OWNERSHIP_REGISTRY.find((rule) => rule.owner === "nutrition")?.factKeys ?? [];

const SITUATION_OPTIONS: { value: AssessmentSituation; label: string }[] = [
  { value: "no_current_concern", label: "No current concern" },
  { value: "stable_existing", label: "Stable existing" },
  { value: "new_or_worsening", label: "New / worsening" },
  { value: "unable_to_assess", label: "Unable to assess" },
];

const INTAKE_OPTIONS = ["adequate", "decreased", "minimal"] as const;
type IntakeStatus = (typeof INTAKE_OPTIONS)[number];

const APPETITE_OPTIONS = ["good", "fair", "poor", "anorexic"] as const;
type AppetiteStatus = (typeof APPETITE_OPTIONS)[number];

const WEIGHT_CHANGE_DIRECTION_OPTIONS = ["gain", "loss", "stable", "unknown"] as const;
type WeightChangeDirection = (typeof WEIGHT_CHANGE_DIRECTION_OPTIONS)[number];

const SWALLOWING_BURDEN_OPTIONS = ["none", "mild", "moderate", "severe"] as const;
type SwallowingBurden = (typeof SWALLOWING_BURDEN_OPTIONS)[number];

const PRIOR_COMPARISON_OPTIONS = ["improved", "same", "worse", "unknown"] as const;
type PriorComparison = (typeof PRIOR_COMPARISON_OPTIONS)[number];

const RESPONSE_TO_INTERVENTION_OPTIONS = ["improved", "unchanged", "worse", "not_yet_known"] as const;
type ResponseToIntervention = (typeof RESPONSE_TO_INTERVENTION_OPTIONS)[number];

const HOPE_IMPACT_OPTIONS = ["not_yet_assessed", "yes", "no", "unclear"] as const;
export type HopeImpactValue = (typeof HOPE_IMPACT_OPTIONS)[number];

export interface NutritionFieldValues {
  intakeStatus?: IntakeStatus;
  appetiteStatus?: AppetiteStatus;
  currentWeight?: string;
  weightChangeDirection?: WeightChangeDirection;
  weightChangeAmount?: string;
  weightChangeTimeframe?: string;
  swallowingBurden?: SwallowingBurden;
  nutritionStatusNotes?: string;
  screeningDateTime?: string;
  priorComparison?: PriorComparison;
  onsetOrSource?: string;
  interventionsGiven?: string;
  responseToIntervention?: ResponseToIntervention;
  followUpNeeds?: string;
  /** Required explicit RN assessment — never derived from any field above, and never from any Braden subscore. */
  hopeComfortImpact: HopeImpactValue;
  /** Required explicit RN assessment — never derived from any field above, and never from any Braden subscore. */
  hopeFunctionImpact: HopeImpactValue;
}

export const INITIAL_NUTRITION_FIELD_VALUES: NutritionFieldValues = {
  hopeComfortImpact: "not_yet_assessed",
  hopeFunctionImpact: "not_yet_assessed",
};

export interface NutritionSystemPanelProps {
  situation?: AssessmentSituation;
  onSituationChange: (situation: AssessmentSituation) => void;
  onRequirementSatisfied: (requirementKey: string) => void;
  onLimitationChange: (limitation: AssessmentLimitation) => void;
  missingRequirements: string[];
  values: NutritionFieldValues;
  onChange: (values: NutritionFieldValues) => void;
}

export function NutritionSystemPanel({
  situation,
  onSituationChange,
  onRequirementSatisfied,
  onLimitationChange,
  missingRequirements,
  values,
  onChange,
}: NutritionSystemPanelProps) {
  const [scope, setScope] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [assessedPortion, setAssessedPortion] = useState("");
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [responsibleClinicianId, setResponsibleClinicianId] = useState("");
  const [timingOrContingency, setTimingOrContingency] = useState("");

  const requirements = situation ? getSituationRequirements(situation) : [];

  const set = <K extends keyof NutritionFieldValues>(key: K, value: NutritionFieldValues[K]) => {
    onChange({ ...values, [key]: value });
  };

  const submitLimitation = () => {
    onLimitationChange({
      scope,
      reason,
      assessedPortion: assessedPortion || undefined,
      followUpRequired,
      responsibleClinicianId: responsibleClinicianId || undefined,
      timingOrContingency: timingOrContingency || undefined,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Nutrition</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div>
          <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Situation</p>
          <ToggleGroup
            type="single"
            value={situation}
            onValueChange={(value) => value && onSituationChange(value as AssessmentSituation)}
          >
            {SITUATION_OPTIONS.map((option) => (
              <ToggleGroupItem key={option.value} value={option.value}>
                {option.label}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>

        {situation && situation !== "unable_to_assess" && (
          <div className="flex flex-col gap-2">
            <p className="text-[11px] font-medium text-rnica-muted">Required for this situation</p>
            <ul className="flex flex-col gap-1">
              {requirements.map((requirement) => (
                <li key={requirement} className="flex items-center gap-2 text-[12px]">
                  <Checkbox
                    checked={!missingRequirements.includes(requirement)}
                    onCheckedChange={(checked) => checked && onRequirementSatisfied(requirement)}
                  />
                  {requirement.replaceAll("_", " ")}
                </li>
              ))}
            </ul>
          </div>
        )}

        {situation && situation !== "unable_to_assess" && (
          <>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                Screening date/time
                <Input
                  type="datetime-local"
                  value={values.screeningDateTime ?? ""}
                  onChange={(e) => set("screeningDateTime", e.target.value)}
                />
              </label>
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Prior comparison</p>
                <ToggleGroup
                  type="single"
                  value={values.priorComparison}
                  onValueChange={(v) => v && set("priorComparison", v as PriorComparison)}
                >
                  {PRIOR_COMPARISON_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
            </div>

            <Textarea
              placeholder="Onset / source"
              value={values.onsetOrSource ?? ""}
              onChange={(e) => set("onsetOrSource", e.target.value)}
            />

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Intake</p>
                <ToggleGroup
                  type="single"
                  value={values.intakeStatus}
                  onValueChange={(v) => v && set("intakeStatus", v as IntakeStatus)}
                >
                  {INTAKE_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Appetite</p>
                <ToggleGroup
                  type="single"
                  value={values.appetiteStatus}
                  onValueChange={(v) => v && set("appetiteStatus", v as AppetiteStatus)}
                >
                  {APPETITE_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                Current weight
                <Input
                  placeholder="Current weight"
                  value={values.currentWeight ?? ""}
                  onChange={(e) => set("currentWeight", e.target.value)}
                />
              </label>
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Weight change</p>
                <ToggleGroup
                  type="single"
                  value={values.weightChangeDirection}
                  onValueChange={(v) => v && set("weightChangeDirection", v as WeightChangeDirection)}
                >
                  {WEIGHT_CHANGE_DIRECTION_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                Weight change amount / timeframe
                <Input
                  placeholder="e.g. 5 lb over 30 days"
                  value={values.weightChangeAmount ?? ""}
                  onChange={(e) => set("weightChangeAmount", e.target.value)}
                />
              </label>
            </div>

            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Swallowing / nutritional burden</p>
              <ToggleGroup
                type="single"
                value={values.swallowingBurden}
                onValueChange={(v) => v && set("swallowingBurden", v as SwallowingBurden)}
              >
                {SWALLOWING_BURDEN_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

            <Textarea
              placeholder="Nutrition status notes"
              value={values.nutritionStatusNotes ?? ""}
              onChange={(e) => set("nutritionStatusNotes", e.target.value)}
            />

            <Textarea
              placeholder="Interventions given"
              value={values.interventionsGiven ?? ""}
              onChange={(e) => set("interventionsGiven", e.target.value)}
            />

            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Response to intervention</p>
              <ToggleGroup
                type="single"
                value={values.responseToIntervention}
                onValueChange={(v) => v && set("responseToIntervention", v as ResponseToIntervention)}
              >
                {RESPONSE_TO_INTERVENTION_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option.replaceAll("_", " ")}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

            <Textarea
              placeholder="Follow-up needs"
              value={values.followUpNeeds ?? ""}
              onChange={(e) => set("followUpNeeds", e.target.value)}
            />

            <div className="flex flex-col gap-2 rounded-lg border border-rnica-borderAI bg-rnica-aiBg/30 p-3">
              <Badge variant="warning">Requires explicit RN assessment — never derived from severity or Braden data</Badge>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div>
                  <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">HOPE comfort impact</p>
                  <ToggleGroup
                    type="single"
                    value={values.hopeComfortImpact}
                    onValueChange={(v) => v && set("hopeComfortImpact", v as HopeImpactValue)}
                  >
                    {HOPE_IMPACT_OPTIONS.map((option) => (
                      <ToggleGroupItem key={option} value={option}>
                        {option.replaceAll("_", " ")}
                      </ToggleGroupItem>
                    ))}
                  </ToggleGroup>
                </div>
                <div>
                  <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">HOPE function impact</p>
                  <ToggleGroup
                    type="single"
                    value={values.hopeFunctionImpact}
                    onValueChange={(v) => v && set("hopeFunctionImpact", v as HopeImpactValue)}
                  >
                    {HOPE_IMPACT_OPTIONS.map((option) => (
                      <ToggleGroupItem key={option} value={option}>
                        {option.replaceAll("_", " ")}
                      </ToggleGroupItem>
                    ))}
                  </ToggleGroup>
                </div>
              </div>
            </div>
          </>
        )}

        {situation === "unable_to_assess" && (
          <div className="flex flex-col gap-3 rounded-lg border border-rnica-borderWarning bg-rnica-warningBg p-3">
            <p className="text-[11px] font-semibold text-rnica-orange">
              Unable to assess — scope, reason, assessed portion, follow-up, timing, and responsible clinician are
              all required. Historical findings do not satisfy this.
            </p>

            <div>
              <p className="mb-1 text-[11px] font-medium text-rnica-muted">Scope not assessed</p>
              <ul className="flex flex-col gap-1">
                {NUTRITION_FACT_KEYS.map((factKey) => (
                  <li key={factKey} className="flex items-center gap-2 text-[12px]">
                    <Checkbox
                      checked={scope.includes(factKey)}
                      onCheckedChange={(checked) =>
                        setScope((prev) => (checked ? [...prev, factKey] : prev.filter((k) => k !== factKey)))
                      }
                    />
                    {factKey.replaceAll("_", " ")}
                  </li>
                ))}
              </ul>
            </div>

            <Textarea
              placeholder="Reason unable to assess (required)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Input
              placeholder="Assessed portion, if any"
              value={assessedPortion}
              onChange={(e) => setAssessedPortion(e.target.value)}
            />
            <label className="flex items-center gap-2 text-[12px]">
              <Checkbox checked={followUpRequired} onCheckedChange={(checked) => setFollowUpRequired(Boolean(checked))} />
              Follow-up required
            </label>
            <Input
              placeholder="Responsible clinician"
              value={responsibleClinicianId}
              onChange={(e) => setResponsibleClinicianId(e.target.value)}
            />
            <Input
              placeholder="Timing / contingency"
              value={timingOrContingency}
              onChange={(e) => setTimingOrContingency(e.target.value)}
            />
            <Button size="sm" onClick={submitLimitation} disabled={!reason.trim()}>
              Save limitation
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
