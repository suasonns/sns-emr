/**
 * SNS Body Systems Workspace — Infection / Immunological pilot panel.
 *
 * Reuses the exact situation / requirement / Unable-to-Assess wiring proven
 * by every prior pilot (canonical state machine: `getSituationRequirements`,
 * `getMissingSituationRequirements`). Adds no fields beyond the ownership
 * registry's `infection_immunological` fact keys (infection_status,
 * infection_type, infection_findings, organism_information,
 * antimicrobial_treatment, precautions_isolation,
 * immunosuppression_status, infection_history,
 * infection_response_followup) — see ownership.ts.
 *
 * CRITICAL SCOPE RULE (product-owner ownership decision): Infection owns
 * facts specifically ABOUT an infection. It never reassesses the
 * underlying clinical problem owned by another system:
 * - Temperature is Vitals-owned and is NEVER captured, edited, or stored
 *   here (see `temperatureIsNotOwnedByInfection` in ownership.ts). This
 *   panel only displays a read-only, source-labeled reference value.
 * - Wound characteristics (type, location, stage, dimensions, bed,
 *   drainage, dressing) remain Integumentary-owned (see
 *   `woundFindingsAreNotOwnedByInfection`). Infection may reference an
 *   infected wound but never re-documents the wound itself.
 * - Urinary findings remain Genitourinary-owned (see
 *   `urinaryFindingsAreNotOwnedByInfection`).
 * - Respiratory findings (dyspnea, lung sounds) remain Respiratory-owned
 *   (see `respiratoryFindingsAreNotOwnedByInfection`).
 * - Allergy data remains owned by the existing authoritative allergy
 *   source; this panel never creates a second allergy store or editor
 *   (see `allergiesAreNotOwnedByInfection`).
 * These cross-system facts are surfaced below only as a compact, read-only,
 * source-labeled "Cross-system context" block — never as editable fields,
 * and never substituting for review in their owning system.
 *
 * CRITICAL RULE (sepsis independence): HOPE/comorbidity sepsis history and
 * current active-infection sepsis are independent facts. Neither is
 * derived from, or auto-set/cleared by, the other (see
 * `hopeSepsisHistoryDoesNotDeriveActiveInfectionSepsis` and
 * `activeInfectionSepsisDoesNotRewriteHopeSepsisHistory`). This panel's
 * `infectionStatus`/`sepsisCurrentlyActive` field is independent local RN
 * input; it never reads from, writes to, or defaults from any HOPE
 * comorbidity data source.
 *
 * CRITICAL RULE (RN Notes): the shared, optional `SystemNotesSection` is
 * placed last, after all structured findings and cross-system context,
 * before the Unable-to-Assess block — this is the SNS-wide placement
 * standard (per the SNS Clinical Notes Standard). The note is always
 * optional and never satisfies a structured finding or completes review
 * (see `systemNotesDoNotSatisfyStructuredFindings`).
 */
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
import { SystemNotesSection } from "../shared/SystemNotesSection";

const INFECTION_FACT_KEYS =
  OWNERSHIP_REGISTRY.find((rule) => rule.owner === "infection_immunological")?.factKeys ?? [];

const SITUATION_OPTIONS: { value: AssessmentSituation; label: string }[] = [
  { value: "no_current_concern", label: "No current concern" },
  { value: "stable_existing", label: "Stable existing" },
  { value: "new_or_worsening", label: "New / worsening" },
  { value: "unable_to_assess", label: "Unable to assess" },
];

const PRIOR_COMPARISON_OPTIONS = ["improved", "same", "worse", "unknown"] as const;
type PriorComparison = (typeof PRIOR_COMPARISON_OPTIONS)[number];

const INFECTION_STATUS_OPTIONS = ["none", "suspected", "confirmed", "resolved"] as const;
type InfectionStatusValue = (typeof INFECTION_STATUS_OPTIONS)[number];

const PRECAUTIONS_OPTIONS = ["none", "contact", "droplet", "airborne", "contact_plus_droplet"] as const;
type PrecautionsValue = (typeof PRECAUTIONS_OPTIONS)[number];

const HOPE_IMPACT_OPTIONS = ["not_yet_assessed", "yes", "no", "unclear"] as const;
export type HopeImpactValue = (typeof HOPE_IMPACT_OPTIONS)[number];

/**
 * Compact, read-only, source-labeled summaries surfaced from other systems'
 * already-captured data. Every field is optional free text supplied by the
 * caller (the shell); this component never fetches, derives, or infers
 * these values itself, and never renders them as editable. Absence of a
 * value is shown as "Not yet documented" — never treated as a finding.
 */
export interface InfectionCrossSystemContext {
  /** Integumentary-owned wound context, e.g. "Stage 2 sacral pressure injury". */
  woundSummary?: string;
  /** Genitourinary-owned urinary context. */
  urinarySummary?: string;
  /** Respiratory-owned respiratory context. */
  respiratorySummary?: string;
  /** Vitals-owned temperature value — reference only, never editable here. */
  temperatureSummary?: string;
  /** Existing authoritative allergy source — reference only, never a second allergy editor. */
  allergySummary?: string;
}

