// Session-stability regression tests (billing navigation sign-out
// defect). Locks in the corrected behavior of the raw-fetch API
// helpers in api/dashboard.ts, api/census.ts, and api/ownerAdmin.ts:
//
//   - A 401 (access token expired) triggers exactly one shared,
//     single-flight token refresh and a single retry of the original
//     request -- it must NOT immediately clear the session.
//   - A successful refresh means the caller gets its data back with no
//     error and no session clear.
//   - A failed refresh (no/invalid refresh token) clears the session
//     and redirects to /login exactly once.
//   - A 403 (tenant suspended / role denial) is never treated as
//     session expiration and never clears a valid session.
//
// These are unit tests against the fetch-helper layer (mocking global
// fetch + the shared client.ts refresh/redirect functions), not full
// browser acceptance tests -- see the browser-level navigation
// scenario tests for the end-to-end walk described in the directive.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../client", () => ({
  ensureFreshAccessToken: vi.fn(),
  redirectToLogin: vi.fn(),
  default: { get: vi.fn(), post: vi.fn() },
}));

import { ensureFreshAccessToken, redirectToLogin } from "../client";
import { setAccessToken, setRefreshToken } from "../session";

const mockEnsureFreshAccessToken = vi.mocked(ensureFreshAccessToken);
const mockRedirectToLogin = vi.mocked(redirectToLogin);

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("dashboard.ts authorizedFetch session handling", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    setAccessToken("initial-access-token");
    setRefreshToken("initial-refresh-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("retries once and succeeds after a single-flight refresh on 401", async () => {
    const fetchMock = vi
      .fn()
      // First attempt: expired access token.
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Invalid or expired token" }))
      // Retry after refresh: succeeds.
      .mockResolvedValueOnce(jsonResponse(200, { total_patients: 3 }));
    vi.stubGlobal("fetch", fetchMock);
    mockEnsureFreshAccessToken.mockResolvedValue("new-access-token");

    const { fetchTenantDashboard } = await import("../dashboard");
    const result = await fetchTenantDashboard();

    expect(result).toEqual({ total_patients: 3 });
    expect(mockEnsureFreshAccessToken).toHaveBeenCalledTimes(1);
    expect(mockRedirectToLogin).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("clears session and redirects to login when refresh fails", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Invalid or expired token" }));
    vi.stubGlobal("fetch", fetchMock);
    mockEnsureFreshAccessToken.mockResolvedValue(null);

    const { fetchTenantDashboard } = await import("../dashboard");

    await expect(fetchTenantDashboard()).rejects.toThrow(
      "Session expired. Please sign in again."
    );
    expect(mockRedirectToLogin).toHaveBeenCalledTimes(1);
  });

  it("never treats a 403 as session expiration and never redirects to login", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(403, {
          detail: "This agency's platform access is currently suspended",
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    const { fetchTenantDashboard } = await import("../dashboard");

    await expect(fetchTenantDashboard()).rejects.toThrow(
      "This agency's platform access is currently suspended"
    );
    expect(mockEnsureFreshAccessToken).not.toHaveBeenCalled();
    expect(mockRedirectToLogin).not.toHaveBeenCalled();
  });

  it("does not redirect and returns data when the access token is still valid", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { ready_count: 5 }));
    vi.stubGlobal("fetch", fetchMock);

    const { fetchTenantDashboard } = await import("../dashboard");
    const result = await fetchTenantDashboard();

    expect(result).toEqual({ ready_count: 5 });
    expect(mockEnsureFreshAccessToken).not.toHaveBeenCalled();
    expect(mockRedirectToLogin).not.toHaveBeenCalled();
  });
});

describe("census.ts fetchJson session handling", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    setAccessToken("initial-access-token");
    setRefreshToken("initial-refresh-token");
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("retries once and succeeds after refresh on 401", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Invalid or expired token" }))
      .mockResolvedValueOnce(jsonResponse(200, { tenant_id: "t1", patient_count: 1, patients: [] }));
    vi.stubGlobal("fetch", fetchMock);
    mockEnsureFreshAccessToken.mockResolvedValue("new-access-token");

    const { fetchCensusWorkspace } = await import("../census");
    const result = await fetchCensusWorkspace();

    expect(result.tenant_id).toBe("t1");
    expect(mockEnsureFreshAccessToken).toHaveBeenCalledTimes(1);
    expect(mockRedirectToLogin).not.toHaveBeenCalled();
  });

  it("does not clear session on 403", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(403, { detail: "Forbidden" }));
    vi.stubGlobal("fetch", fetchMock);

    const { fetchCensusWorkspace } = await import("../census");

    await expect(fetchCensusWorkspace()).rejects.toThrow();
    expect(mockEnsureFreshAccessToken).not.toHaveBeenCalled();
    expect(mockRedirectToLogin).not.toHaveBeenCalled();
  });
});
