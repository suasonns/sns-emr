import * as React from "react";
import { cn } from "../../lib/utils";

// shadcn/ui-style Input, restyled to the real RNICA theme tokens
// (rnica-inputBg / rnica-border / rnica-focusRing).
const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        "flex h-9 w-full rounded-md border border-solid border-rnica-border bg-rnica-inputBg px-3 py-1 text-sm text-rnica-text",
        "placeholder:text-rnica-muted",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rnica-focusRing",
        "disabled:cursor-not-allowed disabled:opacity-60 disabled:bg-rnica-bgAlt",
        "aria-[invalid=true]:border-rnica-borderCritical",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export { Input };
