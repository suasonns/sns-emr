import { useEffect, useMemo, useState } from "react";
import { Alert, Box, CircularProgress, LinearProgress, Paper, Typography } from "@mui/material";

import {
  fetchTenantBillingReadinessReport,
  fetchClaimLifecycle,
  type TenantBillingReadinessReport,
  type ClaimLifecycleResponse,
} from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

// Mirrors app.billing.services.billing_readiness_service.categorize_blocker
// so the "Blocker Breakdown" panel below rolls up the same raw blocker
// strings the backend returns into the same named categories, without a
// dedicated aggregation endpoint. Keep this list in sync with that module's
// BLOCKER_CATEGORY_PREFIXES if it changes.
const BLOCKER_CATEGORY_PREFIXES: Array<[string, string]> = [
  ["Patient status is", "Patient Not Active"],
  ["No benefit period covers", "Missing Benefit Period"],
  ["Hospice election statement is not signed", "Missing Election Statement"],
  ["Notice of Election (NOE) has not been filed", "Missing NOE Filing"],
  ["Certification of Terminal Illness", "Missing Certification"],
  ["Required face-to-face encounter", "Missing F2F Documentation"],
  ["Plan of Care is not active", "Missing POC Physician Signature"],
  ["Payer sequence is ambiguous", "Payer/MSP Sequencing Issue"],
  ["Patient not found", "Patient Not Found"],
];

function categorizeBlocker(blocker: string): string {
  const match = BLOCKER_CATEGORY_PREFIXES.find(([prefix]) => blocker.startsWith(prefix));
  return match ? match[1] : "Other";
}

const CATEGORY_COLOR: Record<string, string> = {
  "Missing F2F Documentation": "#f87171",
  "Missing Benefit Period": "#fbbf24",
  "Missing NOE Filing": "#fb923c",
  "Missing Certification": "#facc15",
  "Missing Election Statement": "#a78bfa",
  "Missing POC Physician Signature": "#38bdf8",
  "Payer/MSP Sequencing Issue": "#f472b6",
  "Patient Not Active": "#94a3b8",
  "Patient Not Found": "#94a3b8",
  Other: "#94a3b8",
};

