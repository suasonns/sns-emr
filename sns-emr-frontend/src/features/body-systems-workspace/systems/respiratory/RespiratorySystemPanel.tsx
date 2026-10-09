/**
 * SNS Body Systems Workspace — Respiratory pilot panel.
 *
 * Phase 1A pilot system #2. Implements the symptom-focused Respiratory
 * fields from the approved design, scoped to the ownership registry's
 * `respiratory` fact keys.
 *
 * Situation / requirement / Unable-to-Assess wiring (added for persistence
 * integration): Respiratory was the first pilot panel built and predates
 * the situation/limitation convention proven by the Neurological pilot and
 * reused by every later pilot (Cardiovascular, Gastrointestinal,
 * Genitourinary, Nutrition, Musculoskeletal, Integumentary, Infection).
 * This panel now uses that exact same, already-approved wiring — copied
 * from `CardiovascularSystemPanel.tsx`, not redesigned — so Respiratory's
 * `situation` and `AssessmentLimitation` can be driven by, and persisted
 * through, the same orchestration state (`useBodySystemsAssessmentState`)
 * and backend contract (`SystemAssessment.situation` /
 * `SystemAssessment.limitation_*`) every other system already uses.
 *
 * CRITICAL RULE: HOPE comfort impact and HOPE function impact are each a
 * separate, explicit RN assessment field. Neither is derived, defaulted,
 * or pre-filled from SOB severity (or from any other field in this
 * component) — there is no effect/derivation wired from `sobSeverity` to
 * either HOPE field, by construction. Both default to "not yet assessed"
 * and only change when the RN explicitly selects a value.
 */
import * as React from "react";
import { useState } from "react";
import { ToggleGroup, ToggleGroupItem } from "../../../../components/ui/toggle-group";
import { Textarea } from "../../../../components/ui/textarea";
import { Input } from "../../../../components/ui/input";
import { Checkbox } from "../../../../components/ui/checkbox";
import { Button } from "../../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";
import { Badge } from "../../../../components/ui/badge";
import {
  OWNERSHIP_REGISTRY,
  getSituationRequirements,
  type AssessmentLimitation,
  type AssessmentSituation,
} from "../../../../domain/body-systems";

const RESPIRATORY_FACT_KEYS = OWNERSHIP_REGISTRY.find((rule) => rule.owner === "respiratory")?.factKeys ?? [];

const SITUATION_OPTIONS: { value: AssessmentSituation; label: string }[] = [
  { value: "no_current_concern", label: "No current concern" },
  { value: "stable_existing", label: "Stable existing" },
  { value: "new_or_worsening", label: "New / worsening" },
  { value: "unable_to_assess", label: "Unable to assess" },
];

const SOB_SEVERITY_OPTIONS = ["none", "mild", "moderate", "severe"] as const;
type SobSeverity = (typeof SOB_SEVERITY_OPTIONS)[number];

const PRIOR_COMPARISON_OPTIONS = ["improved", "same", "worse", "unknown"] as const;
type PriorComparison = (typeof PRIOR_COMPARISON_OPTIONS)[number];

const OXYGEN_DELIVERY_OPTIONS = ["room_air", "nasal_cannula", "mask", "ventilator", "other"] as const;
type OxygenDelivery = (typeof OXYGEN_DELIVERY_OPTIONS)[number];

const HOPE_IMPACT_OPTIONS = ["not_yet_assessed", "yes", "no", "unclear"] as const;
export type HopeImpactValue = (typeof HOPE_IMPACT_OPTIONS)[number];

export interface RespiratoryFieldValues {
  sobSeverity?: SobSeverity;
  screeningDateTime?: string;
  priorComparison?: PriorComparison;
  onsetOrSource?: string;
  lungSounds?: string;
  respiratoryPattern?: string;
  oxygenDelivery?: OxygenDelivery;
  flowRateLpm?: string;
  ventilatorInfo?: string;
  spo2Value?: string;
  spo2Context?: string;
  exertionTolerance?: string;
  /** Required explicit RN assessment — never derived from sobSeverity. */
  hopeComfortImpact: HopeImpactValue;
  /** Required explicit RN assessment — never derived from sobSeverity. */
  hopeFunctionImpact: HopeImpactValue;
}

