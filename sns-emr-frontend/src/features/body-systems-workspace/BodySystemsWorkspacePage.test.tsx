import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { BodySystemsWorkspacePage } from "./BodySystemsWorkspacePage";

describe("BodySystemsWorkspacePage", () => {
  it("mounts BodyShieldShell scoped to the given patient id, not a hardcoded id", () => {
    render(<BodySystemsWorkspacePage patientId="patient-42" />);

    const shell = document.querySelector('[data-patient-id="patient-42"]');
    expect(shell).toBeTruthy();
    expect(screen.getAllByText("Body Systems").length).toBeGreaterThan(0);
  });

  it("renders nothing when no patient id is available yet, rather than fabricating one", () => {
    const { container } = render(<BodySystemsWorkspacePage patientId="" />);
    expect(container.firstChild).toBeNull();
  });
});
