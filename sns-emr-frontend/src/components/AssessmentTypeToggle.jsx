import React from "react";
import "./rn-ica/design-system/RnicaTailwind.css";
import { RadioGroup, RadioGroupItem } from "./ui/radio-group";

// Refactored onto the shadcn/ui RadioGroup primitive (src/components/ui/radio-group.tsx)
// per the approved RNICA Figma reference (rnica-figma-reference pill toggle) and the
// SNS shadcn/ui adoption rule (docs/governance/SNS_RNICA_SHADCN_UI_ADOPTION_RULE.md).
// Same two options, same exact labels, same radiogroup/radio ARIA roles and
// disabled behavior as before -- only the implementation moved from hand-rolled
// buttons + inline hex styles onto Radix RadioGroup + rnica-* theme tokens.
// No visual redesign: still a pill-shaped two-option toggle.
const OPTIONS = [
  { value: "update", label: "Update Assessment" },
  { value: "recert", label: "Recertification Assessment" },
];

export default function AssessmentTypeToggle({ value = "update", onChange, disabled = false }) {
  return (
    <RadioGroup
      aria-label="Reason for assessment"
      aria-disabled={disabled || undefined}
      value={value}
      onValueChange={(next) => !disabled && onChange?.(next)}
      disabled={disabled}
      className={`rounded-full bg-rnica-bgAlt border border-solid border-rnica-border p-1.5 shadow-panel ${
        disabled ? "opacity-60" : ""
      }`}
    >
      {OPTIONS.map((option) => (
        <RadioGroupItem key={option.value} value={option.value} disabled={disabled}>
          {option.label}
        </RadioGroupItem>
      ))}
    </RadioGroup>
  );
}
