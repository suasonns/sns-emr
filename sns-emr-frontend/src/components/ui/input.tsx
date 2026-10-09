import * as React from "react";
import { cn } from "../../lib/utils";

// shadcn/ui-style Input, restyled to the RNICA theme tokens (rnica-border /
// rnica-bg / rnica-text, mapped to --sns-* in tailwind.config.js) instead of
// the library's default palette. Same plain controlled <input> contract
// (value/onChange/type/placeholder/...rest) as every other shadcn primitive
// already used in RNICA.jsx (Select, Checkbox, RadioGroup).
const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type = "text", ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "flex h-9 w-full rounded-lg border border-rnica-border bg-rnica-bg px-3 py-2 text-[11px] text-rnica-text",
        "placeholder:text-rnica-muted",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rnica-focusRing",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export { Input };
