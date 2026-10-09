/**
 * SNS Body Systems Workspace — Cardiovascular pilot panel (Phase 2).
 *
 * Phase 2 architecture-confirmation system: reuses the exact situation /
 * requirement / Unable-to-Assess wiring proven by the Neurological pilot
 * (canonical state machine: `getSituationRequirements`,
 * `getMissingSituationRequirements`) and the explicit symptom-detail +
 * HOPE-guardrail field pattern proven by the Respiratory pilot. Adds no
 * fields beyond the ownership registry's `cardiovascular` fact keys
 * (edema, pulse_rhythm, heart_sounds_perfusion,
 * blood_pressure_orthostatic_findings, chest_pain, syncope, circulation,
 * cardiac_devices) — see ownership.ts.
 *
 * CRITICAL RULE: HOPE comfort impact and HOPE function impact are each a
 * separate, explicit RN assessment field. Neither is derived, defaulted,
 * or pre-filled from chest-pain severity, edema severity, or any other
 * field in this component — there is no effect/derivation wired from any
 * symptom field to either HOPE field, by construction (same guardrail
 * shape as RespiratorySystemPanel). Both default to "not yet assessed"
 * and only change when the RN explicitly selects a value.
 *
 * Non-duplication: edema is owned here, not by Integumentary — see
 * `edemaIsNotOwnedByIntegumentary` / `canReassessEdemaIn` in
 * src/domain/body-systems/ownership.ts.
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

const CARDIOVASCULAR_FACT_KEYS =
  OWNERSHIP_REGISTRY.find((rule) => rule.owner === "cardiovascular")?.factKeys ?? [];

const SITUATION_OPTIONS: { value: AssessmentSituation; label: string }[] = [
  { value: "no_current_concern", label: "No current concern" },
  { value: "stable_existing", label: "Stable existing" },
  { value: "new_or_worsening", label: "New / worsening" },
  { value: "unable_to_assess", label: "Unable to assess" },
];

const EDEMA_SEVERITY_OPTIONS = ["none", "trace", "mild", "moderate", "severe"] as const;
type EdemaSeverity = (typeof EDEMA_SEVERITY_OPTIONS)[number];

const PULSE_RHYTHM_OPTIONS = ["regular", "irregular"] as const;
type PulseRhythm = (typeof PULSE_RHYTHM_OPTIONS)[number];

const PRIOR_COMPARISON_OPTIONS = ["improved", "same", "worse", "unknown"] as const;
type PriorComparison = (typeof PRIOR_COMPARISON_OPTIONS)[number];

const CHEST_PAIN_SEVERITY_OPTIONS = ["none", "mild", "moderate", "severe"] as const;
type ChestPainSeverity = (typeof CHEST_PAIN_SEVERITY_OPTIONS)[number];

const HOPE_IMPACT_OPTIONS = ["not_yet_assessed", "yes", "no", "unclear"] as const;
export type HopeImpactValue = (typeof HOPE_IMPACT_OPTIONS)[number];

export interface CardiovascularFieldValues {
  edemaSeverity?: EdemaSeverity;
  edemaLocation?: string;
  pulseRateBpm?: string;
  pulseRhythm?: PulseRhythm;
  heartSoundsPerfusion?: string;
  bloodPressureReading?: string;
  orthostaticFindings?: string;
  screeningDateTime?: string;
  priorComparison?: PriorComparison;
  onsetOrSource?: string;
  chestPainSeverity?: ChestPainSeverity;
  chestPainDescription?: string;
  syncopeOccurrence?: string;
  circulationStatus?: string;
  cardiacDeviceStatus?: string;
  /** Required explicit RN assessment — never derived from any severity field above. */
  hopeComfortImpact: HopeImpactValue;
  /** Required explicit RN assessment — never derived from any severity field above. */
  hopeFunctionImpact: HopeImpactValue;
}

export const INITIAL_CARDIOVASCULAR_FIELD_VALUES: CardiovascularFieldValues = {
  hopeComfortImpact: "not_yet_assessed",
  hopeFunctionImpact: "not_yet_assessed",
};

