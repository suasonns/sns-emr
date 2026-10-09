/**
 * SNS Body Systems Workspace — desktop responsive layout.
 *
 * Pure presentation: fixed-width registry rail on the left (always visible,
 * never collapsible, never reordered) and the selected system's workspace
 * filling the remaining width. No clinical logic lives here — see
 * SNS_CLINICAL_WORKSPACE_STANDARD.md / SNS_BROWSER_WIDTH_VALIDATION_STANDARD.md
 * for the readability/no-wasted-space rules this layout follows.
 */
import * as React from "react";

export interface ResponsiveDesktopLayoutProps {
  registry: React.ReactNode;
  header: React.ReactNode;
  content: React.ReactNode;
}

export function ResponsiveDesktopLayout({ registry, header, content }: ResponsiveDesktopLayoutProps) {
  return (
    <div className="flex h-full w-full min-w-0 flex-col bg-rnica-bg text-rnica-text">
      <div className="shrink-0 border-b border-rnica-border px-4 py-3">{header}</div>
      <div className="flex min-h-0 flex-1 min-w-0">
        <nav
          aria-label="Body systems registry"
          className="w-[260px] shrink-0 overflow-y-auto border-r border-rnica-border px-2 py-3"
        >
          {registry}
        </nav>
        <main className="min-w-0 flex-1 overflow-y-auto px-4 py-4">{content}</main>
      </div>
    </div>
  );
}
