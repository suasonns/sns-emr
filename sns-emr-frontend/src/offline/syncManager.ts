// Background sync engine.
//
// Drains the durable IndexedDB mutation queue whenever connectivity is
// (re)established, replaying each queued RN write against the real API in
// the order it was created. This is what turns "the RN's device captured
// the work offline" into "the chart reflects it" once a signal is
// available again -- automatically, with no action required from the RN
// and no re-entry of anything they already did.
//
// Safety properties this relies on:
//   - RNICA creates carry a clientRequestId; the backend returns the
//     existing assessment for a repeated id instead of creating a
//     duplicate DRAFT (see save_rnica_assessment in app/api/visits.py).
//   - RNICA updates are full-replace PUTs against a specific assessmentId,
//     which are naturally idempotent to retry.
//   - Document uploads carry the full file bytes and are deduplicated
//     server-side by content hash (Phase A durability work), so retrying a
//     whole-file upload after a partial failure can never create a
//     duplicate document or duplicate structured findings/RNICA writes.
//   - Mutations are replayed strictly in creation order, so a later edit
//     can never be overtaken by an earlier one replaying out of order.
//   - This queue only ever contains the RN's own captured edits -- it never
//     touches structured-finding auto-apply state, so it cannot conflict
//     with or overwrite already-reviewed values.

import {
  listMutations,
  updateMutation,
  removeMutation,
  appendAudit,
  type QueuedMutation,
} from "./db";
import { probeConnectivity, subscribeConnectivity, isOnline } from "./networkStatus";
import { replayRnicaMutation } from "../api/offlineAssessmentApi";
import { replayDocumentMutation } from "../api/offlineDocumentApi";

const MAX_ATTEMPTS_BEFORE_BACKOFF_CAP = 6;
const BASE_BACKOFF_MS = 5_000;

export type SyncManagerListener = (state: SyncState) => void;

export type SyncState = {
  syncing: boolean;
  pendingCount: number;
  lastSyncAt?: string;
  lastError?: string;
};

let currentState: SyncState = { syncing: false, pendingCount: 0 };
const stateListeners = new Set<SyncManagerListener>();
let syncInFlight: Promise<void> | null = null;
let started = false;

function setState(patch: Partial<SyncState>) {
  currentState = { ...currentState, ...patch };
  stateListeners.forEach((listener) => listener(currentState));
}

export function subscribeSyncState(listener: SyncManagerListener): () => void {
  stateListeners.add(listener);
  listener(currentState);
  return () => stateListeners.delete(listener);
}

export function getSyncState(): SyncState {
  return currentState;
}

async function refreshPendingCount() {
  const all = await listMutations();
  setState({
    pendingCount: all.filter((m) => m.status !== "synced").length,
  });
}

function backoffElapsed(mutation: QueuedMutation): boolean {
  if (!mutation.lastAttemptAt) return true;
  const attempts = Math.min(mutation.attempts, MAX_ATTEMPTS_BEFORE_BACKOFF_CAP);
  const delay = BASE_BACKOFF_MS * Math.pow(2, attempts);
  return Date.now() - new Date(mutation.lastAttemptAt).getTime() >= delay;
}

async function replayOne(mutation: QueuedMutation): Promise<void> {
  await updateMutation(mutation.id, {
    status: "syncing",
    attempts: mutation.attempts + 1,
    lastAttemptAt: new Date().toISOString(),
  });
  await appendAudit({
    mutationId: mutation.id,
    kind: mutation.kind,
    event: "attempt",
    timestamp: new Date().toISOString(),
  });

  try {
    if (mutation.kind === "document_upload") {
      await replayDocumentMutation(mutation);
    } else {
      await replayRnicaMutation(mutation);
    }
    await removeMutation(mutation.id);
    await appendAudit({
      mutationId: mutation.id,
      kind: mutation.kind,
      event: "success",
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await updateMutation(mutation.id, { status: "failed", lastError: message });
    await appendAudit({
      mutationId: mutation.id,
      kind: mutation.kind,
      event: "failure",
      timestamp: new Date().toISOString(),
      detail: message,
    });
    throw error;
  }
}

/** Drains the queue once. Safe to call repeatedly / overlap -- concurrent
 * calls share the same in-flight promise so the queue is never processed
 * by two drains at once. */
export function triggerSync(): Promise<void> {
  if (syncInFlight) return syncInFlight;

  syncInFlight = (async () => {
    setState({ syncing: true });
    try {
      const online = isOnline() || (await probeConnectivity());
      if (!online) return;

      const queued = await listMutations();
      for (const mutation of queued) {
        if (mutation.status === "synced") continue;
        if (mutation.status === "failed" && !backoffElapsed(mutation)) continue;
        try {
          await replayOne(mutation);
        } catch {
          // Network/server error on this item -- stop draining further
          // items for this pass (preserves order) and let the next
          // triggerSync() call (reconnect event / periodic probe) retry.
          break;
        }
      }
    } finally {
      await refreshPendingCount();
      setState({ syncing: false, lastSyncAt: new Date().toISOString() });
      syncInFlight = null;
    }
  })();

  return syncInFlight;
}

/** Wires the sync manager to connectivity changes and starts the periodic
 * safety-net drain. Call once at app startup. */
export function startSyncManager(): void {
  if (started) return;
  started = true;

  refreshPendingCount();

  subscribeConnectivity((online) => {
    if (online) triggerSync();
  });

  // Attempt a drain immediately on load, in case the RN closed the tab
  // mid-day with queued work and is reopening it now with a signal.
  triggerSync();
}