export interface InfectionFieldValues {
  screeningDateTime?: string;
  priorComparison?: PriorComparison;
  onsetOrSource?: string;

  /** infection_status + infection_type + infection_findings */
  infectionStatus?: InfectionStatusValue;
  infectionType?: string;
  infectionFindings?: string;

  /** organism_information */
  organismIdentified?: string;
  resistantOrganism?: string;
  cultureSource?: string;
  cultureResultDate?: string;

  /** antimicrobial_treatment */
  antimicrobialAgent?: string;
  antimicrobialRoute?: string;
  antimicrobialStartDate?: string;
  antimicrobialPlannedDuration?: string;
  treatmentResponse?: string;

  /** precautions_isolation */
  precautions?: PrecautionsValue;
  isolationDetails?: string;

  /** immunosuppression_status */
  immunosuppressionStatus?: string;
  immunosuppressionSource?: string;

  /** infection_history */
  infectionHistory?: string;

  /**
   * infection_response_followup — current active-infection sepsis flag.
   * Independent of, and never derived from, HOPE/comorbidity sepsis
   * history — see module docblock "sepsis independence".
   */
  sepsisCurrentlyActive?: HopeImpactValue;
  followUpPlan?: string;

  /** RN Notes — optional narrative context, placed last. See SystemNotesSection. */
  notes?: string;
}

export const INITIAL_INFECTION_FIELD_VALUES: InfectionFieldValues = {
  infectionStatus: "none",
  sepsisCurrentlyActive: "not_yet_assessed",
};

export interface InfectionSystemPanelProps {
  situation?: AssessmentSituation;
  onSituationChange: (situation: AssessmentSituation) => void;
  onRequirementSatisfied: (requirementKey: string) => void;
  onLimitationChange: (limitation: AssessmentLimitation) => void;
  missingRequirements: string[];
  values: InfectionFieldValues;
  onChange: (values: InfectionFieldValues) => void;
  /** Read-only cross-system reference context — see InfectionCrossSystemContext. */
  crossSystemContext?: InfectionCrossSystemContext;
}

