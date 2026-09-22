import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

// shadcn/ui-style Badge, with variants matching the RNICA Figma reference's
// pill labels (RECERTIFICATION, High Risk, Moderate Risk, etc.). Colors are
// theme tokens (--sns-*) so both light and dark reference screenshots are
// reproducible from the same component.
const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide whitespace-nowrap",
  {
    variants: {
      variant: {
        neutral: "bg-rnica-bgAlt text-rnica-muted border border-rnica-border",
        teal: "bg-[color-mix(in_srgb,var(--sns-teal)_15%,transparent)] text-rnica-teal border border-[color-mix(in_srgb,var(--sns-teal)_40%,transparent)]",
        orange: "bg-[color-mix(in_srgb,var(--sns-orange)_15%,transparent)] text-rnica-orange border border-[color-mix(in_srgb,var(--sns-orange)_40%,transparent)]",
        red: "bg-[color-mix(in_srgb,var(--sns-red)_15%,transparent)] text-rnica-red border border-[color-mix(in_srgb,var(--sns-red)_40%,transparent)]",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
