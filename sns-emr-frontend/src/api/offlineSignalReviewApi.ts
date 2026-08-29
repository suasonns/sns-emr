// Offline-aware wrapper around marking a harvested structured finding
// (signal) as reviewed ("APPLIED" or "DISMISSED").
//
// This is queued separately from the RNICA field-value write it usually
// follows (see RNICA.jsx's handleApplyStructuredSignal /
// applyStructuredSignalsBulk): the field values are written first via
// saveRnicaAssessmentOffline/updateRnicaAssessmentOffline, and only then is
// the signal marked reviewed. Both mutations are enqueued in that same
// order, and the sync manager replays strictly in creation order, so a
// signal can never end up marked "APPLIED" on the server while its field
// values never actually landed -- the exact bug this offline layer exists
// to prevent (see the comments in RNICA.jsx around these call sites).
//
// Marking a signal APPLIED/DISMISSED twice (e.g. a retried queued mutation
// after a partial failure) is a safe no-op server-side: it's a disposition
// write on a single signal id, not an append, so replay can never create a
// duplicate finding or duplicate review record.

import { reviewHarvestedSignal, batchReviewHarvestedSignals, type SignalReviewDisposition } from "./icaAssessments";
import { enqueueMutation, generateClientId, type QueuedMutation } from "../offline/db";
import { triggerSync } from "../offline/syncManager";
import { isConnectivityFailure } from "../offline/connectivity";

export type SignalReviewResult = { status: "reviewed" | "queued"; queuedMutationId?: string };

/** Offline-safe replacement for reviewing a single structured finding. */
export async function reviewHarvestedSignalOffline(
  signalId: string,
  disposition: SignalReviewDisposition,
  reason?: string
): Promise<SignalReviewResult> {
  try {
    await reviewHarvestedSignal(signalId, disposition, reason);
    return { status: "reviewed" };
  } catch (error) {
    if (!isConnectivityFailure(error)) throw error;
    return queueSignalReview([signalId], disposition, reason);
  }
}

/** Offline-safe replacement for batch-reviewing structured findings (used
 * by "Apply All Non-Conflicting" / "Apply Selected"). */
export async function batchReviewHarvestedSignalsOffline(
  signalIds: string[],
  disposition: SignalReviewDisposition,
  options?: { reason?: string }
): Promise<SignalReviewResult> {
  try {
    await batchReviewHarvestedSignals(signalIds, disposition, options);
    return { status: "reviewed" };
  } catch (error) {
    if (!isConnectivityFailure(error)) throw error;
    return queueSignalReview(signalIds, disposition, options?.reason);
  }
}

async function queueSignalReview(
  signalIds: string[],
  disposition: SignalReviewDisposition,
  reason?: string
): Promise<SignalReviewResult> {
  const mutationId = generateClientId();
  const mutation: QueuedMutation = {
    id: mutationId,
    kind: "signal_review",
    createdAt: new Date().toISOString(),
    status: "pending",
    attempts: 0,
    payload: { signalIds, disposition, reason: reason ?? null },
  };
  await enqueueMutation(mutation);
  triggerSync();
  return { status: "queued", queuedMutationId: mutationId };
}

/** Replays a single queued signal-review mutation. Used by the sync
 * manager only. */
export async function replaySignalReviewMutation(mutation: {
  payload: Record<string, unknown>;
}): Promise<void> {
  const { signalIds, disposition, reason } = mutation.payload as {
    signalIds: string[];
    disposition: SignalReviewDisposition;
    reason?: string | null;
  };
  await batchReviewHarvestedSignals(signalIds, disposition, { reason: reason ?? undefined });
}
