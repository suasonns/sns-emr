import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Standard shadcn/ui class-merging helper: lets components accept a
// `className` override without producing duplicate/conflicting Tailwind
// utility classes.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
