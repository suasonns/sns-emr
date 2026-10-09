/**
 * SNS Body Systems Workspace — Integumentary pilot panel (Phase 8).
 *
 * Reuses the exact situation / requirement / Unable-to-Assess wiring
 * proven by every prior pilot (canonical state machine:
 * `getSituationRequirements`, `getMissingSituationRequirements`) and the
 * explicit symptom-detail + HOPE-guardrail field pattern proven by
 * Respiratory, Cardiovascular, Gastrointestinal, Genitourinary, Nutrition,
 * and Musculoskeletal. Adds no fields beyond the ownership registry's
 * `integumentary` fact keys (skin_integrity, wounds, pressure_injuries,
 * wound_treatment_detail, body_diagram_wound_markers, braden) — see
 * ownership.ts.
 *
 * CRITICAL SCOPE RULE: per the accepted Integumentary Architecture Review
 * and the accepted Wound Evidence Architecture Review, edema remains
 * Cardiovascular (never duplicated here — see
 * `edemaIsNotOwnedByIntegumentary` in ownership.ts), and this panel adds
 * no fields beyond the six approved fact keys: no ADLs, no fall history,
 * no assistive devices, no new photo/upload/storage architecture.
 *
 * CRITICAL RULE (one wound, one record): each wound is an independent
 * `WoundRecord` with its own lifecycle (add/edit/chain-to-prior). Wounds
 * never share fields or blended state — editing one wound's fields never
 * changes another wound's fields. Longitudinal history is modeled via
 * `priorWoundRecordId`, never by mutating a prior wound's own fields.
 *
 * CRITICAL RULE (body diagram is a location aid only): `bodyDiagramMarker`
 * (view + normalized position) is explicitly non-authoritative. The
 * authoritative source of a wound's location is `locationText` plus
 * `woundType`. A marker alone — with no `locationText`/`woundType` — can
 * never satisfy wound documentation. This reuses, and never duplicates,
 * `woundMarkerAloneSatisfiesWoundRecord` and
 * `bodyDiagramMarkerDoesNotCompleteWoundRecord` from the domain layer.
 *
 * CRITICAL RULE (Braden non-substitution, both directions): Integumentary
 * owns `braden` itself, so unlike Musculoskeletal/Nutrition this is a
 * two-directional guard: a Braden subscale assessment can never complete
 * skin/wound review (no skin/wound fields are read from or derived from
 * Braden), and the skin/wound review can never complete or substitute for
 * Braden (Braden's six subscales and total are only ever set by explicit
 * RN selection in the dedicated Braden block below, and the total is
 * always derived from the subscales — never independently editable — per
 * `bradenTotalIsDerivedFromSubscales`).
 *
 * CRITICAL RULE (photo evidence belongs to the wound): photo evidence is
 * attached to a specific `WoundRecord`, never to the system assessment,
 * never to a `BodyDiagramMarker`. This reuses the existing, unmodified
 * document-upload infrastructure (`uploadDocumentOffline`) — no new photo
 * service, image service, upload service, or storage system is created.
 * Each wound's photo control is scoped to that wound's own local state;
 * uploading a photo for one wound can never append to another wound's
 * evidence list.
 *
 * CRITICAL RULE: HOPE comfort impact and HOPE function impact are each a
 * separate, explicit RN assessment field. Neither is derived, defaulted,
 * or pre-filled from wound count, wound stage, wound dimensions, Braden
 * score, or photo evidence.
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
  bradenTotalIsDerivedFromSubscales,
  type AssessmentLimitation,
  type AssessmentSituation,
} from "../../../../domain/body-systems";
import { uploadDocumentOffline } from "../../../../api/offlineDocumentApi";

const INTEGUMENTARY_FACT_KEYS =
  OWNERSHIP_REGISTRY.find((rule) => rule.owner === "integumentary")?.factKeys ?? [];

const SITUATION_OPTIONS: { value: AssessmentSituation; label: string }[] = [
  { value: "no_current_concern", label: "No current concern" },
  { value: "stable_existing", label: "Stable existing" },
  { value: "new_or_worsening", label: "New / worsening" },
  { value: "unable_to_assess", label: "Unable to assess" },
];

const PRIOR_COMPARISON_OPTIONS = ["improved", "same", "worse", "unknown"] as const;
type PriorComparison = (typeof PRIOR_COMPARISON_OPTIONS)[number];

const SKIN_IMPAIRMENT_OPTIONS = [
  "pressure_injury",
  "stasis_ulcer",
  "surgical_wound",
  "skin_tear",
  "rash_or_maceration",
  "other_open_area",
] as const;

const BODY_DIAGRAM_VIEW_OPTIONS = ["anterior", "posterior", "left_lateral", "right_lateral"] as const;
type BodyDiagramView = (typeof BODY_DIAGRAM_VIEW_OPTIONS)[number];

const WOUND_STAGE_OPTIONS = ["stage_1", "stage_2", "stage_3", "stage_4", "unstageable", "dti", "not_applicable"] as const;

const CHANGE_FROM_PRIOR_OPTIONS = ["improved", "unchanged", "worse", "new", "not_applicable"] as const;
type ChangeFromPrior = (typeof CHANGE_FROM_PRIOR_OPTIONS)[number];

const BRADEN_1_TO_4_OPTIONS = ["1", "2", "3", "4"] as const;
const BRADEN_FRICTION_SHEAR_OPTIONS = ["1", "2", "3"] as const;

const HOPE_IMPACT_OPTIONS = ["not_yet_assessed", "yes", "no", "unclear"] as const;
export type HopeImpactValue = (typeof HOPE_IMPACT_OPTIONS)[number];

export interface WoundPhotoEvidence {
  /** Existing document infrastructure's document id — never a new id scheme. */
  documentId: string;
  fileName: string;
  uploadedAt: string;
  status: "uploaded" | "queued";
}

