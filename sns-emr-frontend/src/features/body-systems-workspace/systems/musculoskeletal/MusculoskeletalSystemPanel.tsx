/**
 * SNS Body Systems Workspace — Musculoskeletal pilot panel (Phase 7).
 *
 * Reuses the exact situation / requirement / Unable-to-Assess wiring
 * proven by every prior pilot (canonical state machine:
 * `getSituationRequirements`, `getMissingSituationRequirements`) and the
 * explicit symptom-detail + HOPE-guardrail field pattern proven by
 * Respiratory, Cardiovascular, Gastrointestinal, Genitourinary, and
 * Nutrition. Adds no fields beyond the ownership registry's
 * `musculoskeletal` fact keys (gait, balance, transfers, mobility,
 * weakness_as_mobility_function) — see ownership.ts.
 *
 * CRITICAL SCOPE RULE: per the accepted Musculoskeletal Architecture and
 * Ownership-Boundary Review, the following are explicitly OUT of scope
 * for this panel and are not represented here in any form (no fields, no
 * hidden state, no TODO scaffolding): ADLs (bathing, dressing, toileting,
 * transferring, eating, grooming), fall history, fall injuries, fall-risk
 * level, safety scoring, assistive devices, contractures, rigidity,
 * contracture location, ECOG, and personal-care aide tasks. Ownership of
 * those concepts remains UNRESOLVED and is not assigned to Musculoskeletal
 * by this implementation.
 *
 * CRITICAL RULE (Braden mobility non-substitution): this panel has no
 * awareness of, and does not read, any Braden Scale subscore. The Braden
 * mobility subscore lives under Integumentary's `braden` fact key (see
 * ownership.ts) and is a pressure-risk input only. Explicit RN review of
 * this panel's situation/requirements is the sole way a Musculoskeletal
 * review is ever marked complete — see
 * `bradenMobilitySubscoreDoesNotCompleteMusculoskeletalReview` in
 * domain/body-systems/ownership.ts, exercised directly by this panel's
 * test file. Presence of any Braden data elsewhere in the chart can never
 * substitute for, pre-select, or auto-complete this panel's own situation
 * or requirements, and can never set gait, balance, transfers, mobility,
 * weakness, HOPE comfort impact, or HOPE function impact.
 *
 * CRITICAL RULE: HOPE comfort impact and HOPE function impact are each a
 * separate, explicit RN assessment field. Neither is derived, defaulted,
 * or pre-filled from any musculoskeletal-status field in this component,
 * nor from any Braden subscore, fall history, or ADL data. Both default
 * to "not yet assessed" and only change when the RN explicitly selects a
 * value.
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

const MUSCULOSKELETAL_FACT_KEYS =
  OWNERSHIP_REGISTRY.find((rule) => rule.owner === "musculoskeletal")?.factKeys ?? [];

const SITUATION_OPTIONS: { value: AssessmentSituation; label: string }[] = [
  { value: "no_current_concern", label: "No current concern" },
  { value: "stable_existing", label: "Stable existing" },
  { value: "new_or_worsening", label: "New / worsening" },
  { value: "unable_to_assess", label: "Unable to assess" },
];

const GAIT_OPTIONS = ["steady", "unsteady", "unable"] as const;
type GaitStatus = (typeof GAIT_OPTIONS)[number];

const BALANCE_OPTIONS = ["steady", "unsteady", "unable_to_stand"] as const;
type BalanceStatus = (typeof BALANCE_OPTIONS)[number];

const TRANSFER_OPTIONS = ["independent", "assisted", "dependent"] as const;
type TransferStatus = (typeof TRANSFER_OPTIONS)[number];

const MOBILITY_OPTIONS = ["independent", "limited", "bedbound"] as const;
type MobilityStatus = (typeof MOBILITY_OPTIONS)[number];

const WEAKNESS_OPTIONS = ["none", "mild", "moderate", "severe"] as const;
type WeaknessStatus = (typeof WEAKNESS_OPTIONS)[number];

const PRIOR_COMPARISON_OPTIONS = ["improved", "same", "worse", "unknown"] as const;
type PriorComparison = (typeof PRIOR_COMPARISON_OPTIONS)[number];

const RESPONSE_TO_INTERVENTION_OPTIONS = ["improved", "unchanged", "worse", "not_yet_known"] as const;
type ResponseToIntervention = (typeof RESPONSE_TO_INTERVENTION_OPTIONS)[number];

const HOPE_IMPACT_OPTIONS = ["not_yet_assessed", "yes", "no", "unclear"] as const;
export type HopeImpactValue = (typeof HOPE_IMPACT_OPTIONS)[number];

export interface MusculoskeletalFieldValues {
  gaitStatus?: GaitStatus;
  balanceStatus?: BalanceStatus;
  transferStatus?: TransferStatus;
  mobilityStatus?: MobilityStatus;
  weaknessStatus?: WeaknessStatus;
  musculoskeletalStatusNotes?: string;
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

export const INITIAL_MUSCULOSKELETAL_FIELD_VALUES: MusculoskeletalFieldValues = {
  hopeComfortImpact: "not_yet_assessed",
  hopeFunctionImpact: "not_yet_assessed",
};

export interface MusculoskeletalSystemPanelProps {
  situation?: AssessmentSituation;
  onSituationChange: (situation: AssessmentSituation) => void;
  onRequirementSatisfied: (requirementKey: string) => void;
  onLimitationChange: (limitation: AssessmentLimitation) => void;
  missingRequirements: string[];
  values: MusculoskeletalFieldValues;
  onChange: (values: MusculoskeletalFieldValues) => void;
}

export function MusculoskeletalSystemPanel({
  situation,
  onSituationChange,
  onRequirementSatisfied,
  onLimitationChange,
  missingRequirements,
  values,
  onChange,
}: MusculoskeletalSystemPanelProps) {
  const [scope, setScope] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [assessedPortion, setAssessedPortion] = useState("");
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [responsibleClinicianId, setResponsibleClinicianId] = useState("");
  const [timingOrContingency, setTimingOrContingency] = useState("");

  const requirements = situation ? getSituationRequirements(situation) : [];

  const set = <K extends keyof MusculoskeletalFieldValues>(key: K, value: MusculoskeletalFieldValues[K]) => {
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
        <CardTitle>Musculoskeletal</CardTitle>
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
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Gait</p>
                <ToggleGroup
                  type="single"
                  value={values.gaitStatus}
                  onValueChange={(v) => v && set("gaitStatus", v as GaitStatus)}
                >
                  {GAIT_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option.replaceAll("_", " ")}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Balance</p>
                <ToggleGroup
                  type="single"
                  value={values.balanceStatus}
                  onValueChange={(v) => v && set("balanceStatus", v as BalanceStatus)}
                >
                  {BALANCE_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option.replaceAll("_", " ")}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Transfers</p>
                <ToggleGroup
                  type="single"
                  value={values.transferStatus}
                  onValueChange={(v) => v && set("transferStatus", v as TransferStatus)}
                >
                  {TRANSFER_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Mobility</p>
                <ToggleGroup
                  type="single"
                  value={values.mobilityStatus}
                  onValueChange={(v) => v && set("mobilityStatus", v as MobilityStatus)}
                >
                  {MOBILITY_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
            </div>

            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Weakness (mobility/function impact)</p>
              <ToggleGroup
                type="single"
                value={values.weaknessStatus}
                onValueChange={(v) => v && set("weaknessStatus", v as WeaknessStatus)}
              >
                {WEAKNESS_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

            <Textarea
              placeholder="Musculoskeletal status notes"
              value={values.musculoskeletalStatusNotes ?? ""}
              onChange={(e) => set("musculoskeletalStatusNotes", e.target.value)}
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
                {MUSCULOSKELETAL_FACT_KEYS.map((factKey) => (
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
