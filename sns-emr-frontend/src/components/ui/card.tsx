import * as React from "react";
import { cn } from "../../lib/utils";

// shadcn/ui-style Card primitives, restyled to the real RNICA theme tokens
// (rnica-card / rnica-border / rnica-text, mapped to --sns-* in
// tailwind.config.js) instead of the library's default palette.
function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-xl border border-rnica-border bg-rnica-card text-rnica-text shadow-sm",
        className
      )}
      {...props}
    />
  );
}

function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center justify-between gap-3 px-5 pt-4", className)}
      {...props}
    />
  );
}

function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("flex items-center gap-2 text-[15px] font-semibold leading-none", className)}
      {...props}
    />
  );
}

function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 py-4", className)} {...props} />;
}

export { Card, CardHeader, CardTitle, CardContent };