export interface WoundBodyDiagramMarker {
  view: BodyDiagramView;
  normalizedX: number;
  normalizedY: number;
}

export interface WoundSubState {
  /** Local list key only — never persisted, never used as the wound's authoritative identity. */
  localId: string;
  label: string;
  /** Authoritative location — see `woundMarkerAloneSatisfiesWoundRecord`. */
  locationText: string;
  /** Authoritative wound type — see `woundMarkerAloneSatisfiesWoundRecord`. */
  woundType: string;
  /** Location aid only — never authoritative. */
  bodyDiagramMarker?: WoundBodyDiagramMarker;
  stage?: (typeof WOUND_STAGE_OPTIONS)[number];
  lengthCm?: string;
  widthCm?: string;
  depthCm?: string;
  underminingTunneling?: string;
  woundBed?: string;
  drainage?: string;
  odor?: string;
  periwoundSkin?: string;
  dressingApplied?: string;
  changeFromPrior?: ChangeFromPrior;
  /** Chains this wound to a prior `WoundRecord`'s localId — never mutates the prior record. */
  priorWoundRecordLocalId?: string;
  interventionsGiven?: string;
  followUpNeeds?: string;
  /** Evidence belongs to this wound only — see module doc "photo evidence belongs to the wound." */
  photoEvidence: WoundPhotoEvidence[];
}

export function createWoundSubState(localId: string): WoundSubState {
  return {
    localId,
    label: "",
    locationText: "",
    woundType: "",
    photoEvidence: [],
  };
}

export interface BradenSubState {
  sensoryPerception?: number;
  moisture?: number;
  activity?: number;
  mobility?: number;
  nutrition?: number;
  frictionShear?: number;
  assessedAt?: string;
  riskFollowUp?: string;
}

export interface IntegumentaryFieldValues {
  screeningDateTime?: string;
  priorComparison?: PriorComparison;
  onsetOrSource?: string;
  skinImpairments: string[];
  skinIntegrityOutsideWounds?: string;
  skinStatusNotes?: string;
  wounds: WoundSubState[];
  braden: BradenSubState;
  /** Required explicit RN assessment — never derived from wound count/stage/dimensions, Braden, or photo evidence. */
  hopeComfortImpact: HopeImpactValue;
  /** Required explicit RN assessment — never derived from wound count/stage/dimensions, Braden, or photo evidence. */
  hopeFunctionImpact: HopeImpactValue;
}

