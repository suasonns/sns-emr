// Offline-aware wrapper around document upload.
//
// If the upload fails due to a connectivity problem, the file bytes are
// stored in IndexedDB (as a real Blob) along with its metadata, and queued
// for replay. Because Phase A's backend upload endpoint deduplicates by
// (tenant, patient, sha256 content hash), retrying the *entire* file on
// reconnect is always safe -- there is no need for byte-range resumable
// upload to guarantee correctness here: a whole-file retry can never
// create a duplicate document, a duplicate harvest, or duplicate
// structured findings, even if an earlier attempt partially transmitted
// before the connection dropped.

import { uploadDocument, type UploadDocumentResponse } from "./documents";
import { enqueueMutation, type QueuedMutation, generateClientId } from "../offline/db";
import { triggerSync } from "../offline/syncManager";
import { isConnectivityFailure } from "../offline/connectivity";

export type OfflineUploadResult =
  | (UploadDocumentResponse & { status: "uploaded" })
  | { status: "queued"; queuedMutationId: string; fileName: string };

export async function uploadDocumentOffline(
  patientId: string,
  documentType: string,
  file: File,
  source = "EXTERNAL",
  documentPassword?: string
): Promise<OfflineUploadResult> {
  try {
    const result = await uploadDocument(patientId, documentType, file, source, documentPassword);
    return { ...result, status: "uploaded" };
  } catch (error) {
    if (!isConnectivityFailure(error)) throw error;

    const mutationId = generateClientId();
    const mutation: QueuedMutation = {
      id: mutationId,
      kind: "document_upload",
      createdAt: new Date().toISOString(),
      status: "pending",
      attempts: 0,
      payload: {
        patientId,
        documentType,
        source,
        documentPassword: documentPassword ?? null,
        fileName: file.name,
      },
      fileBlob: file,
    };
    await enqueueMutation(mutation);
    triggerSync();

    return { status: "queued", queuedMutationId: mutationId, fileName: file.name };
  }
}

/** Replays a single queued document-upload mutation. Used by the sync
 * manager only. */
export async function replayDocumentMutation(mutation: {
  payload: Record<string, unknown>;
  fileBlob?: Blob;
}): Promise<void> {
  const { patientId, documentType, source, documentPassword, fileName } = mutation.payload as {
    patientId: string;
    documentType: string;
    source: string;
    documentPassword: string | null;
    fileName: string;
  };
  if (!mutation.fileBlob) {
    throw new Error("Queued document upload is missing its file data");
  }
  const file = new File([mutation.fileBlob], fileName, { type: mutation.fileBlob.type });
  await uploadDocument(patientId, documentType, file, source, documentPassword ?? undefined);
}
