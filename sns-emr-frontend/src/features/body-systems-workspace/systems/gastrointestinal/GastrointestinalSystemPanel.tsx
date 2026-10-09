/**
 * SNS Body Systems Workspace — Gastrointestinal pilot panel (Phase 3).
 *
 * Phase 3 platform-stability-confirmation system: reuses the exact
 * situation / requirement / Unable-to-Assess wiring proven by the
 * Neurological pilot (canonical state machine: `getSituationRequirements`,
 * `getMissingSituationRequirements`) and the explicit symptom-detail +
 * HOPE-guardrail field pattern proven by the Respiratory and Cardiovascular
 * pilots. Adds no fields beyond the ownership registry's `gastrointestinal`
 * fact keys (bowel_status, gastrointestinal_symptoms) — see ownership.ts.
 * Bowel-status detail fields (last movement, pattern, consistency, regimen
 * response) and symptom-detail fields (nausea/vomiting/distension,
 * interventions given, response to intervention) are UI-level detail
 * captured under those two fact keys, not new facts.
 *
 * CRITICAL RULE: HOPE comfort impact and HOPE function impact are each a
 * separate, explicit RN assessment field. Neither is derived, defaulted,
 * or pre-filled from bowel-status or symptom-severity fields in this
 * component — there is no effect/derivation wired from any symptom field
 * to either HOPE field, by construction (same guardrail shape as
 * RespiratorySystemPanel / CardiovascularSystemPanel). Both default to
 * "not yet assessed" and only change when the RN explicitly selects a
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

const GASTROINTESTINAL_FACT_KEYS =
  OWNERSHIP_REGISTRY.find((rule) => rule.owner === "gastrointestinal")?.factKeys ?? [];

const SITUATION_OPTIONS: { value: AssessmentSituation; label: string }[] = [
  { value: "no_current_concern", label: "No current concern" },
  { value: "stable_existing", label: "Stable existing" },
  { value: "new_or_worsening", label: "New / worsening" },
  { value: "unable_to_assess", label: "Unable to assess" },
];

const BOWEL_PATTERN_OPTIONS = ["normal", "constipated", "diarrhea", "irregular"] as const;
type BowelPattern = (typeof BOWEL_PATTERN_OPTIONS)[number];

const BOWEL_CONSISTENCY_OPTIONS = ["hard", "formed", "soft", "loose", "watery"] as const;
type BowelConsistency = (typeof BOWEL_CONSISTENCY_OPTIONS)[number];

const PRIOR_COMPARISON_OPTIONS = ["improved", "same", "worse", "unknown"] as const;
type PriorComparison = (typeof PRIOR_COMPARISON_OPTIONS)[number];

const SYMPTOM_SEVERITY_OPTIONS = ["none", "mild", "moderate", "severe"] as const;
type SymptomSeverity = (typeof SYMPTOM_SEVERITY_OPTIONS)[number];

const RESPONSE_TO_INTERVENTION_OPTIONS = ["improved", "unchanged", "worse", "not_yet_known"] as const;
type ResponseToIntervention = (typeof RESPONSE_TO_INTERVENTION_OPTIONS)[number];

const HOPE_IMPACT_OPTIONS = ["not_yet_assessed", "yes", "no", "unclear"] as const;
export type HopeImpactValue = (typeof HOPE_IMPACT_OPTIONS)[number];

export interface GastrointestinalFieldValues {
  lastBowelMovementDateTime?: string;
  bowelPattern?: BowelPattern;
  bowelConsistency?: BowelConsistency;
  bowelRegimenResponse?: string;
  screeningDateTime?: string;
  priorComparison?: PriorComparison;
  onsetOrSource?: string;
  nauseaVomitingSeverity?: SymptomSeverity;
  abdominalPainDistensionSeverity?: SymptomSeverity;
  gastrointestinalSymptomDescription?: string;
  interventionsGiven?: string;
  responseToIntervention?: ResponseToIntervention;
  followUpNeeds?: string;
  /** Required explicit RN assessment — never derived from any severity field above. */
  hopeComfortImpact: HopeImpactValue;
  /** Required explicit RN assessment — never derived from any severity field above. */
  hopeFunctionImpact: HopeImpactValue;
}

export const INITIAL_GASTROINTESTINAL_FIELD_VALUES: GastrointestinalFieldValues = {
  hopeComfortImpact: "not_yet_assessed",
  hopeFunctionImpact: "not_yet_assessed",
};

export interface GastrointestinalSystemPanelProps {
  situation?: AssessmentSituation;
  onSituationChange: (situation: AssessmentSituation) => void;
  onRequirementSatisfied: (requirementKey: string) => void;
  onLimitationChange: (limitation: AssessmentLimitation) => void;
  missingRequirements: string[];
  values: GastrointestinalFieldValues;
  onChange: (values: GastrointestinalFieldValues) => void;
}

export function GastrointestinalSystemPanel({
  situation,
  onSituationChange,
  onRequirementSatisfied,
  onLimitationChange,
  missingRequirements,
  values,
  onChange,
}: GastrointestinalSystemPanelProps) {
  const [scope, setScope] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [assessedPortion, setAssessedPortion] = useState("");
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [responsibleClinicianId, setResponsibleClinicianId] = useState("");
  const [timingOrContingency, setTimingOrContingency] = useState("");

  const requirements = situation ? getSituationRequirements(situation) : [];

  const set = <K extends keyof GastrointestinalFieldValues>(key: K, value: GastrointestinalFieldValues[K]) => {
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
        <CardTitle>Gastrointestinal</CardTitle>
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
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                Last bowel movement date/time
                <Input
                  type="datetime-local"
                  value={values.lastBowelMovementDateTime ?? ""}
                  onChange={(e) => set("lastBowelMovementDateTime", e.target.value)}
                />
              </label>
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Bowel pattern</p>
                <ToggleGroup
                  type="single"
                  value={values.bowelPattern}
                  onValueChange={(v) => v && set("bowelPattern", v as BowelPattern)}
                >
                  {BOWEL_PATTERN_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
            </div>

            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Bowel consistency</p>
              <ToggleGroup
                type="single"
                value={values.bowelConsistency}
                onValueChange={(v) => v && set("bowelConsistency", v as BowelConsistency)}
              >
                {BOWEL_CONSISTENCY_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

            <Textarea
              placeholder="Bowel regimen response"
              value={values.bowelRegimenResponse ?? ""}
              onChange={(e) => set("bowelRegimenResponse", e.target.value)}
            />

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Nausea / vomiting severity</p>
                <ToggleGroup
                  type="single"
                  value={values.nauseaVomitingSeverity}
                  onValueChange={(v) => v && set("nauseaVomitingSeverity", v as SymptomSeverity)}
                >
                  {SYMPTOM_SEVERITY_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Abdominal pain / distension severity</p>
                <ToggleGroup
                  type="single"
                  value={values.abdominalPainDistensionSeverity}
                  onValueChange={(v) => v && set("abdominalPainDistensionSeverity", v as SymptomSeverity)}
                >
                  {SYMPTOM_SEVERITY_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
            </div>

            <Textarea
              placeholder="Gastrointestinal symptom description"
              value={values.gastrointestinalSymptomDescription ?? ""}
              onChange={(e) => set("gastrointestinalSymptomDescription", e.target.value)}
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
              <Badge variant="warning">Requires explicit RN assessment — never derived from severity</Badge>
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
                {GASTROINTESTINAL_FACT_KEYS.map((factKey) => (
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
