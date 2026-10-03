import * as React from "react";
import * as TogglePrimitive from "@radix-ui/react-toggle";
import { cn } from "../../lib/utils";

const Toggle = React.forwardRef<
  React.ElementRef<typeof TogglePrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof TogglePrimitive.Root>
>(({ className, ...props }, ref) => (
  <TogglePrimitive.Root
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-full border border-rnica-border px-3 py-1 text-xs font-medium",
      "transition-colors hover:bg-rnica-hoverSurface",
      "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rnica-focusRing",
      "disabled:pointer-events-none disabled:opacity-50",
      "data-[state=on]:border-rnica-teal data-[state=on]:bg-rnica-teal data-[state=on]:text-rnica-textInverse data-[state=on]:font-bold",
      className
    )}
    {...props}
  />
));
Toggle.displayName = TogglePrimitive.Root.displayName;

export { Toggle };
