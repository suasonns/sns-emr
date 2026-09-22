import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rnica-focusRing disabled:pointer-events-none disabled:opacity-50 disabled:bg-rnica-bgAlt disabled:text-rnica-textDisabled",
  {
    variants: {
      variant: {
        default: "bg-rnica-teal text-rnica-textInverse hover:bg-rnica-tealHover active:bg-rnica-tealPressed",
        outline: "border border-solid border-rnica-borderStrong text-rnica-textStrong bg-transparent hover:border-rnica-teal hover:text-rnica-teal",
        ghost: "text-rnica-muted hover:bg-rnica-bgAlt hover:text-rnica-text",
        danger: "bg-rnica-red text-rnica-textInverse hover:opacity-90",
      },
      size: {
        default: "h-9 px-4",
        sm: "h-8 px-3 text-xs",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp className={cn(buttonVariants({ variant, size }), className)} ref={ref} {...props} />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