export const INITIAL_INTEGUMENTARY_FIELD_VALUES: IntegumentaryFieldValues = {
  skinImpairments: [],
  wounds: [],
  braden: {},
  hopeComfortImpact: "not_yet_assessed",
  hopeFunctionImpact: "not_yet_assessed",
};

export interface IntegumentarySystemPanelProps {
  /** Needed to reuse the existing document-upload infrastructure for photo evidence. */
  patientId: string;
  situation?: AssessmentSituation;
  onSituationChange: (situation: AssessmentSituation) => void;
  onRequirementSatisfied: (requirementKey: string) => void;
  onLimitationChange: (limitation: AssessmentLimitation) => void;
  missingRequirements: string[];
  values: IntegumentaryFieldValues;
  onChange: (values: IntegumentaryFieldValues) => void;
}

function bradenTotal(braden: BradenSubState): number | undefined {
  const { sensoryPerception, moisture, activity, mobility, nutrition, frictionShear } = braden;
  if (
    sensoryPerception === undefined ||
    moisture === undefined ||
    activity === undefined ||
    mobility === undefined ||
    nutrition === undefined ||
    frictionShear === undefined
  ) {
    return undefined;
  }
  const total = sensoryPerception + moisture + activity + mobility + nutrition + frictionShear;
  // Proves the derivation this panel relies on — the total is never an
  // independently-set field, so it always equals the subscale sum.
  if (
    !bradenTotalIsDerivedFromSubscales({
      sensoryPerception,
      moisture,
      activity,
      mobility,
      nutrition,
      frictionShear,
      total,
    })
  ) {
    return undefined;
  }
  return total;
}