export function InfectionSystemPanel({
  situation,
  onSituationChange,
  onRequirementSatisfied,
  onLimitationChange,
  missingRequirements,
  values,
  onChange,
  crossSystemContext,
}: InfectionSystemPanelProps) {
  const [scope, setScope] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [assessedPortion, setAssessedPortion] = useState("");
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [responsibleClinicianId, setResponsibleClinicianId] = useState("");
  const [timingOrContingency, setTimingOrContingency] = useState("");

  const requirements = situation ? getSituationRequirements(situation) : [];

  const set = <K extends keyof InfectionFieldValues>(key: K, value: InfectionFieldValues[K]) => {
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
        <CardTitle>Infection / Immunological</CardTitle>
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

            {/* infection_status / infection_type / infection_findings */}
            <div className="flex flex-col gap-2">
              <p className="text-[11px] font-medium text-rnica-muted">Infection status</p>
              <ToggleGroup
                type="single"
                value={values.infectionStatus}
                onValueChange={(v) => v && set("infectionStatus", v as InfectionStatusValue)}
              >
                {INFECTION_STATUS_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
              <Input
                placeholder="Infection type (e.g. UTI, pneumonia, wound infection, cellulitis)"
                value={values.infectionType ?? ""}
                onChange={(e) => set("infectionType", e.target.value)}
              />
              <Textarea
                placeholder="Infection findings"
                value={values.infectionFindings ?? ""}
                onChange={(e) => set("infectionFindings", e.target.value)}
              />
            </div>

            {/* organism_information */}
            <div className="flex flex-col gap-2 rounded-lg border border-rnica-border p-3">
              <p className="text-[11px] font-semibold text-rnica-textStrong">Organism / culture information</p>
              <Input
                placeholder="Organism identified"
                value={values.organismIdentified ?? ""}
                onChange={(e) => set("organismIdentified", e.target.value)}
              />
              <Input
                placeholder="Resistant organism (e.g. MRSA, VRE, C. diff)"
                value={values.resistantOrganism ?? ""}
                onChange={(e) => set("resistantOrganism", e.target.value)}
              />
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Input
                  placeholder="Culture source"
                  value={values.cultureSource ?? ""}
                  onChange={(e) => set("cultureSource", e.target.value)}
                />
                <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                  Culture result date
                  <Input
                    type="date"
                    value={values.cultureResultDate ?? ""}
                    onChange={(e) => set("cultureResultDate", e.target.value)}
                  />
                </label>
              </div>
            </div>

            {/* antimicrobial_treatment */}
            <div className="flex flex-col gap-2 rounded-lg border border-rnica-border p-3">
              <p className="text-[11px] font-semibold text-rnica-textStrong">Antimicrobial treatment</p>
              <Input
                placeholder="Antimicrobial agent"
                value={values.antimicrobialAgent ?? ""}
                onChange={(e) => set("antimicrobialAgent", e.target.value)}
              />
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Input
                  placeholder="Route"
                  value={values.antimicrobialRoute ?? ""}
                  onChange={(e) => set("antimicrobialRoute", e.target.value)}
                />
                <label className="flex flex-col gap-1 text-[11px] text-rnica-muted">
                  Start date
                  <Input
                    type="date"
                    value={values.antimicrobialStartDate ?? ""}
                    onChange={(e) => set("antimicrobialStartDate", e.target.value)}
                  />
                </label>
              </div>
              <Input
                placeholder="Planned duration"
                value={values.antimicrobialPlannedDuration ?? ""}
                onChange={(e) => set("antimicrobialPlannedDuration", e.target.value)}
              />
              <Textarea
                placeholder="Treatment response"
                value={values.treatmentResponse ?? ""}
                onChange={(e) => set("treatmentResponse", e.target.value)}
              />
            </div>

            {/* precautions_isolation */}
            <div className="flex flex-col gap-2">
              <p className="text-[11px] font-medium text-rnica-muted">Precautions / isolation</p>
              <ToggleGroup
                type="single"
                value={values.precautions}
                onValueChange={(v) => v && set("precautions", v as PrecautionsValue)}
              >
                {PRECAUTIONS_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option.replaceAll("_", " ")}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
              <Textarea
                placeholder="Isolation details"
                value={values.isolationDetails ?? ""}
                onChange={(e) => set("isolationDetails", e.target.value)}
              />
            </div>

            {/* immunosuppression_status */}
            <div className="flex flex-col gap-2">
              <p className="text-[11px] font-medium text-rnica-muted">Immunosuppression status</p>
              <Input
                placeholder="Immunosuppression status"
                value={values.immunosuppressionStatus ?? ""}
                onChange={(e) => set("immunosuppressionStatus", e.target.value)}
              />
              <Input
                placeholder="Source (e.g. chemotherapy, chronic steroids, transplant)"
                value={values.immunosuppressionSource ?? ""}
                onChange={(e) => set("immunosuppressionSource", e.target.value)}
              />
            </div>

            {/* infection_history */}
            <Textarea
              placeholder="Infection history"
              value={values.infectionHistory ?? ""}
              onChange={(e) => set("infectionHistory", e.target.value)}
            />

            {/* infection_response_followup — includes independent current sepsis flag */}
            <div className="flex flex-col gap-2 rounded-lg border border-rnica-borderAI bg-rnica-aiBg/30 p-3">
              <Badge variant="warning">
                Current active-infection sepsis — independent of, and never derived from, HOPE/comorbidity sepsis
                history
              </Badge>
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Sepsis currently active</p>
              <ToggleGroup
                type="single"
                value={values.sepsisCurrentlyActive}
                onValueChange={(v) => v && set("sepsisCurrentlyActive", v as HopeImpactValue)}
              >
                {HOPE_IMPACT_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={option}>
                    {option.replaceAll("_", " ")}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
              <Textarea
                placeholder="Infection response / follow-up plan"
                value={values.followUpPlan ?? ""}
                onChange={(e) => set("followUpPlan", e.target.value)}
              />
            </div>

            {/* Cross-system context — compact, read-only, source-labeled, non-substituting */}
            <div className="flex flex-col gap-1.5 rounded-lg border border-rnica-border bg-rnica-bgAlt p-3">
              <p className="text-[11px] font-semibold text-rnica-textStrong">Cross-system context (reference only)</p>
              <p className="text-[11px] text-rnica-muted">
                Wound (Integumentary): {crossSystemContext?.woundSummary ?? "Not yet documented"}
              </p>
              <p className="text-[11px] text-rnica-muted">
                Urinary (Genitourinary): {crossSystemContext?.urinarySummary ?? "Not yet documented"}
              </p>
              <p className="text-[11px] text-rnica-muted">
                Respiratory: {crossSystemContext?.respiratorySummary ?? "Not yet documented"}
              </p>
              <p className="text-[11px] text-rnica-muted">
                Temperature (Vitals): {crossSystemContext?.temperatureSummary ?? "Not yet documented"}
              </p>
              <p className="text-[11px] text-rnica-muted">
                Allergies: {crossSystemContext?.allergySummary ?? "Not yet documented"}
              </p>
              <p className="text-[10px] italic text-rnica-muted">
                Read-only. Does not substitute for review in the owning system.
              </p>
            </div>

            <SystemNotesSection
              id="infection-rn-notes"
              value={values.notes}
              onChange={(value) => set("notes", value)}
            />
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
                {INFECTION_FACT_KEYS.map((factKey) => (
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
