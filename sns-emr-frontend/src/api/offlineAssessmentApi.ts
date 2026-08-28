// Offline-aware wrapper around the RN ICA save/update calls.
//
// The real network call is always attempted first. It is only queued for
// later replay when the failure looks like a *connectivity* problem (no
// response ever came back -- offline, DNS failure, timeout) rather than a
// real server-side rejection (validation error, 401, 409 "already
// locked", etc.), which must still surface to the RN immediately so they
// can fix it rather than have it silently queued and fail again later.
//
// Local ("offline-") ids: when a brand-new assessment is *created* while
// offline, there is no server-assigned assessmentId yet. Callers get back
// a local placeholder id of the form "offline-<mutationId>" so the RN can
// keep documenting immediately. Further edits made before that create ever
// syncs are folded into the SAME queued create mutation (its formData is
// amended in place) rather than queued as a separate update against a
// server id that doesn't exist yet -- this is what prevents a queued
// update from ever being replayed as a PUT to a nonexistent assessment.
// Once the create syncs, the assessment exists under its real server id;
// the RN's next chart open/refresh reads it there.

import { saveRnicaAssessment, updateRnicaAssessment } from "./icaAssessments";
import {
  enqueueMutation,
  updateMutation,
  getMutation,
  generateClientId,
  type QueuedMutation,
} from "../offline/db";
import { triggerSync } from "../offline/syncManager";
import { isConnectivityFailure } from "../offline/connectivity";

type SaveArgs = Parameters<typeof saveRnicaAssessment>[0];

const OFFLINE_ID_PREFIX = "offline-";

export function isOfflineDraftId(id: string | null | undefined): boolean {
  return typeof id === "string" && id.startsWith(OFFLINE_ID_PREFIX);
}

function draftMutationId(offlineId: string): string {
  return offlineId.slice(OFFLINE_ID_PREFIX.length);
}

export type OfflineSaveResult = {
  assessmentId: string;
  status: "saved" | "queued";
  assessmentType?: string;
  queuedMutationId?: string;
};

/** Offline-safe replacement for the initial-create RN ICA save. */
export async function saveRnicaAssessmentOffline(args: SaveArgs): Promise<OfflineSaveResult> {
  const clientRequestId = generateClientId();
  const payloadWithId = { ...args, clientRequestId };
  try {
    const result = await saveRnicaAssessment(payloadWithId);
    return { ...(result as Record<string, unknown>), status: "saved" } as OfflineSaveResult;
  } catch (error) {
    if (!isConnectivityFailure(error)) throw error;

    const mutationId = clientRequestId;
    const mutation: QueuedMutation = {
      id: mutationId,
      kind: "rnica_create",
      createdAt: new Date().toISOString(),
      status: "pending",
      attempts: 0,
      payload: { ...payloadWithId },
    };
    await enqueueMutation(mutation);
    triggerSync(); // best-effort immediate attempt; no-op if still offline

    return {
      assessmentId: `${OFFLINE_ID_PREFIX}${mutationId}`,
      status: "queued",
      assessmentType: args.assessmentSubtype,
      queuedMutationId: mutationId,
    };
  }
}

/** Offline-safe replacement for RN ICA assessment updates. */
export async function updateRnicaAssessmentOffline(
  assessmentId: string,
  formData: Record<string, unknown>,
  fieldProvenance?: Array<Record<string, unknown>>
): Promise<OfflineSaveResult> {
  // Still-unsynced local draft: fold this edit into the queued create
  // instead of queuing a PUT against an assessmentId the server has never
  // heard of.
  if (isOfflineDraftId(assessmentId)) {
    const mutationId = draftMutationId(assessmentId);
    const existing = await getMutation(mutationId);
    if (existing) {
      await updateMutation(mutationId, {
        payload: { ...existing.payload, formData, ...(fieldProvenance ? { fieldProvenance } : {}) },
      });
      triggerSync();
      return { assessmentId, status: "queued", queuedMutationId: mutationId };
    }
    // The create already synced and was removed from the queue between
    // this call being made and now (e.g. a background sync completed
    // concurrently) but the caller's local state hasn't been refreshed
    // with the real id yet. Fall through and surface this as an error the
    // caller can react to, rather than silently doing nothing.
    throw new Error(
      "This assessment finished syncing in the background. Reload the chart to continue editing with its saved id."
    );
  }

  try {
    await updateRnicaAssessment(assessmentId, formData, fieldProvenance);
    return { assessmentId, status: "saved" };
  } catch (error) {
    if (!isConnectivityFailure(error)) throw error;

    const mutationId = generateClientId();
    const mutation: QueuedMutation = {
      id: mutationId,
      kind: "rnica_update",
      createdAt: new Date().toISOString(),
      status: "pending",
      attempts: 0,
      payload: { assessmentId, formData, ...(fieldProvenance ? { fieldProvenance } : {}) },
    };
    await enqueueMutation(mutation);
    triggerSync();

    return { assessmentId, status: "queued", queuedMutationId: mutationId };
  }
}

/** Replays a single queued RNICA mutation. Used by the sync manager only. */
export async function replayRnicaMutation(mutation: {
  kind: string;
  payload: Record<string, unknown>;
}): Promise<void> {
  if (mutation.kind === "rnica_create") {
    await saveRnicaAssessment(mutation.payload as SaveArgs);
    return;
  }
  if (mutation.kind === "rnica_update") {
    const { assessmentId, formData, fieldProvenance } = mutation.payload as {
      assessmentId: string;
      formData: Record<string, unknown>;
      fieldProvenance?: Array<Record<string, unknown>>;
    };
    await updateRnicaAssessment(assessmentId, formData, fieldProvenance);
    return;
  }
  throw new Error(`Unknown RNICA mutation kind: ${mutation.kind}`);
}
