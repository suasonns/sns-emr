/**
 * SNS Body Systems Workspace — BodyShieldShell.
 *
 * Top-level orchestrator. Owns visit-mode switching, system navigation,
 * fixed registry visibility, review/exception/progress counts, draft
 * status, and desktop/mobile layout selection. Contains no clinical
 * business logic of its own — situation rules, requirement rules, and
 * exception rules all come from `src/domain/body-systems`; system-specific
 * fields come from the pilot panels (Neurological, Respiratory,
 * Cardiovascular, Gastrointestinal, Genitourinary, Nutrition,
 * Musculoskeletal, Integumentary) or a Phase 2 placeholder for the
 * remaining systems.
 */
import * as React from "react";
import { useEffect, useRef, useState } from "react";
import { Badge } from "../../../components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "../../../components/ui/tabs";
import { Button } from "../../../components/ui/button";
import { Card, CardContent } from "../../../components/ui/card";
import { useViewportKind } from "./useViewportKind";
import { ResponsiveDesktopLayout } from "./ResponsiveDesktopLayout";
import { ResponsiveMobileLayout } from "./ResponsiveMobileLayout";
import { SystemRegisterRow } from "../workspace/SystemRegisterRow";
import { BodySystemsWorkspace } from "../workspace/BodySystemsWorkspace";
import { ReviewExceptionDrawer } from "../workspace/ReviewExceptionDrawer";
import { AISuggestionShell } from "../ai/AISuggestionShell";
import { NeurologicalSystemPanel } from "../systems/neurological/NeurologicalSystemPanel";
import {
  INITIAL_RESPIRATORY_FIELD_VALUES,
  RespiratorySystemPanel,
  type RespiratoryFieldValues,
} from "../systems/respiratory/RespiratorySystemPanel";
import {
  CardiovascularSystemPanel,
  INITIAL_CARDIOVASCULAR_FIELD_VALUES,
  type CardiovascularFieldValues,
} from "../systems/cardiovascular/CardiovascularSystemPanel";
import {
  GastrointestinalSystemPanel,
  INITIAL_GASTROINTESTINAL_FIELD_VALUES,
  type GastrointestinalFieldValues,
} from "../systems/gastrointestinal/GastrointestinalSystemPanel";
import {
  GenitourinarySystemPanel,
  INITIAL_GENITOURINARY_FIELD_VALUES,
  type GenitourinaryFieldValues,
} from "../systems/genitourinary/GenitourinarySystemPanel";
import {
  NutritionSystemPanel,
  INITIAL_NUTRITION_FIELD_VALUES,
  type NutritionFieldValues,
} from "../systems/nutrition/NutritionSystemPanel";
import {
  MusculoskeletalSystemPanel,
  INITIAL_MUSCULOSKELETAL_FIELD_VALUES,
  type MusculoskeletalFieldValues,
} from "../systems/musculoskeletal/MusculoskeletalSystemPanel";
import {
  IntegumentarySystemPanel,
  INITIAL_INTEGUMENTARY_FIELD_VALUES,
  type IntegumentaryFieldValues,
} from "../systems/integumentary/IntegumentarySystemPanel";
import {
  InfectionSystemPanel,
  INITIAL_INFECTION_FIELD_VALUES,
  type InfectionFieldValues,
} from "../systems/infection/InfectionSystemPanel";
import { useBodySystemsAssessmentState } from "../state/useBodySystemsAssessmentState";
import { useRespiratoryPersistence, type RespiratoryPersistenceStatus } from "../systems/respiratory/useRespiratoryPersistence";
import {
  getVisitModeConfig,
  type AssessmentSituation,
  type BodySystemCode,
  type VisitMode,
} from "../../../domain/body-systems";

const VISIT_MODE_TABS: { value: VisitMode; label: string }[] = [
  { value: "admission_comprehensive", label: "Admission / Comprehensive" },
  { value: "routine_rn", label: "Routine RN Visit" },
  { value: "recertification", label: "Recertification" },
];

const PILOT_SYSTEMS: readonly BodySystemCode[] = [
  "neurological",
  "respiratory",
  "cardiovascular",
  "nutrition",
  "gastrointestinal",
  "genitourinary",
  "musculoskeletal",
  "integumentary",
  "infection_immunological",
];

