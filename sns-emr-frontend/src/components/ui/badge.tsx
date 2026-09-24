import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

// shadcn/ui-style Badge, with variants matching the RNICA Figma reference's
// pill labels (RECERTIFICATION, High Risk, Moderate Risk, etc.). Colors are
// theme tokens (--sns-*) so both light and dark reference screenshots are
// reproducible from the same component.
const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide whitespace-nowrap border-solid",
  {
    variants: {
      variant: {
        neutral: "bg-rnica-bgAlt text-rnica-muted border border-rnica-border",
        teal: "bg-rnica-tealSoftBg text-rnica-teal border border-rnica-tealSoftBorder",
        orange: "bg-[color-mix(in_srgb,var(--sns-orange)_15%,transparent)] text-rnica-orange border border-[color-mix(in_srgb,var(--sns-orange)_40%,transparent)]",
        red: "bg-[color-mix(in_srgb,var(--sns-red)_15%,transparent)] text-rnica-red border border-[color-mix(in_srgb,var(--sns-red)_40%,transparent)]",
        // Explicit status-semantic variants (Lively Clinical Slate): use
        // these where color must map to a verified severity/completion
        // state, keeping "teal" reserved for brand/neutral-informational
        // labels rather than "done".
        success: "bg-rnica-successBg text-rnica-green border border-[color-mix(in_srgb,var(--sns-green)_40%,transparent)]",
        warning: "bg-rnica-warningBg text-rnica-orange border border-rnica-borderWarning",
        critical: "bg-rnica-criticalBg text-rnica-red border border-rnica-borderCritical",
        ai: "bg-rnica-aiBg text-rnica-purple border border-rnica-borderAI",
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
