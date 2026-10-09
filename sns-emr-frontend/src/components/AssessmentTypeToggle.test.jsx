import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { axe } from "jest-axe";

import AssessmentTypeToggle from "./AssessmentTypeToggle";

describe("AssessmentTypeToggle", () => {
  it("renders the exact Update Assessment / Recertification Assessment labels", () => {
    render(<AssessmentTypeToggle value="update" onChange={() => {}} />);
    expect(screen.getByRole("radio", { name: "Update Assessment" })).toBeTruthy();
    expect(screen.getByRole("radio", { name: "Recertification Assessment" })).toBeTruthy();
  });

  it("marks the active option as checked via aria-checked", () => {
    render(<AssessmentTypeToggle value="recert" onChange={() => {}} />);
    expect(screen.getByRole("radio", { name: "Recertification Assessment" }).getAttribute("aria-checked")).toBe("true");
    expect(screen.getByRole("radio", { name: "Update Assessment" }).getAttribute("aria-checked")).toBe("false");
  });

  it("calls onChange with the selected value when enabled", () => {
    const onChange = vi.fn();
    render(<AssessmentTypeToggle value="update" onChange={onChange} />);
    fireEvent.click(screen.getByRole("radio", { name: "Recertification Assessment" }));
    expect(onChange).toHaveBeenCalledWith("recert");
  });

  it("disables both options and does not call onChange when disabled", () => {
    const onChange = vi.fn();
    render(<AssessmentTypeToggle value="update" onChange={onChange} disabled />);
    const recertButton = screen.getByRole("radio", { name: "Recertification Assessment" });
    expect(recertButton.disabled).toBe(true);
    fireEvent.click(recertButton);
    expect(onChange).not.toHaveBeenCalled();
  });

  it("exposes a radiogroup with an accessible label", () => {
    render(<AssessmentTypeToggle value="update" onChange={() => {}} />);
    expect(screen.getByRole("radiogroup", { name: "Reason for assessment" })).toBeTruthy();
  });

  it("has no detectable accessibility violations (enabled)", async () => {
    const { container } = render(<AssessmentTypeToggle value="update" onChange={() => {}} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("has no detectable accessibility violations (disabled)", async () => {
    const { container } = render(<AssessmentTypeToggle value="update" onChange={() => {}} disabled />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
