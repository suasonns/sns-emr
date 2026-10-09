/**
 * SNS Body Systems Workspace — AI suggestion shell (CONTAINER ONLY).
 *
 * AI remains a future capability. This component has no extraction logic,
 * no inference engine, and no persistence. It only renders whatever
 * suggestions are passed in (empty by default in Phase 1) with
 * Accept / Edit / Reject placeholder actions. Per the domain ownership
 * registry's `aiSuggestionsDoNotMarkSystemReviewed` rule, accepting a
 * suggestion here only changes its own local disposition — it never marks
 * a system reviewed and never calls out to the assessment state machine.
 */
import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import type { AISuggestion } from "../../../domain/body-systems";

export interface AISuggestionShellProps {
  suggestions: AISuggestion[];
  onDispositionChange?: (suggestionId: string, disposition: AISuggestion["disposition"]) => void;
}

export function AISuggestionShell({ suggestions, onDispositionChange }: AISuggestionShellProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI suggestions</CardTitle>
        <Badge variant="ai">Future capability</Badge>
      </CardHeader>
      <CardContent>
        {suggestions.length === 0 ? (
          <p className="text-[12px] text-rnica-muted">
            No AI suggestions in Phase 1. This container is a shell for a future extraction engine; suggestions will
            always require nurse accept/edit/reject and can never become authoritative on their own.
          </p>
        ) : (
          <ul className="flex flex-col gap-2">
            {suggestions.map((suggestion) => (
              <li key={suggestion.id} className="rounded-lg border border-rnica-borderAI p-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[12px] font-medium text-rnica-textStrong">{suggestion.targetFieldPath}</span>
                  {suggestion.confidence && <Badge variant="ai">{suggestion.confidence} confidence</Badge>}
                </div>
                <p className="mt-1 text-[12px] text-rnica-muted">{suggestion.sourceExcerpt}</p>
                <div className="mt-2 flex gap-2">
                  <Button size="sm" onClick={() => onDispositionChange?.(suggestion.id, "accepted")}>
                    Accept
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => onDispositionChange?.(suggestion.id, "edited")}>
                    Edit
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => onDispositionChange?.(suggestion.id, "rejected")}>
                    Reject
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
