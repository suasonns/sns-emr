// PRODUCT OWNER DIRECTIVE "Safety & Clinical Risk Current State Review
// and Next Actions" (2026-10-24) Issue 1 -- regression coverage for the
// Place-of-Service dual-path bug: the four Living Environment fields
// (Site of Service, Admitted From, Living Arrangement, Availability of
// Assistance) must write to the SAME authoritative
// `formData.demographics.livingSituation.*` path Safety and the HOPE
// report generator read, not a disconnected top-level
// `formData.livingSituation` that nothing else consults.
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// Radix `Select` requires pointer-capture/portal APIs this jsdom test
// environment doesn't polyfill; stub it with a plain native `<select>`
// so the test exercises the real `onValueChange` wiring in
// `HopeAdministrativeReview.jsx` without depending on Radix internals.
vi.mock("../../ui/select", () => {
  const Select = ({ value, onValueChange, disabled, children }) => (
    <select
      value={value ?? ""}
      disabled={disabled}
      onChange={(e) => onValueChange?.(e.target.value)}
    >
      <option value="" />
      {children}
    </select>
  );
  const SelectTrigger = () => null;
  const SelectValue = () => null;
  const SelectContent = ({ children }) => <>{children}</>;
  const SelectItem = ({ value, children }) => <option value={value}>{children}</option>;
  return { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
});

import HopeAdministrativeReview from "./HopeAdministrativeReview";

function renderReview(onUpdateField, value = {}) {
  render(<HopeAdministrativeReview value={value} onUpdateField={onUpdateField} />);
}

// Each `ReviewSection` renders its title in a heading `<span>` followed by
// its control(s) as siblings inside a shared `.rnica-hope-section`
// container -- find the select inside the section whose heading matches.
function selectInSection(titleRegex) {
  const heading = screen.getByText(titleRegex);
  const section = heading.closest(".rnica-hope-section");
  return section.querySelector("select");
}

describe("HopeAdministrativeReview Living Environment -- Place-of-Service wiring", () => {
  it("writes Site of Service to demographics.livingSituation.siteOfService, not a top-level livingSituation section", () => {
    const onUpdateField = vi.fn();
    renderReview(onUpdateField);

    const select = selectInSection(/Site of Service at Admission/i);
    select.value = "01";
    select.dispatchEvent(new Event("change", { bubbles: true }));

    expect(onUpdateField).toHaveBeenCalledWith("demographics", "livingSituation.siteOfService", "01");
    expect(onUpdateField).not.toHaveBeenCalledWith("livingSituation", "siteOfService", "01");
  });

  it("writes Admitted From to demographics.livingSituation.admittedFrom", () => {
    const onUpdateField = vi.fn();
    renderReview(onUpdateField);

    const select = selectInSection(/Admitted From/i);
    select.value = "02";
    select.dispatchEvent(new Event("change", { bubbles: true }));

    expect(onUpdateField).toHaveBeenCalledWith("demographics", "livingSituation.admittedFrom", "02");
    expect(onUpdateField).not.toHaveBeenCalledWith("livingSituation", "admittedFrom", "02");
  });

  it("writes Living Arrangement to demographics.livingSituation.livingArrangement", () => {
    const onUpdateField = vi.fn();
    renderReview(onUpdateField);

    const select = selectInSection(/Living Arrangement/i);
    select.value = "1";
    select.dispatchEvent(new Event("change", { bubbles: true }));

    expect(onUpdateField).toHaveBeenCalledWith("demographics", "livingSituation.livingArrangement", "1");
    expect(onUpdateField).not.toHaveBeenCalledWith("livingSituation", "livingArrangement", "1");
  });

  it("writes Availability of Assistance to demographics.livingSituation.availabilityOfAssistance", () => {
    const onUpdateField = vi.fn();
    renderReview(onUpdateField);

    const select = selectInSection(/Availability of Assistance/i);
    select.value = "24/7 available";
    select.dispatchEvent(new Event("change", { bubbles: true }));

    expect(onUpdateField).toHaveBeenCalledWith("demographics", "livingSituation.availabilityOfAssistance", "24/7 available");
    expect(onUpdateField).not.toHaveBeenCalledWith("livingSituation", "availabilityOfAssistance", "24/7 available");
  });

  it("reflects a site of service already projected onto the flattened `value` prop (the shape RNICA.jsx now builds from demographics.livingSituation)", () => {
    const onUpdateField = vi.fn();
    renderReview(onUpdateField, { siteOfService: "04" });

    const select = selectInSection(/Site of Service at Admission/i);
    expect(select.value).toBe("04");
  });
});
