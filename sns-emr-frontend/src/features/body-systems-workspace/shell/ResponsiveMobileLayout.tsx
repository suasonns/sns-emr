/**
 * SNS Body Systems Workspace — mobile responsive layout.
 *
 * Pure presentation: the fixed ten-system registry renders as a horizontally
 * scrollable strip above the selected system's workspace, instead of a
 * side rail. Same registry, same fixed order, same content — only the
 * placement changes, per SNS_BROWSER_WIDTH_VALIDATION_STANDARD.md (iPad /
 * iPhone viewports) and SNS_CLINICAL_WORKSPACE_STANDARD.md.
 */
import * as React from "react";

export interface ResponsiveMobileLayoutProps {
  registry: React.ReactNode;
  header: React.ReactNode;
  content: React.ReactNode;
}

export function ResponsiveMobileLayout({ registry, header, content }: ResponsiveMobileLayoutProps) {
  return (
    <div className="flex h-full w-full min-w-0 flex-col bg-rnica-bg text-rnica-text">
      <div className="shrink-0 border-b border-rnica-border px-3 py-2">{header}</div>
      <nav
        aria-label="Body systems registry"
        className="flex shrink-0 gap-2 overflow-x-auto border-b border-rnica-border px-2 py-2"
      >
        {registry}
      </nav>
      <main className="min-w-0 flex-1 overflow-y-auto px-3 py-3">{content}</main>
    </div>
  );
}
