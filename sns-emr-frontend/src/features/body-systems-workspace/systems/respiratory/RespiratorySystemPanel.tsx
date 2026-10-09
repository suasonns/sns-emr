/**
 * SNS Body Systems Workspace — Respiratory pilot panel.
 *
 * Phase 1A pilot system #2. Implements the symptom-focused Respiratory
 * fields from the approved design, scoped to the ownership registry's
 * `respiratory` fact keys.
 *
 * CRITICAL RULE: HOPE comfort impact and HOPE function impact are each a
 * separate, explicit RN assessment field. Neither is derived, defaulted,
 * or pre-filled from SOB severity (or from any other field in this
 * component) — there is no effect/derivation wired from `sobSeverity` to
 * either HOPE field, by construction. Both default to "not yet assessed"
 * and only change when the RN explicitly selects a value.
 */
import * as React from "react";
import { ToggleGroup, ToggleGroupItem } from "../../../../components/ui/toggle-group";
import { Textarea } from "../../../../components/ui/textarea";
import { Input } from "../../../../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";
import { Badge } from "../../../../components/ui/badge";

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
  values: RespiratoryFieldValues;
  onChange: (values: RespiratoryFieldValues) => void;
}

export function RespiratorySystemPanel({ values, onChange }: RespiratorySystemPanelProps) {
  const set = <K extends keyof RespiratoryFieldValues>(key: K, value: RespiratoryFieldValues[K]) => {
    onChange({ ...values, [key]: value });
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
      </CardContent>
    </Card>
  );
}
