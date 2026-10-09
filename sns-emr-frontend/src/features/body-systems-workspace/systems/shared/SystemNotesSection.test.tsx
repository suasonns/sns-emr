import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SystemNotesSection } from "./SystemNotesSection";

describe("SystemNotesSection (shared, optional RN Notes component)", () => {
  it("renders a labeled, accessible textarea with explicit optional helper text", () => {
    render(<SystemNotesSection id="test-notes" value={undefined} onChange={vi.fn()} />);

    screen.getByText("RN Notes");
    screen.getByText(/Optional\. Add context or explain the clinical reasoning/);
    const textarea = screen.getByPlaceholderText("Optional clinical context or explanation");
    expect(textarea.getAttribute("id")).toBe("test-notes");
    expect(textarea.getAttribute("aria-describedby")).toBe("test-notes-helper");
  });

  it("supports a custom label while keeping the optional helper text", () => {
    render(<SystemNotesSection id="test-notes" label="Clinical Explanation" value={undefined} onChange={vi.fn()} />);

    screen.getByText("Clinical Explanation");
    screen.getByText(/Optional\./);
  });

  it("renders a blank value when undefined — never shown as incomplete or required", () => {
    render(<SystemNotesSection id="test-notes" value={undefined} onChange={vi.fn()} />);

    const textarea = screen.getByPlaceholderText("Optional clinical context or explanation") as HTMLTextAreaElement;
    expect(textarea.value).toBe("");
    expect(textarea.required).toBe(false);
  });

  it("calls onChange with the new value on every keystroke, never mutating unrelated state", () => {
    const onChange = vi.fn();
    render(<SystemNotesSection id="test-notes" value="" onChange={onChange} />);

    fireEvent.change(screen.getByPlaceholderText("Optional clinical context or explanation"), {
      target: { value: "Daughter reports increased SOB overnight." },
    });

    expect(onChange).toHaveBeenCalledWith("Daughter reports increased SOB overnight.");
  });

  it("renders an existing note value as-is", () => {
    render(<SystemNotesSection id="test-notes" value="Wound dimensions unchanged." onChange={vi.fn()} />);

    const textarea = screen.getByPlaceholderText("Optional clinical context or explanation") as HTMLTextAreaElement;
    expect(textarea.value).toBe("Wound dimensions unchanged.");
  });
});
