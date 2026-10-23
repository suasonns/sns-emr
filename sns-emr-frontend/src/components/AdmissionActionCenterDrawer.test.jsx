import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import {
  ACTION_CENTER_REQUEST_TYPES,
  ACTION_CENTER_STATUSES,
} from "./AdmissionActionCenterDrawer";
import AdmissionActionCenterDrawer from "./AdmissionActionCenterDrawer";

const mocks = vi.hoisted(() => ({
  listRnicaActionCenterRequests: vi.fn(),
  createRnicaActionCenterRequest: vi.fn(),
  updateRnicaActionCenterRequestStatus: vi.fn(),
  completeRnicaActionCenterRequest: vi.fn(),
  cancelRnicaActionCenterRequest: vi.fn(),
}));

vi.mock("../api/icaAssessments", () => ({
  listRnicaActionCenterRequests: mocks.listRnicaActionCenterRequests,
  createRnicaActionCenterRequest: mocks.createRnicaActionCenterRequest,
  updateRnicaActionCenterRequestStatus: mocks.updateRnicaActionCenterRequestStatus,
  completeRnicaActionCenterRequest: mocks.completeRnicaActionCenterRequest,
  cancelRnicaActionCenterRequest: mocks.cancelRnicaActionCenterRequest,
}));

const STYLES = {
  sectionTitle: {},
  sectionSubtitle: {},
  card: {},
  cardTitle: {},
  formGroup: {},
  label: {},
  select: {},
  textarea: {},
  btnPrimary: {},
  btnSecondary: {},
  warningBox: {},
  statusBadge: {},
};
const COLORS = { white: "#fff", gray: "#888", dark: "#111", success: "#0F766E", warning: "#B45309" };

function renderDrawer(overrides = {}) {
  const onClose = vi.fn();
  render(
    <AdmissionActionCenterDrawer
      open
      onClose={onClose}
      assessmentId="assessment-1"
      sourceSection="respiratory"
      patientName="Jane Doe"
      styles={STYLES}
      COLORS={COLORS}
      {...overrides}
    />,
  );
  return { onClose };
}

describe("Admission Action Center (Phase A) request types", () => {
  it("exposes exactly the six in-scope request types", () => {
    const values = ACTION_CENTER_REQUEST_TYPES.map((t) => t.value);
    expect(values).toEqual([
      "MEDICATION_REQUEST",
      "PHYSICIAN_ORDER",
      "PHYSICIAN_CONTACT",
      "DME_ORDER",
      "SUPPLY_ORDER",
      "REFERRAL",
    ]);
  });

  it("does not include out-of-scope types (Lab / Oxygen / Treatment)", () => {
    const values = ACTION_CENTER_REQUEST_TYPES.map((t) => t.value);
    expect(values).not.toContain("LAB_ORDER");
    expect(values).not.toContain("OXYGEN_ORDER");
    expect(values).not.toContain("TREATMENT_ORDER");
  });

  it("gives every request type a human-readable label", () => {
    for (const t of ACTION_CENTER_REQUEST_TYPES) {
      expect(typeof t.label).toBe("string");
      expect(t.label.length).toBeGreaterThan(0);
    }
  });
});

describe("Admission Action Center (Phase A) statuses", () => {
  it("tracks the linear non-terminal REQUESTED -> DELIVERED lifecycle in order; COMPLETED/CANCELED are terminal states handled by dedicated complete/cancel endpoints, not this generic status list", () => {
    expect(ACTION_CENTER_STATUSES).toEqual([
      "REQUESTED",
      "ORDERED",
      "SENT",
      "ACKNOWLEDGED",
      "DELIVERED",
    ]);
  });

  it("does not include approval-routing or fulfillment sub-states", () => {
    expect(ACTION_CENTER_STATUSES).not.toContain("PENDING_APPROVAL");
    expect(ACTION_CENTER_STATUSES).not.toContain("APPROVED");
    expect(ACTION_CENTER_STATUSES).not.toContain("REJECTED");
  });
});

describe("Admission Action Center drawer (team-based admission workflow directive)", () => {
  beforeEach(() => {
    mocks.listRnicaActionCenterRequests.mockReset().mockResolvedValue({ requests: [] });
    mocks.createRnicaActionCenterRequest.mockReset().mockResolvedValue({});
  });

  it("shows the patient's name (never a raw UUID) and labels the close action 'Back to Assessment'", async () => {
    renderDrawer();
    await waitFor(() => expect(mocks.listRnicaActionCenterRequests).toHaveBeenCalled());
    expect(screen.getByText("Jane Doe")).toBeTruthy();
    expect(screen.queryByText("assessment-1")).toBeNull();
    expect(screen.getByRole("button", { name: "Back to Assessment" })).toBeTruthy();
  });

  it("preselects the request type from initialRequestType (e.g. Respiratory's Create/Open Order button)", async () => {
    renderDrawer({ initialRequestType: "PHYSICIAN_ORDER" });
    await waitFor(() => expect(mocks.listRnicaActionCenterRequests).toHaveBeenCalled());
    expect(screen.getByDisplayValue("Physician Order")).toBeTruthy();
  });

  it("lets the RN assign the order task to another role (DPCS, Case Manager, RN, Office RN) via the existing responsible_discipline field", async () => {
    renderDrawer();
    await waitFor(() => expect(mocks.listRnicaActionCenterRequests).toHaveBeenCalled());

    const detailsGroup = screen.getByText("Details").closest("div");
    fireEvent.change(within(detailsGroup).getByPlaceholderText("Describe what is being requested..."), {
      target: { value: "Needs a new nebulizer order" },
    });
    const assignGroup = screen.getByText("Assign Order Task To").closest("div");
    fireEvent.change(within(assignGroup).getByRole("combobox"), { target: { value: "DPCS" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit Request" }));

    await waitFor(() =>
      expect(mocks.createRnicaActionCenterRequest).toHaveBeenCalledWith(
        "assessment-1",
        expect.objectContaining({ responsible_discipline: "DPCS" }),
      ),
    );
  });

  it("does not block closing, and does not send responsible_discipline, when no delegate is chosen (default 'I will complete it')", async () => {
    const { onClose } = renderDrawer();
    await waitFor(() => expect(mocks.listRnicaActionCenterRequests).toHaveBeenCalled());

    const detailsGroup = screen.getByText("Details").closest("div");
    fireEvent.change(within(detailsGroup).getByPlaceholderText("Describe what is being requested..."), {
      target: { value: "Needs budesonide order" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit Request" }));
    await waitFor(() =>
      expect(mocks.createRnicaActionCenterRequest).toHaveBeenCalledWith(
        "assessment-1",
        expect.not.objectContaining({ responsible_discipline: expect.anything() }),
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Back to Assessment" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("protects an unsubmitted draft on close instead of discarding silently (Submit / Discard / Continue Editing)", async () => {
    const { onClose } = renderDrawer();
    await waitFor(() => expect(mocks.listRnicaActionCenterRequests).toHaveBeenCalled());

    const detailsGroup = screen.getByText("Details").closest("div");
    fireEvent.change(within(detailsGroup).getByPlaceholderText("Describe what is being requested..."), {
      target: { value: "Unsent draft text" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Back to Assessment" }));

    expect(onClose).not.toHaveBeenCalled();
    expect(screen.getByText("You have an unsubmitted request")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Discard and Return" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

