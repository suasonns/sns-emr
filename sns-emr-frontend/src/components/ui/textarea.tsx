import * as React from "react";
import { cn } from "../../lib/utils";

// shadcn/ui-style Textarea, restyled to the RNICA theme tokens. Same plain
// controlled contract as the rest of RNICA.jsx's shared field primitives.
const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "flex w-full rounded-lg border border-rnica-border bg-rnica-bg px-3 py-2 text-[11px] text-rnica-text",
        "placeholder:text-rnica-muted",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rnica-focusRing",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
);
Textarea.displayName = "Textarea";

export { Textarea };