export default function BillingOverviewPage() {
  const { selectedAgencyId, agencies } = useAgency();
  const [readiness, setReadiness] = useState<TenantBillingReadinessReport | null>(null);
  const [lifecycle, setLifecycle] = useState<ClaimLifecycleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const agencyName =
    agencies.find((a) => a.tenant_id === selectedAgencyId)?.display_name ||
    agencies.find((a) => a.tenant_id === selectedAgencyId)?.legal_name ||
    "the selected agency";

  useEffect(() => {
    if (!selectedAgencyId) {
      setLoading(false);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    Promise.allSettled([
      fetchTenantBillingReadinessReport(selectedAgencyId),
      fetchClaimLifecycle(selectedAgencyId),
    ]).then(([readinessRes, lifecycleRes]) => {
      if (!isMounted) return;
      if (readinessRes.status === "fulfilled") {
        setReadiness(readinessRes.value);
      } else {
        setError(readinessRes.reason?.message || "Unable to load billing readiness.");
      }
      setLifecycle(lifecycleRes.status === "fulfilled" ? lifecycleRes.value : null);
      setLoading(false);
    });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  const blockerBreakdown = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const patient of readiness?.patients ?? []) {
      for (const blocker of patient.blockers) {
        const category = categorizeBlocker(blocker);
        counts[category] = (counts[category] || 0) + 1;
      }
    }
    return Object.entries(counts)
      .map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count);
  }, [readiness]);

  const maxBlockerCount = Math.max(1, ...blockerBreakdown.map((b) => b.count));

  const cleanClaimRate =
    lifecycle && lifecycle.accepted + lifecycle.denied > 0
      ? Math.round((lifecycle.accepted / (lifecycle.accepted + lifecycle.denied)) * 1000) / 10
      : null;

  const metrics = [
    { label: "Total Patients", value: String(readiness?.total_patients ?? 0), caption: "Active census this cycle" },
    {
      label: "Ready to Bill",
      value: String(readiness?.ready_count ?? 0),
      caption:
        readiness && readiness.total_patients > 0
          ? `${Math.round(((readiness.ready_count ?? 0) / readiness.total_patients) * 100)}% of active patient files cleared`
          : "No active patients found",
      color: "#4ade80",
    },
    {
      label: "Blockers Outstanding",
      value: String(readiness?.not_ready_count ?? 0),
      caption:
        readiness && readiness.total_patients > 0
          ? `${Math.round(((readiness.not_ready_count ?? 0) / readiness.total_patients) * 100)}% of files contain status flags`
          : "—",
      color: (readiness?.not_ready_count ?? 0) > 0 ? "#f87171" : "#4ade80",
    },
    {
      label: "Clean Claim Rate",
      value: cleanClaimRate !== null ? `${cleanClaimRate}%` : "—",
      caption: cleanClaimRate !== null ? "Accepted vs. accepted + denied" : "No claim lifecycle data yet",
      color: cleanClaimRate === null ? "#94a3b8" : cleanClaimRate >= 90 ? "#4ade80" : "#fbbf24",
    },
  ];

  const batchStages = [
    { label: "Draft Batching", value: lifecycle?.ready ?? 0, caption: "Pre-audit verification in progress" },
    { label: "Submitted to Clearinghouse", value: lifecycle?.sent ?? 0, caption: "Awaiting Electronic Remittance advice" },
    { label: "Accepted & Validated", value: lifecycle?.accepted ?? 0, caption: "Validated with no current exception alerts" },
    { label: "Paid / Remitted", value: lifecycle?.paid ?? 0, caption: "Successfully posted this fiscal quarter" },
  ];

  return (
    <Box>
      <PageHeader
        title="Billing Dashboard"
        subtitle={`Billing readiness and clearinghouse preprocessing overview for ${agencyName}`}
      />
      <HipaaBanner />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its billing dashboard.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics} />

          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2, mb: 2.5, alignItems: "flex-start" }}>
            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", mb: 1.5 }}>
                BLOCKER BREAKDOWN BY UNRESOLVED FLAG
              </Typography>
              {blockerBreakdown.length === 0 ? (
                <Typography sx={{ fontSize: 12.5, color: "#4ade80" }}>
                  No unresolved billing blockers for this agency.
                </Typography>
              ) : (
                blockerBreakdown.map((b) => (
                  <Box key={b.category} sx={{ mb: 1.3 }}>
                    <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.3 }}>
                      <Typography sx={{ fontSize: 12.5, color: "#e2e8f0" }}>{b.category}</Typography>
                      <Typography sx={{ fontSize: 12.5, color: "#e2e8f0", fontWeight: 700 }}>
                        {b.count} Patient{b.count === 1 ? "" : "s"}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(b.count / maxBlockerCount) * 100}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        bgcolor: "#1f3a5c",
                        "& .MuiLinearProgress-bar": { bgcolor: CATEGORY_COLOR[b.category] || "#94a3b8" },
                      }}
                    />
                  </Box>
                ))
              )}
            </Paper>

            <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
              <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", mb: 0.3 }}>
                CLAIMS LIFECYCLE SNAPSHOT ({agencyName})
              </Typography>
              <Typography sx={{ fontSize: 10.5, color: "#7f97b3", mb: 1.5 }}>
                Replaces the Figma reference's cross-agency comparison panel, which requires an
                owner-only rollup this billing-role dashboard doesn't have access to -- see
                docs/design/biller-dashboard-figma/README.md.
              </Typography>
              {!lifecycle ? (
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>No claim lifecycle data available.</Typography>
              ) : (
                (["ready", "sent", "accepted", "paid", "denied"] as const).map((key) => (
                  <Box key={key} sx={{ display: "flex", justifyContent: "space-between", py: 0.6, borderBottom: "1px solid #1f3a5c" }}>
                    <Typography sx={{ fontSize: 12.5, color: "#cbd5e1", textTransform: "capitalize" }}>{key}</Typography>
                    <Typography sx={{ fontSize: 12.5, color: key === "denied" ? "#f87171" : "#e2e8f0", fontWeight: 700 }}>
                      {lifecycle[key]}
                    </Typography>
                  </Box>
                ))
              )}
            </Paper>
          </Box>

          <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", mb: 1 }}>
            ACTIVE BILLING BATCH LIFECYCLE STAGES ({agencyName})
          </Typography>
          <Box sx={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 2 }}>
            {batchStages.map((stage) => (
              <Paper key={stage.label} sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2 }}>
                <Typography sx={{ fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3" }}>
                  {stage.label.toUpperCase()}
                </Typography>
                <Typography sx={{ fontSize: 22, fontWeight: 800, color: "#fff" }}>{stage.value} Claims</Typography>
                <Typography sx={{ fontSize: 11, color: "#7f97b3" }}>{stage.caption}</Typography>
              </Paper>
            ))}
          </Box>
        </>
      )}
    </Box>
  );
}
