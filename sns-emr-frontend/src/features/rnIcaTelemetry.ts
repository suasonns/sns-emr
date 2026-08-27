export type RnIcaTelemetryEvent =
  | { name: "density_changed"; density: "compact" | "comfortable" | "large" }
  | { name: "section_jump"; section: string; source: "navigator" | "quick_capture" | "requirement" | "next" | "previous" }
  | { name: "section_find"; elapsedMs: number; resultCount: number }
  | { name: "workspace_scroll"; region: "navigator" | "detail" | "rail"; depthBucket: 0 | 25 | 50 | 75 | 100 }
  | { name: "completion_viewed"; completed: number; total: number };

export type RnIcaTelemetrySink = (event: RnIcaTelemetryEvent) => void;

let telemetrySink: RnIcaTelemetrySink | null = null;

export function registerRnIcaTelemetrySink(sink: RnIcaTelemetrySink | null): void {
  telemetrySink = sink;
}

export function emitRnIcaTelemetry(event: RnIcaTelemetryEvent): void {
  telemetrySink?.(event);
  window.dispatchEvent(new CustomEvent("sns:rnica-pilot-telemetry", { detail: event }));
}
