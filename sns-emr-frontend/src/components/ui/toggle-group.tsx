import * as React from "react";
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import { cn } from "../../lib/utils";

// Compact chip-row group. type="single" behaves like a mutually-exclusive
// segmented control (radio semantics); type="multiple" behaves like an
// independent multi-select pill row. Visually matches the existing
// FormSegmented/FormPillGroup chip language used across every other RNICA
// section (same pill shape, border, and selected-state color) so this is a
// drop-in replacement, not a new visual language.
const ToggleGroup = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root>
>(({ className, ...props }, ref) => (
  <ToggleGroupPrimitive.Root
    ref={ref}
    // "rnica-chip-group" is a stable marker, not a style: Radix gives a
    // type="single" Root role="radiogroup", which collided with Body
    // Systems' legacy-radio-dot density override
    // (.rnica-bodysystem-workspace [role="radiogroup"]) and crushed every
    // chip row's spacing down to the same 2px/8px gap meant for old
    // RadioGroupItem dot rows. See the Item's comment below for the
    // per-chip version of this same regression.
    className={cn("flex flex-wrap items-center gap-[3px] rnica-chip-group", className)}
    {...props}
  />
));
ToggleGroup.displayName = ToggleGroupPrimitive.Root.displayName;

const ToggleGroupItem = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <ToggleGroupPrimitive.Item
    ref={ref}
    className={cn(
      // "rnica-chip-toggle" is a stable marker, not a style: a single-type
      // Item gets role="radio" from Radix, which made Body Systems' legacy
      // radio-dot density override (targeting real RadioGroupItem dots,
      // via `button[role="radio"]:not(.rnica-segment-btn)`) also match
      // this full pill chip and crush it to a 14x14px dot, truncating its
      // label (owner-reported regression, 2026-10-04: "Neurological...
      // regressed away from the approved Pain/Functional Status design
      // language"). The marker lets that override explicitly exclude
      // every chip built on this shared ToggleGroupItem, everywhere it's
      // used (Pain, Functional Status, and every Body System alike).
      "rnica-chip-toggle inline-flex items-center justify-center whitespace-nowrap rounded-full border px-[9px] py-[2px] text-[11px] leading-[1.6]",
      // Explicit unselected background: Tailwind preflight is disabled
      // project-wide (see RnicaTailwind.css), so a native <button> with no
      // background class falls back to the browser's default button
      // background (opaque white/gray) instead of Tailwind's reset
      // "transparent" -- that white box behind the already-dark
      // `text-rnica-text` is what produced the "white on white, unreadable"
      // unselected chips. bg-transparent lets the card's own dark
      // background show through, matching every other unselected pill.
      "bg-transparent border-rnica-border text-rnica-text font-medium",
      "transition-colors hover:border-rnica-teal",
      "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rnica-focusRing",
      "disabled:pointer-events-none disabled:opacity-50",
      "data-[state=on]:border-rnica-teal data-[state=on]:bg-rnica-teal data-[state=on]:text-rnica-textInverse data-[state=on]:font-bold",
      className
    )}
    {...props}
  >
    {children}
  </ToggleGroupPrimitive.Item>
));
ToggleGroupItem.displayName = ToggleGroupPrimitive.Item.displayName;

export { ToggleGroup, ToggleGroupItem };
