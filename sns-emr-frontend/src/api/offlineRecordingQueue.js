// Durable client-side queue for visit recordings that couldn't upload
// immediately (offline, connectivity drop, backend unreachable). Recordings
// are written here BEFORE the upload attempt so the audio survives a lost
// connection, a closed tab, or a browser restart — the RN never has to
// re-record. Each entry is keyed by clientRecordingId, the same idempotency
// key the backend uses to dedupe retries, so replaying an entry (even
// multiple times, e.g. one attempt on reconnect plus a manual "Retry now")
// can never create a duplicate recording/transcript/RNICA write.
const DB_NAME = "sns_emr_offline_recordings";
const STORE_NAME = "pending_visit_recordings";
const DB_VERSION = 1;

function openDb() {
  return new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) {
      reject(new Error("IndexedDB is not available in this browser."));
      return;
    }
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "clientRecordingId" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// entry: { clientRecordingId, patientId, assessmentId, assessmentType,
//          blob, durationSeconds, mimeType, consentConfirmed, createdAt,
//          attempts, lastError, lastAttemptAt }
export async function queueRecording(entry) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(entry);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function removeQueuedRecording(clientRecordingId) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).delete(clientRecordingId);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function listQueuedRecordings(patientId) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readonly");
    const req = tx.objectStore(STORE_NAME).getAll();
    req.onsuccess = () => {
      const all = req.result || [];
      all.sort((a, b) => (a.createdAt || "").localeCompare(b.createdAt || ""));
      resolve(patientId ? all.filter((r) => r.patientId === patientId) : all);
    };
    req.onerror = () => reject(req.error);
  });
}

export async function markQueuedAttempt(clientRecordingId, lastError) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const getReq = store.get(clientRecordingId);
    getReq.onsuccess = () => {
      const rec = getReq.result;
      if (rec) {
        rec.attempts = (rec.attempts || 0) + 1;
        rec.lastError = lastError || "";
        rec.lastAttemptAt = new Date().toISOString();
        store.put(rec);
      }
    };
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}
