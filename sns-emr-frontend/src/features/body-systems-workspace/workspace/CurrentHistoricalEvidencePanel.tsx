/**
 * SNS Body Systems Workspace — Current vs Historical Evidence display.
 *
 * Display only; no duplicate assessment logic lives here. Historical
 * evidence always renders dated/sourced/historical, and is never silently
 * promoted into current evidence — there is no "copy to current" action in
 * this component. Blank current evidence is rendered as an explicit
 * "not yet reviewed" state, never as an implied-normal blank area
 * (per the spec's "blank is not normal" rule).
 */
import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Badge } from "../../../components/ui/badge";
import type { Evidence } from "../../../domain/body-systems";

export interface CurrentHistoricalEvidencePanelProps {
  currentEvidence: Evidence[];
  historicalEvidence: Evidence[];
  requiresExplicitCurrentReview: boolean;
}

function EvidenceRow({ evidence }: { evidence: Evidence }) {
  return (
    <li className="flex flex-col gap-0.5 rounded-md border border-rnica-border px-2.5 py-2 text-[12px]">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-rnica-textStrong">{evidence.sourceType.replaceAll("_", " ")}</span>
        <Badge variant={evidence.status === "current" ? "teal" : "neutral"}>{evidence.status}</Badge>
      </div>
      {evidence.excerpt && <p className="text-rnica-muted">{evidence.excerpt}</p>}
      <span className="text-[10px] text-rnica-dim">
        {evidence.sourceDateTime ? new Date(evidence.sourceDateTime).toLocaleString() : "No date/time recorded"}
      </span>
    </li>
  );
}

export function CurrentHistoricalEvidencePanel({
  currentEvidence,
  historicalEvidence,
  requiresExplicitCurrentReview,
}: CurrentHistoricalEvidencePanelProps) {
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Current evidence</CardTitle>
          <Badge variant={currentEvidence.length > 0 ? "success" : "warning"}>
            {currentEvidence.length > 0 ? "Reviewed this visit" : "Not yet reviewed"}
          </Badge>
        </CardHeader>
        <CardContent>
          {currentEvidence.length === 0 ? (
            <p className="text-[12px] text-rnica-muted">
              {requiresExplicitCurrentReview
                ? "No current evidence has been entered yet. This system requires an explicit current review — a blank field is never treated as normal."
                : "No current evidence entered."}
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {currentEvidence.map((evidence) => (
                <EvidenceRow key={evidence.id} evidence={evidence} />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Historical evidence</CardTitle>
          <Badge variant="neutral">Read-only</Badge>
        </CardHeader>
        <CardContent>
          {historicalEvidence.length === 0 ? (
            <p className="text-[12px] text-rnica-muted">No historical evidence on file.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {historicalEvidence.map((evidence) => (
                <EvidenceRow key={evidence.id} evidence={evidence} />
              ))}
            </ul>
          )}
          <p className="mt-2 text-[10px] text-rnica-dim">
            Historical findings remain historical. They never become current evidence automatically.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
