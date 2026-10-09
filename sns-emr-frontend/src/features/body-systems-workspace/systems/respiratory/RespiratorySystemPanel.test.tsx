import { describe, expect, it } from "vitest";
import { useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  RespiratorySystemPanel,
  INITIAL_RESPIRATORY_FIELD_VALUES,
  type RespiratoryFieldValues,
} from "./RespiratorySystemPanel";

function Harness() {
  const [values, setValues] = useState<RespiratoryFieldValues>(INITIAL_RESPIRATORY_FIELD_VALUES);
  return <RespiratorySystemPanel values={values} onChange={setValues} />;
}

describe("RespiratorySystemPanel", () => {
  it("renders both HOPE impact fields defaulted to not yet assessed", () => {
    render(<Harness />);
    expect(screen.getAllByText("not yet assessed").length).toBeGreaterThanOrEqual(2);
  });

  it("CRITICAL: selecting a SOB severity never changes either HOPE impact field — RN assessment is explicit only", () => {
    render(<Harness />);

    // Both HOPE fields start unset/"not yet assessed".
    const comfortGroup = screen.getByText("HOPE comfort impact").parentElement as HTMLElement;
    const functionGroup = screen.getByText("HOPE function impact").parentElement as HTMLElement;
    expect(comfortGroup.querySelector('[data-state="on"]')?.textContent).toBe("not yet assessed");
    expect(functionGroup.querySelector('[data-state="on"]')?.textContent).toBe("not yet assessed");

    // Select the most severe SOB option.
    fireEvent.click(screen.getByText("severe"));

    // HOPE fields must remain exactly "not yet assessed" — no derivation.
    expect(comfortGroup.querySelector('[data-state="on"]')?.textContent).toBe("not yet assessed");
    expect(functionGroup.querySelector('[data-state="on"]')?.textContent).toBe("not yet assessed");
  });

  it("only shows flow rate field for nasal cannula / mask oxygen delivery, and ventilator info only for ventilator", () => {
    render(<Harness />);
    expect(screen.queryByText("Flow rate (L/min)")).toBeNull();
    expect(screen.queryByText("Ventilator information")).toBeNull();

    fireEvent.click(screen.getByText("nasal cannula"));
    screen.getByText("Flow rate (L/min)");

    fireEvent.click(screen.getByText("ventilator"));
    screen.getByPlaceholderText("Ventilator information");
  });
});