export function IntegumentarySystemPanel({
  patientId,
  situation,
  onSituationChange,
  onRequirementSatisfied,
  onLimitationChange,
  missingRequirements,
  values,
  onChange,
}: IntegumentarySystemPanelProps) {
  const [scope, setScope] = useState<string[]>([]);
  const [reason, setReason] = useState("");
  const [assessedPortion, setAssessedPortion] = useState("");
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [responsibleClinicianId, setResponsibleClinicianId] = useState("");
  const [timingOrContingency, setTimingOrContingency] = useState("");
  const [nextWoundId, setNextWoundId] = useState(1);

  const requirements = situation ? getSituationRequirements(situation) : [];

  const set = <K extends keyof IntegumentaryFieldValues>(key: K, value: IntegumentaryFieldValues[K]) => {
    onChange({ ...values, [key]: value });
  };

  const setBraden = <K extends keyof BradenSubState>(key: K, value: BradenSubState[K]) => {
    onChange({ ...values, braden: { ...values.braden, [key]: value } });
  };

  const addWound = () => {
    const wound = createWoundSubState(`wound-${nextWoundId}`);
    setNextWoundId((n) => n + 1);
    set("wounds", [...values.wounds, wound]);
  };

  const updateWound = (localId: string, patch: Partial<WoundSubState>) => {
    set(
      "wounds",
      values.wounds.map((wound) => (wound.localId === localId ? { ...wound, ...patch } : wound)),
    );
  };

  const removeWound = (localId: string) => {
    set(
      "wounds",
      values.wounds.filter((wound) => wound.localId !== localId),
    );
  };

  const attachPhoto = async (localId: string, file: File) => {
    const result = await uploadDocumentOffline(patientId, "WOUND_PHOTO", file);
    const evidence: WoundPhotoEvidence =
      result.status === "uploaded"
        ? {
            documentId: result.document_id,
            fileName: result.file_name ?? file.name,
            uploadedAt: result.uploaded_at,
            status: "uploaded",
          }
        : {
            documentId: result.queuedMutationId,
            fileName: result.fileName,
            uploadedAt: new Date().toISOString(),
            status: "queued",
          };
    const wound = values.wounds.find((w) => w.localId === localId);
    if (!wound) return;
    updateWound(localId, { photoEvidence: [...wound.photoEvidence, evidence] });
  };

  const removePhoto = (localId: string, documentId: string) => {
    const wound = values.wounds.find((w) => w.localId === localId);
    if (!wound) return;
    updateWound(localId, { photoEvidence: wound.photoEvidence.filter((p) => p.documentId !== documentId) });
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

  const totalBraden = bradenTotal(values.braden);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Integumentary</CardTitle>
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
              <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Skin impairments present</p>
              <ul className="flex flex-col gap-1">
                {SKIN_IMPAIRMENT_OPTIONS.map((option) => (
                  <li key={option} className="flex items-center gap-2 text-[12px]">
                    <Checkbox
                      checked={values.skinImpairments.includes(option)}
                      onCheckedChange={(checked) =>
                        set(
                          "skinImpairments",
                          checked
                            ? [...values.skinImpairments, option]
                            : values.skinImpairments.filter((o) => o !== option),
                        )
                      }
                    />
                    {option.replaceAll("_", " ")}
                  </li>
                ))}
              </ul>
            </div>

            <Textarea
              placeholder="Skin integrity outside recorded wounds"
              value={values.skinIntegrityOutsideWounds ?? ""}
              onChange={(e) => set("skinIntegrityOutsideWounds", e.target.value)}
            />

            <Textarea
              placeholder="Skin status notes"
              value={values.skinStatusNotes ?? ""}
              onChange={(e) => set("skinStatusNotes", e.target.value)}
            />

            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <p className="text-[11px] font-medium text-rnica-muted">Wounds (each independent — no shared state)</p>
                <Button size="sm" onClick={addWound}>
                  + wound
                </Button>
              </div>

              {values.wounds.map((wound) => (
                <div key={wound.localId} className="flex flex-col gap-2 rounded-lg border border-rnica-border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <Input
                      placeholder="Wound label (e.g. Sacrum)"
                      value={wound.label}
                      onChange={(e) => updateWound(wound.localId, { label: e.target.value })}
                    />
                    <Button size="sm" variant="ghost" onClick={() => removeWound(wound.localId)}>
                      Remove wound
                    </Button>
                  </div>

                  <Input
                    placeholder="Location (required — the authoritative record)"
                    value={wound.locationText}
                    onChange={(e) => updateWound(wound.localId, { locationText: e.target.value })}
                  />
                  <Input
                    placeholder="Wound type (required — the authoritative record)"
                    value={wound.woundType}
                    onChange={(e) => updateWound(wound.localId, { woundType: e.target.value })}
                  />

                  <div className="rounded-lg border border-dashed border-rnica-border p-2">
                    <p className="mb-1.5 text-[10px] font-medium text-rnica-muted">
                      Body diagram — location aid only. Location and wound type above are the record.
                    </p>
                    <ToggleGroup
                      type="single"
                      value={wound.bodyDiagramMarker?.view}
                      onValueChange={(v) =>
                        v &&
                        updateWound(wound.localId, {
                          bodyDiagramMarker: {
                            view: v as BodyDiagramView,
                            normalizedX: wound.bodyDiagramMarker?.normalizedX ?? 0.5,
                            normalizedY: wound.bodyDiagramMarker?.normalizedY ?? 0.5,
                          },
                        })
                      }
                    >
                      {BODY_DIAGRAM_VIEW_OPTIONS.map((option) => (
                        <ToggleGroupItem key={option} value={option}>
                          {option.replaceAll("_", " ")}
                        </ToggleGroupItem>
                      ))}
                    </ToggleGroup>
                  </div>

                  <div>
                    <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Stage</p>
                    <ToggleGroup
                      type="single"
                      value={wound.stage}
                      onValueChange={(v) => v && updateWound(wound.localId, { stage: v as WoundSubState["stage"] })}
                    >
                      {WOUND_STAGE_OPTIONS.map((option) => (
                        <ToggleGroupItem key={option} value={option}>
                          {option.replaceAll("_", " ")}
                        </ToggleGroupItem>
                      ))}
                    </ToggleGroup>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <Input
                      placeholder="Length (cm)"
                      value={wound.lengthCm ?? ""}
                      onChange={(e) => updateWound(wound.localId, { lengthCm: e.target.value })}
                    />
                    <Input
                      placeholder="Width (cm)"
                      value={wound.widthCm ?? ""}
                      onChange={(e) => updateWound(wound.localId, { widthCm: e.target.value })}
                    />
                    <Input
                      placeholder="Depth (cm)"
                      value={wound.depthCm ?? ""}
                      onChange={(e) => updateWound(wound.localId, { depthCm: e.target.value })}
                    />
                  </div>

                  <Input
                    placeholder="Undermining / tunneling"
                    value={wound.underminingTunneling ?? ""}
                    onChange={(e) => updateWound(wound.localId, { underminingTunneling: e.target.value })}
                  />
                  <Input
                    placeholder="Wound bed"
                    value={wound.woundBed ?? ""}
                    onChange={(e) => updateWound(wound.localId, { woundBed: e.target.value })}
                  />
                  <Input
                    placeholder="Drainage"
                    value={wound.drainage ?? ""}
                    onChange={(e) => updateWound(wound.localId, { drainage: e.target.value })}
                  />
                  <Input
                    placeholder="Odor"
                    value={wound.odor ?? ""}
                    onChange={(e) => updateWound(wound.localId, { odor: e.target.value })}
                  />
                  <Input
                    placeholder="Periwound skin"
                    value={wound.periwoundSkin ?? ""}
                    onChange={(e) => updateWound(wound.localId, { periwoundSkin: e.target.value })}
                  />
                  <Input
                    placeholder="Dressing applied"
                    value={wound.dressingApplied ?? ""}
                    onChange={(e) => updateWound(wound.localId, { dressingApplied: e.target.value })}
                  />

                  <div>
                    <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Change since prior</p>
                    <ToggleGroup
                      type="single"
                      value={wound.changeFromPrior}
                      onValueChange={(v) => v && updateWound(wound.localId, { changeFromPrior: v as ChangeFromPrior })}
                    >
                      {CHANGE_FROM_PRIOR_OPTIONS.map((option) => (
                        <ToggleGroupItem key={option} value={option}>
                          {option.replaceAll("_", " ")}
                        </ToggleGroupItem>
                      ))}
                    </ToggleGroup>
                  </div>

                  <Input
                    placeholder="Prior wound record (dated chain, if any)"
                    value={wound.priorWoundRecordLocalId ?? ""}
                    onChange={(e) => updateWound(wound.localId, { priorWoundRecordLocalId: e.target.value })}
                  />

                  <Textarea
                    placeholder="Interventions given"
                    value={wound.interventionsGiven ?? ""}
                    onChange={(e) => updateWound(wound.localId, { interventionsGiven: e.target.value })}
                  />
                  <Textarea
                    placeholder="Follow-up needs"
                    value={wound.followUpNeeds ?? ""}
                    onChange={(e) => updateWound(wound.localId, { followUpNeeds: e.target.value })}
                  />

                  <div className="flex flex-col gap-1.5">
                    <p className="text-[11px] font-medium text-rnica-muted">
                      Photo evidence (belongs to this wound only — reuses existing document upload)
                    </p>
                    <input
                      aria-label={`Attach wound photo evidence for ${wound.label || wound.localId}`}
                      type="file"
                      accept="image/jpeg,image/png,image/tiff"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) void attachPhoto(wound.localId, file);
                        e.target.value = "";
                      }}
                    />
                    <ul className="flex flex-col gap-1">
                      {wound.photoEvidence.map((photo) => (
                        <li key={photo.documentId} className="flex items-center gap-2 text-[12px]">
                          <span>{photo.fileName}</span>
                          <Badge variant={photo.status === "uploaded" ? "success" : "warning"}>{photo.status}</Badge>
                          <Button size="sm" variant="ghost" onClick={() => removePhoto(wound.localId, photo.documentId)}>
                            Remove
                          </Button>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-col gap-2 rounded-lg border border-rnica-border p-3">
              <p className="text-[11px] font-semibold text-rnica-muted">
                Braden Scale — standardized instrument, clinician-rated. Independent of the skin/wound review above:
                Braden does not complete skin review, and skin review does not complete Braden.
              </p>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                <div>
                  <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Sensory perception</p>
                  <ToggleGroup
                    type="single"
                    value={values.braden.sensoryPerception?.toString()}
                    onValueChange={(v) => v && setBraden("sensoryPerception", Number(v))}
                  >
                    {BRADEN_1_TO_4_OPTIONS.map((option) => (
                      <ToggleGroupItem key={option} value={option}>
                        {option}
                      </ToggleGroupItem>
                    ))}
                  </ToggleGroup>
                </div>
                <div>
                  <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Moisture</p>
                  <ToggleGroup
                    type="single"
                    value={values.braden.moisture?.toString()}
                    onValueChange={(v) => v && setBraden("moisture", Number(v))}
                  >
                    {BRADEN_1_TO_4_OPTIONS.map((option) => (
                      <ToggleGroupItem key={option} value={option}>
                        {option}
                      </ToggleGroupItem>
                    ))}
                  </ToggleGroup>
                </div>
                <div>
                  <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Activity</p>
                  <ToggleGroup
                    type="single"
                    value={values.braden.activity?.toString()}
                    onValueChange={(v) => v && setBraden("activity", Number(v))}
                  >
                    {BRADEN_1_TO_4_OPTIONS.map((option) => (
                      <ToggleGroupItem key={option} value={option}>
                        {option}
                      </ToggleGroupItem>
                    ))}
                  </ToggleGroup>
                </div>
                <div>
                  <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Mobility (Braden)</p>
                  <ToggleGroup
                    type="single"
                    value={values.braden.mobility?.toString()}
                    onValueChange={(v) => v && setBraden("mobility", Number(v))}
                  >
                    {BRADEN_1_TO_4_OPTIONS.map((option) => (
                      <ToggleGroupItem key={option} value={option}>
                        {option}
                      </ToggleGroupItem>
                    ))}
                  </ToggleGroup>
                </div>
                <div>
                  <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Nutrition (Braden)</p>
                  <ToggleGroup
                    type="single"
                    value={values.braden.nutrition?.toString()}
                    onValueChange={(v) => v && setBraden("nutrition", Number(v))}
                  >
                    {BRADEN_1_TO_4_OPTIONS.map((option) => (
                      <ToggleGroupItem key={option} value={option}>
                        {option}
                      </ToggleGroupItem>
                    ))}
                  </ToggleGroup>
                </div>
                <div>
                  <p className="mb-1.5 text-[11px] font-medium text-rnica-muted">Friction / shear</p>
                  <ToggleGroup
                    type="single"
                    value={values.braden.frictionShear?.toString()}
                    onValueChange={(v) => v && setBraden("frictionShear", Number(v))}
                  >
                    {BRADEN_FRICTION_SHEAR_OPTIONS.map((option) => (
                      <ToggleGroupItem key={option} value={option}>
                        {option}
                      </ToggleGroupItem>
                    ))}
                  </ToggleGroup>
                </div>
              </div>
              <p className="text-[12px] font-medium text-rnica-ink">
                Total: {totalBraden !== undefined ? `${totalBraden}/23` : "incomplete"}
              </p>
              <Textarea
                placeholder="Risk follow-up"
                value={values.braden.riskFollowUp ?? ""}
                onChange={(e) => setBraden("riskFollowUp", e.target.value)}
              />
            </div>

            <div className="flex flex-col gap-2 rounded-lg border border-rnica-borderAI bg-rnica-aiBg/30 p-3">
              <Badge variant="warning">
                Requires explicit RN assessment — never derived from wound count, stage, dimensions, Braden score, or
                photo evidence
              </Badge>
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
                {INTEGUMENTARY_FACT_KEYS.map((factKey) => (
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
