// IndexedDB wrapper for the offline durable-write queue.
//
// This is the browser-side counterpart to the backend's Phase A document
// durability work: instead of a failed network request silently losing an
// RN's assessment edit or document upload, the write is captured here and
// replayed automatically once connectivity returns (see syncManager.ts).
//
// Two object stores:
//   - "mutations"  : the actual queued writes, in creation order.
//   - "audit_log"  : an append-only record of every enqueue/attempt/outcome,
//                    so "what happened to my offline work" is always
//                    answerable, not just "did it eventually sync".
//
// No external dependency (idb/dexie) is used -- the native IndexedDB API is
// small enough here that a thin promise wrapper is simpler than adding a
// new runtime dependency for ~150 lines of code.

const DB_NAME = "sns_emr_offline";
const DB_VERSION = 1;
const MUTATIONS_STORE = "mutations";
const AUDIT_STORE = "audit_log";

export type MutationKind =
  | "rnica_create"
  | "rnica_update"
  | "document_upload"
  | "signal_review";

export type MutationStatus = "pending" | "syncing" | "failed" | "synced";

export type QueuedMutation = {
  id: string; // client-generated uuid, stable across retries
  kind: MutationKind;
  createdAt: string; // ISO timestamp, used to preserve write order on replay
  status: MutationStatus;
  attempts: number;
  lastAttemptAt?: string;
  lastError?: string;
  // Free-form payload, shape depends on `kind` (see offlineAssessmentApi.ts
  // and offlineDocumentApi.ts for the concrete shapes).
  payload: Record<string, unknown>;
  // For document uploads, the file bytes can't be serialized as plain JSON;
  // stored as a real Blob, which IndexedDB natively supports.
  fileBlob?: Blob;
};

export type AuditEntry = {
  id?: number; // autoincrement
  mutationId: string;
  kind: MutationKind;
  event: "queued" | "attempt" | "success" | "failure" | "deduplicated";
  timestamp: string;
  detail?: string;
};

let dbPromise: Promise<IDBDatabase> | null = null;

function openDb(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("IndexedDB is not available in this environment"));
      return;
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(MUTATIONS_STORE)) {
        const store = db.createObjectStore(MUTATIONS_STORE, { keyPath: "id" });
        store.createIndex("by_status", "status");
        store.createIndex("by_createdAt", "createdAt");
      }
      if (!db.objectStoreNames.contains(AUDIT_STORE)) {
        const auditStore = db.createObjectStore(AUDIT_STORE, {
          keyPath: "id",
          autoIncrement: true,
        });
        auditStore.createIndex("by_mutationId", "mutationId");
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  return dbPromise;
}

function promisifyRequest<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function enqueueMutation(mutation: QueuedMutation): Promise<void> {
  const db = await openDb();
  const tx = db.transaction([MUTATIONS_STORE, AUDIT_STORE], "readwrite");
  tx.objectStore(MUTATIONS_STORE).put(mutation);
  tx.objectStore(AUDIT_STORE).put({
    mutationId: mutation.id,
    kind: mutation.kind,
    event: "queued",
    timestamp: new Date().toISOString(),
  } as AuditEntry);
  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getMutation(id: string): Promise<QueuedMutation | undefined> {
  const db = await openDb();
  const tx = db.transaction(MUTATIONS_STORE, "readonly");
  return promisifyRequest(tx.objectStore(MUTATIONS_STORE).get(id)) as Promise<
    QueuedMutation | undefined
  >;
}

export async function updateMutation(
  id: string,
  patch: Partial<QueuedMutation>
): Promise<void> {
  const db = await openDb();
  const tx = db.transaction(MUTATIONS_STORE, "readwrite");
  const store = tx.objectStore(MUTATIONS_STORE);
  const existing = await promisifyRequest(store.get(id));
  if (!existing) return;
  store.put({ ...existing, ...patch });
  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function removeMutation(id: string): Promise<void> {
  const db = await openDb();
  const tx = db.transaction(MUTATIONS_STORE, "readwrite");
  tx.objectStore(MUTATIONS_STORE).delete(id);
  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function listMutations(): Promise<QueuedMutation[]> {
  const db = await openDb();
  const tx = db.transaction(MUTATIONS_STORE, "readonly");
  const all = await promisifyRequest(tx.objectStore(MUTATIONS_STORE).getAll());
  // Replay strictly in creation order so, e.g., an RNICA "create" is never
  // applied after a later "update" queued for the same draft.
  return (all as QueuedMutation[]).sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}

export async function countPendingMutations(): Promise<number> {
  const all = await listMutations();
  return all.filter((m) => m.status === "pending" || m.status === "failed").length;
}

export async function appendAudit(entry: AuditEntry): Promise<void> {
  const db = await openDb();
  const tx = db.transaction(AUDIT_STORE, "readwrite");
  tx.objectStore(AUDIT_STORE).put(entry);
  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function listAuditLog(mutationId?: string): Promise<AuditEntry[]> {
  const db = await openDb();
  const tx = db.transaction(AUDIT_STORE, "readonly");
  const store = tx.objectStore(AUDIT_STORE);
  if (mutationId) {
    const index = store.index("by_mutationId");
    return promisifyRequest(index.getAll(mutationId)) as Promise<AuditEntry[]>;
  }
  return promisifyRequest(store.getAll()) as Promise<AuditEntry[]>;
}

export function generateClientId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // Fallback for environments without crypto.randomUUID (older browsers).
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
