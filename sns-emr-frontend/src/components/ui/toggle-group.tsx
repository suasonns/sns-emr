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
    className={cn("flex flex-wrap items-center gap-[3px]", className)}
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
      "inline-flex items-center justify-center whitespace-nowrap rounded-full border px-[9px] py-[2px] text-[11px] leading-[1.6]",
      "border-rnica-border text-rnica-text font-medium",
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
