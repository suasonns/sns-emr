/**
 * SNS Body Systems Workspace — Genitourinary pilot panel (Phase 4).
 *
 * Phase 4 platform-stability-confirmation system: reuses the exact
 * situation / requirement / Unable-to-Assess wiring proven by the
 * Neurological pilot (canonical state machine: `getSituationRequirements`,
 * `getMissingSituationRequirements`) and the explicit symptom-detail +
 * HOPE-guardrail field pattern proven by Respiratory, Cardiovascular, and
 * Gastrointestinal. Adds no fields beyond the ownership registry's
 * `genitourinary` fact keys (urinary_status, genitourinary_symptoms) — see
 * ownership.ts. Urinary-status detail fields (continence, catheter status,
 * voiding pattern) and symptom-detail fields (urinary symptom description,
 * interventions given, response to intervention) are UI-level detail
 * captured under those two fact keys, not new facts. No additional GU
 * fields were introduced; this panel has zero cross-system entanglement
 * (no Braden interaction, unlike Nutrition/Musculoskeletal).
 *
 * CRITICAL RULE: HOPE comfort impact and HOPE function impact are each a
 * separate, explicit RN assessment field. Neither is derived, defaulted,
 * or pre-filled from urinary-status or symptom-severity fields in this
 * component — there is no effect/derivation wired from any symptom field
 * to either HOPE field, by construction (same guardrail shape as
 * RespiratorySystemPanel / CardiovascularSystemPanel / GastrointestinalSystemPanel).
 * Both default to "not yet assessed" and only change when the RN
 * explicitly selects a value.
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

const GENITOURINARY_FACT_KEYS =
  OWNERSHIP_REGISTRY.find((rule) => rule.owner === "genitourinary")?.factKeys ?? [];

const SITUATION_OPTIONS: { value: AssessmentSituation; label: string }[] = [
  { value: "no_current_concern", label: "No current concern" },
  { value: "stable_existing", label: "Stable existing" },
  { value: "new_or_worsening", label: "New / worsening" },
  { value: "unable_to_assess", label: "Unable to assess" },
];

const CONTINENCE_STATUS_OPTIONS = ["continent", "stress_incontinence", "urge_incontinence", "incontinent"] as const;
type ContinenceStatus = (typeof CONTINENCE_STATUS_OPTIONS)[number];

const CATHETER_STATUS_OPTIONS = ["none", "indwelling_foley", "suprapubic", "intermittent_cath"] as const;
type CatheterStatus = (typeof CATHETER_STATUS_OPTIONS)[number];

const VOIDING_PATTERN_OPTIONS = ["normal", "frequency", "urgency", "retention", "hesitancy"] as const;
type VoidingPattern = (typeof VOIDING_PATTERN_OPTIONS)[number];

const PRIOR_COMPARISON_OPTIONS = ["improved", "same", "worse", "unknown"] as const;
type PriorComparison = (typeof PRIOR_COMPARISON_OPTIONS)[number];

const SYMPTOM_SEVERITY_OPTIONS = ["none", "mild", "moderate", "severe"] as const;
type SymptomSeverity = (typeof SYMPTOM_SEVERITY_OPTIONS)[number];

const RESPONSE_TO_INTERVENTION_OPTIONS = ["improved", "unchanged", "worse", "not_yet_known"] as const;
type ResponseToIntervention = (typeof RESPONSE_TO_INTERVENTION_OPTIONS)[number];

const HOPE_IMPACT_OPTIONS = ["not_yet_assessed", "yes", "no", "unclear"] as const;
export type HopeImpactValue = (typeof HOPE_IMPACT_OPTIONS)[number];

export interface GenitourinaryFieldValues {
  continenceStatus?: ContinenceStatus;
  catheterStatus?: CatheterStatus;
  voidingPattern?: VoidingPattern;
  urinaryStatusNotes?: string;
  screeningDateTime?: string;
  priorComparison?: PriorComparison;
  onsetOrSource?: string;
  urinarySymptomSeverity?: SymptomSeverity;
  genitourinarySymptomDescription?: string;
  interventionsGiven?: string;
  responseToIntervention?: ResponseToIntervention;
  followUpNeeds?: string;
  /** Required explicit RN assessment — never derived from any severity field above. */
  hopeComfortImpact: HopeImpactValue;
  /** Required explicit RN assessment — never derived from any severity field above. */
  hopeFunctionImpact: HopeImpactValue;
}

export const INITIAL_GENITOURINARY_FIELD_VALUES: GenitourinaryFieldValues = {
  hopeComfortImpact: "not_yet_assessed",
  hopeFunctionImpact: "not_yet_assessed",
};

export interface GenitourinarySystemPanelProps {
  situation?: AssessmentSituation;
  onSituationChange: (situation: AssessmentSituation) => void;
  onRequirementSatisfied: (requirementKey: string) => void;
  onLimitationChange: (limitation: AssessmentLimitation) => void;
  missingRequirements: string[];
  values: GenitourinaryFieldValues;
  onChange: (values: GenitourinaryFieldValues) => void;
}

export function GenitourinarySystemPanel({
  situation,
  onSituationChange,
  onRequirementSatisfied,
  onLimitationChange,
  missingRequirements,
  values,
  onChange,
}: GenitourinarySystemPanelProps) {
  const [scope, setScope] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [assessedPortion, setAssessedPortion] = useState("");
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [responsibleClinicianId, setResponsibleClinicianId] = useState("");
  const [timingOrContingency, setTimingOrContingency] = useState("");

  const requirements = situation ? getSituationRequirements(situation) : [];

  const set = <K extends keyof GenitourinaryFieldValues>(key: K, value: GenitourinaryFieldValues[K]) => {
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
        <CardTitle>Genitourinary</CardTitle>
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
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Continence status</p>
                <ToggleGroup
                  type="single"
                  value={values.continenceStatus}
                  onValueChange={(v) => v && set("continenceStatus", v as ContinenceStatus)}
                >
                  {CONTINENCE_STATUS_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option.replaceAll("_", " ")}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Catheter status</p>
                <ToggleGroup
                  type="single"
                  value={values.catheterStatus}
                  onValueChange={(v) => v && set("catheterStatus", v as CatheterStatus)}
                >
                  {CATHETER_STATUS_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option.replaceAll("_", " ")}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
            </div>

            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Voiding pattern</p>
              <ToggleGroup
                type="single"
                value={values.voidingPattern}
                onValueChange={(v) => v && set("voidingPattern", v as VoidingPattern)}
              >
                {VOIDING_PATTERN_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

            <Textarea
              placeholder="Urinary status notes"
              value={values.urinaryStatusNotes ?? ""}
              onChange={(e) => set("urinaryStatusNotes", e.target.value)}
            />

            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Urinary symptom severity</p>
              <ToggleGroup
                type="single"
                value={values.urinarySymptomSeverity}
                onValueChange={(v) => v && set("urinarySymptomSeverity", v as SymptomSeverity)}
              >
                {SYMPTOM_SEVERITY_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

            <Textarea
              placeholder="Genitourinary symptom description"
              value={values.genitourinarySymptomDescription ?? ""}
              onChange={(e) => set("genitourinarySymptomDescription", e.target.value)}
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
                {GENITOURINARY_FACT_KEYS.map((factKey) => (
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
