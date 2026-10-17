import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AlertThresholdsPage from "./AlertThresholdsPage";
import { deferred } from "../../test/testUtils";

const mocks = vi.hoisted(() => ({
  fetchAlertThresholds: vi.fn(),
  updateAlertThreshold: vi.fn(),
  useAgency: vi.fn(),
}));

vi.mock("../../api/dashboard", async () => {
  const actual = await vi.importActual("../../api/dashboard");
  return {
    ...actual,
    fetchAlertThresholds: mocks.fetchAlertThresholds,
    updateAlertThreshold: mocks.updateAlertThreshold,
  };
});

vi.mock("../../components/billing/AgencyContext", () => ({
  useAgency: mocks.useAgency,
}));

const baseThreshold = {
  id: "threshold-1",
  tenant_id: "tenant-1",
  alert_type: "OVERDUE_90",
  enabled: true,
  threshold_amount: "100.00",
  threshold_days: 90,
  is_default: false,
};

describe("AlertThresholdsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.useAgency.mockReturnValue({
      selectedAgencyId: "tenant-1",
      agencies: [],
      setSelectedAgencyId: vi.fn(),
      loading: false,
      error: null,
    });
  });

  it("shows loading state before thresholds resolve", () => {
    const pending = deferred();
    mocks.fetchAlertThresholds.mockReturnValue(pending.promise);

    render(<AlertThresholdsPage />);

    expect(screen.getByText("Loading…")).toBeTruthy();
  });

  it("renders threshold rows once data resolves", async () => {
    mocks.fetchAlertThresholds.mockResolvedValue({ items: [baseThreshold] });

    render(<AlertThresholdsPage />);

    await screen.findByText("Overdue 90");
    expect(screen.getByText("$100.00")).toBeTruthy();
    expect(screen.getByText("90")).toBeTruthy();
  });

  it("shows load failures instead of fabricated threshold rows", async () => {
    mocks.fetchAlertThresholds.mockRejectedValue(new Error("Unable to load alert thresholds."));

    render(<AlertThresholdsPage />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load alert thresholds.")).toBeTruthy();
    });
  });
});
