import React from "react";
import {
  BookOpen,
  FileText,
  Activity,
  TrendingDown,
  Users,
  AlertTriangle,
  Settings2,
  RefreshCw,
  ArrowRight,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import { notYetDocumented } from "../design-system/RnicaDesignSystem";
import "../design-system/RnicaTailwind.css";

// Screen 1 -- Patient Story, rebuilt with shadcn/ui primitives (Card, Badge,
// Button) to match the approved Figma reference pixel-for-pixel (see
// rnica-figma-reference/light/patient-story.png and
// dark/v3.2-10screen/patient-story.png in the session files). All content
// is still 100% sourced from the same real `patient`/`intelligence`/
// validation props PatientStoryPanel already computed -- this file only
// changes presentation, not data. Colors are the "rnica-*" Tailwind classes
// wired to the real --sns-* theme tokens (tailwind.config.js), so both
// light and dark render from the same one live theme, not a hardcoded copy.

const RISK_TONE = {
  critical: { label: "High Risk", variant: "red", dot: "bg-rnica-red" },
  warning: { label: "Moderate Risk", variant: "orange", dot: "bg-rnica-orange" },
  info: { label: "Monitor", variant: "teal", dot: "bg-rnica-teal" },
};

function Fact({ label, value }) {
  return (
    <div className="flex flex-col gap-0.5 min-w-0">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-rnica-dim">{label}</span>
      <span className="text-sm font-bold text-rnica-text truncate">
        {notYetDocumented(value) ? <span className="text-rnica-dim font-medium normal-case">Not yet documented</span> : value}
      </span>
    </div>
  );
}

function NarrativeOrEmpty({ text, source, onNavigateToSource }) {
  if (notYetDocumented(text)) {
    return (
      <div className="flex flex-col items-start gap-2 rounded-lg border border-dashed border-rnica-border bg-rnica-bgAlt px-3.5 py-3">
        <span className="text-rnica-dim text-sm font-medium">NOT YET DOCUMENTED</span>
        {source && (
          <button type="button" onClick={onNavigateToSource} className="bg-transparent text-xs font-semibold text-rnica-teal hover:underline">
            Add in {source}
          </button>
        )}
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm leading-relaxed text-rnica-text">{text}</p>
      {source && (
        <button type="button" onClick={onNavigateToSource} className="bg-transparent self-start text-xs font-semibold text-rnica-teal hover:underline">
          View source: {source}
        </button>
      )}
    </div>
  );
}

export default function PatientStoryShadcn({
  patient,
  intelligence,
  findings,
  recommendations,
  missingItems,
  documentedRiskRows,
  caregiver,
  caregiverSummary,
  functionalDecline,
  onNavigate,
}) {
  return (
    <div className="flex flex-col gap-5" aria-labelledby="patient-story-title">
      <p id="patient-story-title" className="sr-only">Patient Story</p>

      {/* Patient identity + facts row -- keeps the RnicaPatientHeader gradient
          + teal accent border from the original design system */}
      <Card className="border-l-4 border-l-rnica-teal bg-[linear-gradient(135deg,var(--sns-cardSoft)_0%,var(--sns-card)_65%)]">
        <CardContent className="py-4 flex flex-col gap-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-extrabold text-rnica-text tracking-tight">{patient.name || "Unnamed patient"}</h1>
              {patient.age && (
                <span className="rounded bg-rnica-bgAlt border border-rnica-border px-2 py-0.5 text-xs font-semibold text-rnica-muted">
                  {patient.age}{(patient.sex || "").slice(0, 1).toUpperCase()}
                </span>
              )}
            </div>
            {!notYetDocumented(patient.assessmentStage) && (
              <Badge variant="orange">{patient.assessmentStage}</Badge>
            )}
          </div>
          <div className="grid gap-4 pt-3 border-t border-rnica-border" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))" }}>
            <Fact label="MRN Number" value={patient.mrn} />
            <Fact label="Primary Diagnosis" value={patient.primaryDiagnosis} />
            <Fact label="Hospice Admission" value={patient.admissionDate} />
            <Fact label="Attending Physician" value={patient.attendingPhysician} />
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-rnica-dim">Current PPS</span>
              {notYetDocumented(patient.currentPps) ? (
                <span className="text-sm font-medium text-rnica-dim">Not yet documented</span>
              ) : (
                <span className="flex items-center gap-1.5 text-sm font-bold text-rnica-text">
                  <span className="inline-block h-2 w-2 rounded-full bg-rnica-orange" aria-hidden="true" />
                  {patient.currentPps}
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <p className="text-sm text-rnica-muted max-w-[62ch]">
        This is a read-only summary of information already documented elsewhere in RNICA. It does
        not store data and is not a certification, eligibility, or prognosis determination.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)] gap-5 items-start">
        {/* Main column */}
        <div className="flex flex-col gap-4 min-w-0">
          <Card>
            <CardHeader>
              <CardTitle><BookOpen className="h-4 w-4 text-rnica-teal" /> Why Hospice</CardTitle>
            </CardHeader>
            <CardContent>
              <NarrativeOrEmpty text={patient.whyHospiceNarrative} source="Diagnosis & LCD" onNavigateToSource={() => onNavigate("diagnoses")} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle><FileText className="h-4 w-4 text-rnica-teal" /> Recent Hospitalization</CardTitle>
            </CardHeader>
            <CardContent>
              <NarrativeOrEmpty text={patient.recentHospitalization} source="Diagnosis & LCD" onNavigateToSource={() => onNavigate("diagnoses")} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle><Activity className="h-4 w-4 text-rnica-teal" /> Current Clinical Concerns</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2.5">
              {documentedRiskRows.length === 0 && (
                <p className="text-sm text-rnica-muted">No documented clinical concerns currently flagged across Safety, Pain, Psychosocial, or Caregiver screens.</p>
              )}
              {documentedRiskRows.map((row) => {
                const tone = RISK_TONE[row.tone] || RISK_TONE.info;
                return (
                  <div key={row.moduleKey} className="flex items-start justify-between gap-3 rounded-lg border border-rnica-border bg-rnica-bgAlt px-3.5 py-3">
                    <div className="flex items-start gap-2.5 min-w-0">
                      <span className={`mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full ${tone.dot}`} aria-hidden="true" />
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-rnica-text">{row.label}</p>
                        <p className="text-xs text-rnica-muted">{row.detail}</p>
                      </div>
                    </div>
                    <Badge variant={tone.variant} className="shrink-0">{tone.label}</Badge>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle><TrendingDown className="h-4 w-4 text-rnica-teal" /> Functional Decline</CardTitle>
            </CardHeader>
            <CardContent>
              <NarrativeOrEmpty text={functionalDecline} source="Functional Status" onNavigateToSource={() => onNavigate("performanceStatus")} />
            </CardContent>
          </Card>
        </div>

        {/* Rail */}
        <div className="flex flex-col gap-4 min-w-0">
          <Card className="border-rnica-teal shadow-[0_0_0_1px_var(--sns-teal)]">
            <CardHeader>
              <CardTitle className="text-rnica-teal"><Settings2 className="h-4 w-4" /> RNICA Intelligence</CardTitle>
              <button type="button" className="bg-transparent flex items-center gap-1 text-xs font-semibold text-rnica-teal hover:underline">
                <RefreshCw className="h-3 w-3" /> Refresh
              </button>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {!intelligence && <p className="text-sm text-rnica-muted">Save the assessment to generate the clinical signal summary.</p>}
              {intelligence && findings.length === 0 && recommendations.length === 0 && (
                <p className="text-sm text-rnica-muted">No current findings or recommendations.</p>
              )}
              {findings.slice(0, 5).map((finding, index) => (
                <button
                  type="button"
                  key={`story-finding-${index}`}
                  onClick={() => onNavigate("finalization")}
                  className="bg-transparent text-left text-sm text-rnica-text hover:text-rnica-teal"
                >
                  <strong>{finding.title}</strong>{finding.details ? ` \u2014 ${finding.details}` : ""}
                </button>
              ))}
              {recommendations.slice(0, 3).map((rec, index) => (
                <p key={`story-rec-${index}`} className="text-sm text-rnica-text">{typeof rec === "string" ? rec : rec?.text || rec?.title}</p>
              ))}
            </CardContent>
          </Card>

          {missingItems.length > 0 && (
            <Card className="border-rnica-orange">
              <CardHeader>
                <CardTitle className="text-rnica-orange"><AlertTriangle className="h-4 w-4" /> Missing Information</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {missingItems.map((item) => (
                  <button
                    type="button"
                    key={item.key}
                    onClick={() => onNavigate(item.route || "finalization")}
                    className="bg-transparent flex items-start gap-2 text-left text-sm text-rnica-text hover:text-rnica-orange"
                  >
                    <span className="mt-1 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-rnica-orange" aria-hidden="true" />
                    {item.label}
                  </button>
                ))}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle><Users className="h-4 w-4 text-rnica-teal" /> Caregiver Overview</CardTitle>
            </CardHeader>
            <CardContent>
              {notYetDocumented(caregiverSummary) ? (
                <div className="flex flex-col items-start gap-2 rounded-lg border border-dashed border-rnica-border bg-rnica-bgAlt px-3.5 py-3">
                  <span className="text-rnica-dim text-sm font-medium">NOT YET DOCUMENTED</span>
                  <button type="button" onClick={() => onNavigate("caregiverAssessment")} className="bg-transparent text-xs font-semibold text-rnica-teal hover:underline">
                    Add in Caregiver & Support
                  </button>
                </div>
              ) : (
                <div className="flex flex-col gap-1.5">
                  <button type="button" onClick={() => onNavigate("caregiverAssessment")} className="bg-transparent self-start text-sm font-semibold text-rnica-teal hover:underline">
                    {caregiverSummary}
                  </button>
                  {caregiver.anxietyLevel && <p className="text-xs text-rnica-muted">Anxiety level: {caregiver.anxietyLevel}</p>}
                  {caregiver.willingToProvideCare === false && (
                    <Badge variant="orange" className="self-start">Not willing to provide care</Badge>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          <Button onClick={() => onNavigate("demographics")} className="w-full justify-between h-auto py-3 px-4">
            <span className="flex flex-col items-start gap-0.5 text-left normal-case">
              <span className="text-sm font-bold">Continue to Evidence & Intake</span>
              <span className="text-xs font-normal opacity-80">Review available intake docs next</span>
            </span>
            <ArrowRight className="h-4 w-4 shrink-0" />
          </Button>
        </div>
      </div>
    </div>
  );
}