export interface CardiovascularSystemPanelProps {
  situation?: AssessmentSituation;
  onSituationChange: (situation: AssessmentSituation) => void;
  onRequirementSatisfied: (requirementKey: string) => void;
  onLimitationChange: (limitation: AssessmentLimitation) => void;
  missingRequirements: string[];
  values: CardiovascularFieldValues;
  onChange: (values: CardiovascularFieldValues) => void;
}

export function CardiovascularSystemPanel({
  situation,
  onSituationChange,
  onRequirementSatisfied,
  onLimitationChange,
  missingRequirements,
  values,
  onChange,
}: CardiovascularSystemPanelProps) {
  const [scope, setScope] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [assessedPortion, setAssessedPortion] = useState("");
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [responsibleClinicianId, setResponsibleClinicianId] = useState("");
  const [timingOrContingency, setTimingOrContingency] = useState("");

  const requirements = situation ? getSituationRequirements(situation) : [];

  const set = <K extends keyof CardiovascularFieldValues>(key: K, value: CardiovascularFieldValues[K]) => {
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
        <CardTitle>Cardiovascular</CardTitle>
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

            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Edema severity</p>
              <ToggleGroup
                type="single"
                value={values.edemaSeverity}
                onValueChange={(v) => v && set("edemaSeverity", v as EdemaSeverity)}
              >
                {EDEMA_SEVERITY_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>
            <Input
              placeholder="Edema location"
              value={values.edemaLocation ?? ""}
              onChange={(e) => set("edemaLocation", e.target.value)}
            />

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                Pulse rate (bpm)
                <Input value={values.pulseRateBpm ?? ""} onChange={(e) => set("pulseRateBpm", e.target.value)} />
              </label>
              <div>
                <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Pulse rhythm</p>
                <ToggleGroup
                  type="single"
                  value={values.pulseRhythm}
                  onValueChange={(v) => v && set("pulseRhythm", v as PulseRhythm)}
                >
                  {PULSE_RHYTHM_OPTIONS.map((option) => (
                    <ToggleGroupItem key={option} value={option}>
                      {option}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
            </div>

            <Textarea
              placeholder="Heart sounds / perfusion (cap refill, skin color/temp)"
              value={values.heartSoundsPerfusion ?? ""}
              onChange={(e) => set("heartSoundsPerfusion", e.target.value)}
            />

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                Blood pressure
                <Input
                  value={values.bloodPressureReading ?? ""}
                  onChange={(e) => set("bloodPressureReading", e.target.value)}
                />
              </label>
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                Orthostatic findings
                <Input
                  value={values.orthostaticFindings ?? ""}
                  onChange={(e) => set("orthostaticFindings", e.target.value)}
                />
              </label>
            </div>

            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Chest pain severity</p>
              <ToggleGroup
                type="single"
                value={values.chestPainSeverity}
                onValueChange={(v) => v && set("chestPainSeverity", v as ChestPainSeverity)}
              >
                {CHEST_PAIN_SEVERITY_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>
            <Textarea
              placeholder="Chest pain description"
              value={values.chestPainDescription ?? ""}
              onChange={(e) => set("chestPainDescription", e.target.value)}
            />

            <Textarea
              placeholder="Syncope / near-syncope occurrence"
              value={values.syncopeOccurrence ?? ""}
              onChange={(e) => set("syncopeOccurrence", e.target.value)}
            />
            <Textarea
              placeholder="Circulation status"
              value={values.circulationStatus ?? ""}
              onChange={(e) => set("circulationStatus", e.target.value)}
            />
            <Textarea
              placeholder="Cardiac device status (pacemaker, ICD, etc.)"
              value={values.cardiacDeviceStatus ?? ""}
              onChange={(e) => set("cardiacDeviceStatus", e.target.value)}
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
                {CARDIOVASCULAR_FACT_KEYS.map((factKey) => (
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
