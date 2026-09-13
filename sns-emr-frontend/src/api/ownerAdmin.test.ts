// Regression coverage for ownerAdmin.ts's 401 handling. Any 401 from the
// owner-admin fetch() calls must attempt exactly one shared, single-flight
// access-token refresh (client.ts's ensureFreshAccessToken()) before
// giving up, matching the retry behavior api/client.ts's axios
// interceptor already applies app-wide.
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({
  getAccessToken: vi.fn(() => "expired-token"),
  ensureFreshAccessToken: vi.fn(),
  redirectToLogin: vi.fn(),
}));

vi.mock("./session", () => ({
  getAccessToken: mocks.getAccessToken,
}));

vi.mock("./client", () => ({
  ensureFreshAccessToken: mocks.ensureFreshAccessToken,
  redirectToLogin: mocks.redirectToLogin,
}));

describe("ownerAdmin.ts 401 refresh-retry", () => {
  beforeEach(() => {
    vi.resetModules();
    Object.values(mocks).forEach((m) => m.mockClear());
  });

  it("refreshes once and retries successfully on a single 401", async () => {
    let fetchCallCount = 0;
    globalThis.fetch = vi.fn(async () => {
      fetchCallCount += 1;
      if (fetchCallCount === 1) {
        return { status: 401, ok: false, json: async () => ({ detail: "expired" }) } as Response;
      }
      return { status: 200, ok: true, json: async () => ({ tenants: [] }) } as Response;
    });
    mocks.ensureFreshAccessToken.mockResolvedValue("fresh-token");

    const { fetchOwnerTenants } = await import("./ownerAdmin");
    const result = await fetchOwnerTenants();

    expect(fetchCallCount).toBe(2); // initial 401 + one retry
    expect(mocks.ensureFreshAccessToken).toHaveBeenCalledTimes(1);
    expect(mocks.redirectToLogin).not.toHaveBeenCalled();
    expect(result).toEqual({ tenants: [] });
  });

  it("redirects to login if refresh fails", async () => {
    globalThis.fetch = vi.fn(async () => ({ status: 401, ok: false, json: async () => ({}) }) as unknown as Response);
    mocks.ensureFreshAccessToken.mockResolvedValue(null);

    const { fetchOwnerTenants } = await import("./ownerAdmin");
    await expect(fetchOwnerTenants()).rejects.toThrow("Session expired");

    expect(mocks.redirectToLogin).toHaveBeenCalledTimes(1);
  });

  it("redirects to login if the retried request also 401s", async () => {
    globalThis.fetch = vi.fn(async () => ({ status: 401, ok: false, json: async () => ({}) }) as unknown as Response);
    mocks.ensureFreshAccessToken.mockResolvedValue("fresh-token-that-still-fails");

    const { fetchOwnerTenants } = await import("./ownerAdmin");
    await expect(fetchOwnerTenants()).rejects.toThrow("Session expired");

    expect(mocks.ensureFreshAccessToken).toHaveBeenCalledTimes(1);
    expect(mocks.redirectToLogin).toHaveBeenCalledTimes(1);
  });

  it("does not implement a second competing refresh path per request", async () => {
    let fetchCallCount = 0;
    globalThis.fetch = vi.fn(async () => {
      fetchCallCount += 1;
      if (fetchCallCount <= 2) {
        return { status: 401, ok: false, json: async () => ({}) } as Response;
      }
      return { status: 200, ok: true, json: async () => ({ tenants: [] }) } as Response;
    });
    mocks.ensureFreshAccessToken.mockResolvedValue("fresh-token");

    const { fetchOwnerTenants } = await import("./ownerAdmin");
    await Promise.all([fetchOwnerTenants(), fetchOwnerTenants()]);

    // Each request path calls the shared single-flight primitive exactly
    // once; de-duplication across concurrent callers is client.ts's own
    // responsibility (already covered there), this only proves ownerAdmin.ts
    // defers to it instead of rolling its own refresh logic.
    expect(mocks.ensureFreshAccessToken).toHaveBeenCalledTimes(2);
  });
});