export interface BodyShieldShellProps {
  patientId: string;
  visitId: string;
  bodySystemsAssessmentId: string;
  initialVisitMode?: VisitMode;
  onVisitModeChange?: (mode: VisitMode) => void;
}

export function BodyShieldShell({
  patientId,
  visitId,
  bodySystemsAssessmentId,
  initialVisitMode = "routine_rn",
  onVisitModeChange,
}: BodyShieldShellProps) {
  const viewportKind = useViewportKind();
  const [visitMode, setVisitMode] = useState<VisitMode>(initialVisitMode);
  const [exceptionDrawerOpen, setExceptionDrawerOpen] = useState(false);
  const [respiratoryValues, setRespiratoryValues] = useState<RespiratoryFieldValues>(
    INITIAL_RESPIRATORY_FIELD_VALUES,
  );
  const [cardiovascularValues, setCardiovascularValues] = useState<CardiovascularFieldValues>(
    INITIAL_CARDIOVASCULAR_FIELD_VALUES,
  );
  const [gastrointestinalValues, setGastrointestinalValues] = useState<GastrointestinalFieldValues>(
    INITIAL_GASTROINTESTINAL_FIELD_VALUES,
  );
  const [genitourinaryValues, setGenitourinaryValues] = useState<GenitourinaryFieldValues>(
    INITIAL_GENITOURINARY_FIELD_VALUES,
  );
  const [nutritionValues, setNutritionValues] = useState<NutritionFieldValues>(
    INITIAL_NUTRITION_FIELD_VALUES,
  );
  const [musculoskeletalValues, setMusculoskeletalValues] = useState<MusculoskeletalFieldValues>(
    INITIAL_MUSCULOSKELETAL_FIELD_VALUES,
  );
  const [integumentaryValues, setIntegumentaryValues] = useState<IntegumentaryFieldValues>(
    INITIAL_INTEGUMENTARY_FIELD_VALUES,
  );
  const [infectionValues, setInfectionValues] = useState<InfectionFieldValues>(
    INITIAL_INFECTION_FIELD_VALUES,
  );

  const state = useBodySystemsAssessmentState(bodySystemsAssessmentId);
  const visitModeConfig = getVisitModeConfig(visitMode);
  const openExceptionCount = state.exceptions.filter((exception) => exception.status === "open").length;

  // Respiratory persistence (Workspace integration). The other eight pilot
  // systems remain in-memory-only (Phase 1 scope); this is additive and
  // scoped to Respiratory only, per the approved persistence-proof plan.
  const respiratoryPersistence = useRespiratoryPersistence(patientId);
  const respiratoryLoadedIntoStateRef = useRef<string | null>(null);

  useEffect(() => {
    const loaded = respiratoryPersistence.assessment;
    if (!loaded) return;
    if (respiratoryPersistence.status !== "draft_loaded" && respiratoryPersistence.status !== "no_draft_yet") return;
    // Seed orchestration state + local field values from the server exactly
    // once per load (identified by id+version) -- never on every render,
    // and never overwriting local edits made after the load completed.
    const loadKey = `${loaded.id}:${loaded.version}`;
    if (respiratoryLoadedIntoStateRef.current === loadKey) return;
    respiratoryLoadedIntoStateRef.current = loadKey;

    if (loaded.situation) {
      state.setSituation("respiratory", loaded.situation as AssessmentSituation);
    }
    if (
      loaded.limitationReason ||
      (loaded.limitationScope && loaded.limitationScope.length > 0) ||
      loaded.limitationResponsibleClinicianId ||
      loaded.limitationTimingOrContingency
    ) {
      state.setLimitation("respiratory", {
        scope: loaded.limitationScope ?? [],
        reason: loaded.limitationReason ?? "",
        assessedPortion: loaded.limitationAssessedPortion ?? undefined,
        followUpRequired: loaded.limitationFollowUpRequired ?? false,
        responsibleClinicianId: loaded.limitationResponsibleClinicianId ?? undefined,
        timingOrContingency: loaded.limitationTimingOrContingency ?? undefined,
      });
    }
    setRespiratoryValues((prev) => ({ ...prev, ...(loaded.data as Partial<RespiratoryFieldValues>) }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [respiratoryPersistence.assessment, respiratoryPersistence.status]);

  const handleSaveRespiratoryDraft = () => {
    const respiratoryState = state.systems.respiratory;
    respiratoryPersistence
      .save({
        situation: respiratoryState.situation ?? null,
        data: respiratoryValues as unknown as Record<string, unknown>,
        reviewState: respiratoryState.reviewState,
        limitationScope: respiratoryState.limitation?.scope ?? null,
        limitationReason: respiratoryState.limitation?.reason ?? null,
        limitationAssessedPortion: respiratoryState.limitation?.assessedPortion ?? null,
        limitationFollowUpRequired: respiratoryState.limitation?.followUpRequired ?? null,
        limitationResponsibleClinicianId: respiratoryState.limitation?.responsibleClinicianId ?? null,
        limitationTimingOrContingency: respiratoryState.limitation?.timingOrContingency ?? null,
      })
      .catch(() => {
        // Status/errorMessage already reflect the failure; nothing further
        // to do here. Swallowed so a rejected promise doesn't surface as an
        // unhandled rejection -- the UI reads respiratoryPersistence.status.
      });
  };

  const handleVisitModeChange = (mode: VisitMode) => {
    setVisitMode(mode);
    onVisitModeChange?.(mode);
  };

  const selectedSystemState = state.systems[state.selectedSystem];

  const registry = (
    <>
      {state.registryOrder.map((system) => (
        <SystemRegisterRow
          key={system}
          system={system}
          reviewState={state.systems[system].reviewState}
          exceptionCount={
            state.exceptions.filter((exception) => exception.system === system && exception.status === "open").length
          }
          isSelected={system === state.selectedSystem}
          isPilotImplemented={PILOT_SYSTEMS.includes(system)}
          onSelect={state.selectSystem}
          layout={viewportKind === "mobile" ? "strip" : "rail"}
        />
      ))}
    </>
  );

  const header = (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-3">
      <div className="flex min-w-0 flex-wrap items-center gap-3">
        <h1 className="text-[14px] font-semibold text-rnica-textStrong">Body Systems</h1>
        <Badge variant="neutral">Draft</Badge>
        <span className="text-[11px] text-rnica-muted">{visitModeConfig.goal}</span>
      </div>

      <div className="flex min-w-0 flex-wrap items-center gap-3">
        <div className="w-full min-w-0 overflow-x-auto sm:w-auto">
          <Tabs value={visitMode} onValueChange={(value) => handleVisitModeChange(value as VisitMode)}>
            <TabsList>
              {VISIT_MODE_TABS.map((tab) => (
                <TabsTrigger key={tab.value} value={tab.value}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-rnica-muted">
          <Badge variant="success">{state.counts.reviewed} reviewed</Badge>
          <Badge variant="warning">{state.counts.reviewedWithException} with exception</Badge>
          <Badge variant="teal">{state.counts.inProgress} in progress</Badge>
          <Badge variant="neutral">{state.counts.notReviewed} not reviewed</Badge>
        </div>

        <Button size="sm" variant="outline" onClick={() => setExceptionDrawerOpen(true)}>
          Exceptions ({openExceptionCount})
        </Button>
      </div>
    </div>
  );

  const content = (
    <div className="flex flex-col gap-4">
      <BodySystemsWorkspace
        system={state.selectedSystem}
        reviewState={selectedSystemState.reviewState}
        currentEvidence={selectedSystemState.currentEvidence}
        historicalEvidence={selectedSystemState.historicalEvidence}
        exceptions={state.exceptions}
        onStartReview={() => state.startReview(state.selectedSystem)}
        onCompleteReview={() => state.completeReview(state.selectedSystem)}
      >
        {state.selectedSystem === "neurological" && (
          <NeurologicalSystemPanel
            situation={selectedSystemState.situation}
            onSituationChange={(situation) => state.setSituation("neurological", situation)}
            onRequirementSatisfied={(key) => state.markRequirementSatisfied("neurological", key)}
            onLimitationChange={(limitation) => state.setLimitation("neurological", limitation)}
            missingRequirements={state.missingRequirementsFor("neurological")}
          />
        )}

        {state.selectedSystem === "respiratory" && (
          <div className="flex flex-col gap-2">
            <RespiratorySystemPanel
              situation={selectedSystemState.situation}
              onSituationChange={(situation) => {
                state.setSituation("respiratory", situation);
                respiratoryPersistence.markDirty();
              }}
              onRequirementSatisfied={(key) => state.markRequirementSatisfied("respiratory", key)}
              onLimitationChange={(limitation) => {
                state.setLimitation("respiratory", limitation);
                respiratoryPersistence.markDirty();
              }}
              missingRequirements={state.missingRequirementsFor("respiratory")}
              values={respiratoryValues}
              onChange={(values) => {
                setRespiratoryValues(values);
                respiratoryPersistence.markDirty();
              }}
            />
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={handleSaveRespiratoryDraft}
                disabled={respiratoryPersistence.status === "saving" || respiratoryPersistence.status === "loading"}
              >
                Save Respiratory draft
              </Button>
              <RespiratoryPersistenceStatusBadge
                status={respiratoryPersistence.status}
                errorMessage={respiratoryPersistence.errorMessage}
                onRetry={respiratoryPersistence.reload}
              />
            </div>
          </div>
        )}

        {state.selectedSystem === "cardiovascular" && (
          <CardiovascularSystemPanel
            situation={selectedSystemState.situation}
            onSituationChange={(situation) => state.setSituation("cardiovascular", situation)}
            onRequirementSatisfied={(key) => state.markRequirementSatisfied("cardiovascular", key)}
            onLimitationChange={(limitation) => state.setLimitation("cardiovascular", limitation)}
            missingRequirements={state.missingRequirementsFor("cardiovascular")}
            values={cardiovascularValues}
            onChange={setCardiovascularValues}
          />
        )}

        {state.selectedSystem === "gastrointestinal" && (
          <GastrointestinalSystemPanel
            situation={selectedSystemState.situation}
            onSituationChange={(situation) => state.setSituation("gastrointestinal", situation)}
            onRequirementSatisfied={(key) => state.markRequirementSatisfied("gastrointestinal", key)}
            onLimitationChange={(limitation) => state.setLimitation("gastrointestinal", limitation)}
            missingRequirements={state.missingRequirementsFor("gastrointestinal")}
            values={gastrointestinalValues}
            onChange={setGastrointestinalValues}
          />
        )}

        {state.selectedSystem === "genitourinary" && (
          <GenitourinarySystemPanel
            situation={selectedSystemState.situation}
            onSituationChange={(situation) => state.setSituation("genitourinary", situation)}
            onRequirementSatisfied={(key) => state.markRequirementSatisfied("genitourinary", key)}
            onLimitationChange={(limitation) => state.setLimitation("genitourinary", limitation)}
            missingRequirements={state.missingRequirementsFor("genitourinary")}
            values={genitourinaryValues}
            onChange={setGenitourinaryValues}
          />
        )}

        {state.selectedSystem === "nutrition" && (
          <NutritionSystemPanel
            situation={selectedSystemState.situation}
            onSituationChange={(situation) => state.setSituation("nutrition", situation)}
            onRequirementSatisfied={(key) => state.markRequirementSatisfied("nutrition", key)}
            onLimitationChange={(limitation) => state.setLimitation("nutrition", limitation)}
            missingRequirements={state.missingRequirementsFor("nutrition")}
            values={nutritionValues}
            onChange={setNutritionValues}
          />
        )}

        {state.selectedSystem === "musculoskeletal" && (
          <MusculoskeletalSystemPanel
            situation={selectedSystemState.situation}
            onSituationChange={(situation) => state.setSituation("musculoskeletal", situation)}
            onRequirementSatisfied={(key) => state.markRequirementSatisfied("musculoskeletal", key)}
            onLimitationChange={(limitation) => state.setLimitation("musculoskeletal", limitation)}
            missingRequirements={state.missingRequirementsFor("musculoskeletal")}
            values={musculoskeletalValues}
            onChange={setMusculoskeletalValues}
          />
        )}

        {state.selectedSystem === "integumentary" && (
          <IntegumentarySystemPanel
            patientId={patientId}
            situation={selectedSystemState.situation}
            onSituationChange={(situation) => state.setSituation("integumentary", situation)}
            onRequirementSatisfied={(key) => state.markRequirementSatisfied("integumentary", key)}
            onLimitationChange={(limitation) => state.setLimitation("integumentary", limitation)}
            missingRequirements={state.missingRequirementsFor("integumentary")}
            values={integumentaryValues}
            onChange={setIntegumentaryValues}
          />
        )}

        {state.selectedSystem === "infection_immunological" && (
          <InfectionSystemPanel
            situation={selectedSystemState.situation}
            onSituationChange={(situation) => state.setSituation("infection_immunological", situation)}
            onRequirementSatisfied={(key) => state.markRequirementSatisfied("infection_immunological", key)}
            onLimitationChange={(limitation) => state.setLimitation("infection_immunological", limitation)}
            missingRequirements={state.missingRequirementsFor("infection_immunological")}
            values={infectionValues}
            onChange={setInfectionValues}
            crossSystemContext={{
              woundSummary:
                integumentaryValues.wounds.length > 0
                  ? integumentaryValues.wounds
                      .map((wound) => `${wound.woundType || "Wound"} — ${wound.locationText || "location pending"}`)
                      .join("; ")
                  : undefined,
              urinarySummary: genitourinaryValues.urinarySymptomSeverity
                ? `Urinary symptom severity: ${genitourinaryValues.urinarySymptomSeverity}`
                : undefined,
              respiratorySummary: respiratoryValues.sobSeverity
                ? `SOB severity: ${respiratoryValues.sobSeverity}`
                : undefined,
            }}
          />
        )}

        {!PILOT_SYSTEMS.includes(state.selectedSystem) && (
          <Card>
            <CardContent className="py-6 text-center text-[12px] text-rnica-muted">
              {`${state.selectedSystem.replaceAll("_", " ")} fields are Phase 2 scope. The system is registered, ` +
                "always visible, and participates in review/exception tracking today; its clinical field set ships " +
                "in a later phase."}
            </CardContent>
          </Card>
        )}
      </BodySystemsWorkspace>

      <AISuggestionShell suggestions={[]} />
    </div>
  );

  return (
    <div className="h-full w-full" data-patient-id={patientId} data-visit-id={visitId}>
      {viewportKind === "mobile" ? (
        <ResponsiveMobileLayout registry={registry} header={header} content={content} />
      ) : (
        <ResponsiveDesktopLayout registry={registry} header={header} content={content} />
      )}

      <ReviewExceptionDrawer
        open={exceptionDrawerOpen}
        onOpenChange={setExceptionDrawerOpen}
        exceptions={state.exceptions}
        onNavigateToSystem={(system) => {
          state.selectSystem(system);
          setExceptionDrawerOpen(false);
        }}
        onOpenCorrection={(system) => {
          state.openCorrection(system);
          state.selectSystem(system);
          setExceptionDrawerOpen(false);
        }}
      />
    </div>
  );
}

const RESPIRATORY_PERSISTENCE_STATUS_LABELS: Record<RespiratoryPersistenceStatus, string> = {
  loading: "Loading…",
  no_draft_yet: "No draft yet",
  draft_loaded: "Draft loaded",
  unsaved: "Unsaved changes",
  saving: "Saving…",
  saved: "Saved",
  stale_conflict: "Someone else saved this — reload to see their changes before saving again",
  validation_error: "Could not save: invalid data",
  auth_error: "Not authorized to save this assessment",
  network_error: "Could not reach the server",
};

function respiratoryStatusBadgeVariant(
  status: RespiratoryPersistenceStatus,
): "success" | "warning" | "neutral" | "teal" {
  switch (status) {
    case "saved":
    case "draft_loaded":
      return "success";
    case "unsaved":
    case "saving":
      return "teal";
    case "stale_conflict":
    case "validation_error":
    case "auth_error":
    case "network_error":
      return "warning";
    default:
      return "neutral";
  }
}

function RespiratoryPersistenceStatusBadge({
  status,
  errorMessage,
  onRetry,
}: {
  status: RespiratoryPersistenceStatus;
  errorMessage: string | null;
  onRetry: () => void;
}) {
  const isError =
    status === "stale_conflict" || status === "validation_error" || status === "auth_error" || status === "network_error";
  return (
    <div className="flex items-center gap-2">
      <Badge variant={respiratoryStatusBadgeVariant(status)}>
        {errorMessage ?? RESPIRATORY_PERSISTENCE_STATUS_LABELS[status]}
      </Badge>
      {isError && (
        <Button size="sm" variant="outline" onClick={onRetry}>
          Reload
        </Button>
      )}
    </div>
  );
}
