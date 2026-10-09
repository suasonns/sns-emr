import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

// shadcn/ui-style Alert, restyled to the real RNICA theme tokens
// (rnica-criticalBg/borderCritical for errors, rnica-successBg/teal for
// confirmations) instead of the library's default palette. Plain markup
// (not Radix-based, matching shadcn's own Alert) with role="alert" so
// validation errors and save confirmations are announced to assistive
// technology without relying on color alone.
const alertVariants = cva("rounded-md border border-solid px-3 py-2 text-xs font-medium", {
  variants: {
    variant: {
      default: "bg-rnica-bgAlt border-rnica-border text-rnica-text",
      destructive: "bg-rnica-criticalBg border-rnica-borderCritical text-rnica-red",
      success: "bg-rnica-successBg border-[color-mix(in_srgb,var(--sns-green)_40%,transparent)] text-rnica-green",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

export interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(({ className, variant, ...props }, ref) => (
  <div ref={ref} role="alert" className={cn(alertVariants({ variant }), className)} {...props} />
));
Alert.displayName = "Alert";

export { Alert, alertVariants };
