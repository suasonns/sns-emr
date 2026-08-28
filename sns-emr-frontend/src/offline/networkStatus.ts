// Network status detection.
//
// navigator.onLine alone is unreliable (it only reflects whether the device
// has *a* network interface up, e.g. still reports true on a captive wifi
// portal with no real route to the backend). It's used here as a cheap
// first signal, but the source of truth for "is sync actually possible" is
// a lightweight reachability probe against the backend's own health
// endpoint, which is what actually gates whether the sync manager attempts
// to drain the queue.

import api from "../api/client";

export type ConnectivityListener = (online: boolean) => void;

const listeners = new Set<ConnectivityListener>();
let lastKnownOnline = typeof navigator !== "undefined" ? navigator.onLine : true;
let probeTimer: ReturnType<typeof setInterval> | null = null;

const PROBE_INTERVAL_MS = 20_000;

function notify(online: boolean) {
  if (online === lastKnownOnline) return;
  lastKnownOnline = online;
  listeners.forEach((listener) => listener(online));
}

export async function probeConnectivity(): Promise<boolean> {
  try {
    // A cheap, auth-free endpoint; a real 2xx response is the only thing
    // that proves the RN's device can actually reach the backend right now
    // (not just "has a network interface"), which is what actually
    // determines whether queued mutations can be replayed.
    await api.get("/health", { timeout: 5000 });
    notify(true);
    return true;
  } catch {
    notify(false);
    return false;
  }
}

export function isOnline(): boolean {
  return lastKnownOnline;
}

export function subscribeConnectivity(listener: ConnectivityListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function startConnectivityMonitor(): void {
  if (typeof window === "undefined") return;

  window.addEventListener("online", () => {
    probeConnectivity();
  });
  window.addEventListener("offline", () => {
    notify(false);
  });

  // Periodic reachability probe as a safety net -- covers the "connected
  // to wifi with no internet" case that the online/offline browser events
  // don't reliably catch, and doubles as the retry heartbeat for the sync
  // manager when a prior sync attempt failed.
  if (!probeTimer) {
    probeTimer = setInterval(() => {
      probeConnectivity();
    }, PROBE_INTERVAL_MS);
  }

  // Fire an initial probe immediately on load.
  probeConnectivity();
}
