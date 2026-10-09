/**
 * SNS Body Systems Workspace — Neurological pilot panel.
 *
 * Phase 1A pilot system #1. Implements the four situations (No current
 * concern / Stable existing / New-or-worsening / Unable to assess) driven
 * entirely by the canonical state machine (`SITUATION_REQUIREMENTS`,
 * `getMissingSituationRequirements`) — this component adds no extra
 * neurological fields beyond the ownership registry's `neurological`
 * fact keys (orientation, cognition, responsiveness, mental_status).
 */
import * as React from "react";
import { useState } from "react";
import { ToggleGroup, ToggleGroupItem } from "../../../../components/ui/toggle-group";
import { Textarea } from "../../../../components/ui/textarea";
import { Checkbox } from "../../../../components/ui/checkbox";
import { Input } from "../../../../components/ui/input";
import { Button } from "../../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";
import {
  OWNERSHIP_REGISTRY,
  getSituationRequirements,
  type AssessmentLimitation,
  type AssessmentSituation,
} from "../../../../domain/body-systems";

const NEUROLOGICAL_FACT_KEYS =
  OWNERSHIP_REGISTRY.find((rule) => rule.owner === "neurological")?.factKeys ?? [];

const SITUATION_OPTIONS: { value: AssessmentSituation; label: string }[] = [
  { value: "no_current_concern", label: "No current concern" },
  { value: "stable_existing", label: "Stable existing" },
  { value: "new_or_worsening", label: "New / worsening" },
  { value: "unable_to_assess", label: "Unable to assess" },
];

export interface NeurologicalSystemPanelProps {
  situation?: AssessmentSituation;
  onSituationChange: (situation: AssessmentSituation) => void;
  onRequirementSatisfied: (requirementKey: string) => void;
  onLimitationChange: (limitation: AssessmentLimitation) => void;
  missingRequirements: string[];
}

export function NeurologicalSystemPanel({
  situation,
  onSituationChange,
  onRequirementSatisfied,
  onLimitationChange,
  missingRequirements,
}: NeurologicalSystemPanelProps) {
  const [scope, setScope] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [assessedPortion, setAssessedPortion] = useState("");
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [responsibleClinicianId, setResponsibleClinicianId] = useState("");
  const [timingOrContingency, setTimingOrContingency] = useState("");

  const requirements = situation ? getSituationRequirements(situation) : [];

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
        <CardTitle>Neurological</CardTitle>
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

        {situation === "unable_to_assess" && (
          <div className="flex flex-col gap-3 rounded-lg border border-rnica-borderWarning bg-rnica-warningBg p-3">
            <p className="text-[11px] font-semibold text-rnica-orange">
              Unable to assess — scope, reason, assessed portion, follow-up, timing, and responsible clinician are
              all required. Historical findings do not satisfy this.
            </p>

            <div>
              <p className="mb-1 text-[11px] font-medium text-rnica-muted">Scope not assessed</p>
              <ul className="flex flex-col gap-1">
                {NEUROLOGICAL_FACT_KEYS.map((factKey) => (
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
