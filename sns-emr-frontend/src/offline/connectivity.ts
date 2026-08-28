// Shared "was this a connectivity problem or a real server rejection?"
// classifier used by every offline-aware API wrapper.
//
// Naively this would just be "no response came back" (DNS failure, dropped
// connection, request timeout). But behind a reverse proxy or dev server
// proxy (as in this app's Vite dev proxy, and common in production behind
// a load balancer/API gateway), an unreachable backend often still comes
// back as a real HTTP response -- a 502/503/504 from the proxy itself,
// not from the app. Treating those as "real server rejections" would mean
// an RN's work silently fails and is lost instead of being queued, the
// exact opposite of what this offline layer exists to prevent. So those
// gateway-level status codes are treated as connectivity failures too.
//
// Genuine application-level errors (401 auth, 409 already-locked, 422
// validation, etc.) are NOT included here and must still surface to the
// RN immediately so they can act on them.
import axios from "axios";

const GATEWAY_UNAVAILABLE_STATUSES = new Set([502, 503, 504, 408]);

function isConnectivityAxiosError(error: unknown): boolean {
  if (!axios.isAxiosError(error)) return false;

  // No response at all: offline, DNS failure, timeout, dropped mid-flight.
  if (!error.response) return true;

  // A response came back, but it's a gateway/proxy-level failure telling
  // us the real backend was unreachable -- still a connectivity gap from
  // the RN's point of view, not a rejection of their data.
  return GATEWAY_UNAVAILABLE_STATUSES.has(error.response.status);
}

export function isConnectivityFailure(error: unknown): boolean {
  if (isConnectivityAxiosError(error)) return true;

  // Some API wrappers (e.g. icaAssessments.ts's `unwrap`) re-throw a
  // friendlier message-only Error for display purposes, but attach the
  // original AxiosError via `cause` so it isn't lost. Check there too.
  if (error instanceof Error && error.cause) {
    return isConnectivityAxiosError(error.cause);
  }

  return false;
}
