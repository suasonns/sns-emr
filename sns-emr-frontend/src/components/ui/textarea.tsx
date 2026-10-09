import * as React from "react";
import { cn } from "../../lib/utils";

// shadcn/ui-style Textarea, restyled to the real RNICA theme tokens
// (rnica-inputBg / rnica-border / rnica-focusRing).
const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-[72px] w-full rounded-md border border-solid border-rnica-border bg-rnica-inputBg px-3 py-2 text-sm text-rnica-text",
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
Textarea.displayName = "Textarea";

export { Textarea };