export const INITIAL_RESPIRATORY_FIELD_VALUES: RespiratoryFieldValues = {
  hopeComfortImpact: "not_yet_assessed",
  hopeFunctionImpact: "not_yet_assessed",
};

export interface RespiratorySystemPanelProps {
  situation?: AssessmentSituation;
  onSituationChange: (situation: AssessmentSituation) => void;
  onRequirementSatisfied: (requirementKey: string) => void;
  onLimitationChange: (limitation: AssessmentLimitation) => void;
  missingRequirements: string[];
  values: RespiratoryFieldValues;
  onChange: (values: RespiratoryFieldValues) => void;
}

export function RespiratorySystemPanel({
  situation,
  onSituationChange,
  onRequirementSatisfied,
  onLimitationChange,
  missingRequirements,
  values,
  onChange,
}: RespiratorySystemPanelProps) {
  const [scope, setScope] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [assessedPortion, setAssessedPortion] = useState("");
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [responsibleClinicianId, setResponsibleClinicianId] = useState("");
  const [timingOrContingency, setTimingOrContingency] = useState("");

  const requirements = situation ? getSituationRequirements(situation) : [];

  const set = <K extends keyof RespiratoryFieldValues>(key: K, value: RespiratoryFieldValues[K]) => {
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

  const showsOxygenFlowRate = values.oxygenDelivery === "nasal_cannula" || values.oxygenDelivery === "mask";
  const showsVentilatorInfo = values.oxygenDelivery === "ventilator";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Respiratory</CardTitle>
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
            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">SOB severity</p>
              <ToggleGroup
                type="single"
                value={values.sobSeverity}
                onValueChange={(v) => v && set("sobSeverity", v as SobSeverity)}
              >
                {SOB_SEVERITY_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

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
            <Textarea
              placeholder="Lung sounds"
              value={values.lungSounds ?? ""}
              onChange={(e) => set("lungSounds", e.target.value)}
            />
            <Textarea
              placeholder="Respiratory pattern"
              value={values.respiratoryPattern ?? ""}
              onChange={(e) => set("respiratoryPattern", e.target.value)}
            />

            <div>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Oxygen delivery</p>
              <ToggleGroup
                type="single"
                value={values.oxygenDelivery}
                onValueChange={(v) => v && set("oxygenDelivery", v as OxygenDelivery)}
              >
                {OXYGEN_DELIVERY_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option.replaceAll("_", " ")}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

            {showsOxygenFlowRate && (
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                Flow rate (L/min)
                <Input value={values.flowRateLpm ?? ""} onChange={(e) => set("flowRateLpm", e.target.value)} />
              </label>
            )}
            {showsVentilatorInfo && (
              <Textarea
                placeholder="Ventilator information"
                value={values.ventilatorInfo ?? ""}
                onChange={(e) => set("ventilatorInfo", e.target.value)}
              />
            )}

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                SpO2
                <Input value={values.spo2Value ?? ""} onChange={(e) => set("spo2Value", e.target.value)} />
              </label>
              <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                SpO2 context
                <Input value={values.spo2Context ?? ""} onChange={(e) => set("spo2Context", e.target.value)} />
              </label>
            </div>

            <Textarea
              placeholder="Exertion tolerance"
              value={values.exertionTolerance ?? ""}
              onChange={(e) => set("exertionTolerance", e.target.value)}
            />

            <div className="flex flex-col gap-2 rounded-lg border border-rnica-borderAI bg-rnica-aiBg/30 p-3">
              <Badge variant="warning">Requires explicit RN assessment — never derived from severity</Badge>

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
                {RESPIRATORY_FACT_KEYS.map((factKey) => (
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
