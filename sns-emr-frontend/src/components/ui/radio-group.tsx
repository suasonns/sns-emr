import * as React from "react";
import * as RadioGroupPrimitive from "@radix-ui/react-radio-group";
import { cn } from "../../lib/utils";

// shadcn/ui-style RadioGroup, restyled to the real RNICA theme tokens
// (rnica-teal / rnica-border / rnica-focusRing, mapped to --sns-* in
// tailwind.config.js) instead of the library's default palette. Built on
// Radix's RadioGroup primitive so the exact ARIA radiogroup/radio
// semantics, keyboard navigation (arrow keys), and checked-state
// announcements come from a verified accessible implementation rather than
// a hand-rolled button-group.
const RadioGroup = React.forwardRef<
  React.ElementRef<typeof RadioGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof RadioGroupPrimitive.Root>
>(({ className, ...props }, ref) => (
  <RadioGroupPrimitive.Root ref={ref} className={cn("flex flex-wrap items-center gap-2", className)} {...props} />
));
RadioGroup.displayName = RadioGroupPrimitive.Root.displayName;

const RadioGroupItem = React.forwardRef<
  React.ElementRef<typeof RadioGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof RadioGroupPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <RadioGroupPrimitive.Item
    ref={ref}
    className={cn(
      "rounded-full border-none px-4 py-2.5 text-xs font-bold cursor-pointer transition-colors",
      "bg-transparent text-rnica-muted hover:bg-rnica-hoverSurface",
      "data-[state=checked]:bg-rnica-teal data-[state=checked]:text-rnica-textInverse data-[state=checked]:hover:bg-rnica-tealHover",
      "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rnica-focusRing",
      "disabled:cursor-not-allowed disabled:opacity-60",
      className
    )}
    {...props}
  >
    {children}
  </RadioGroupPrimitive.Item>
));
RadioGroupItem.displayName = RadioGroupPrimitive.Item.displayName;

export { RadioGroup, RadioGroupItem };
