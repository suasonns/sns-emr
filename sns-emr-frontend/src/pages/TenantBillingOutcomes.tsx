import { useEffect, useMemo, useState, type CSSProperties } from "react";

import { getCurrentUser } from "../api/session";
import {
  fetchBillableAgencies,
  fetchBillingQueue,
  fetchClaimLifecycle,
  fetchClaims,
  fetchDenials,
  fetchDenialsAppealsSummary,
  fetchNoeTracking,
  fetchRemittances,
  fetchTenantBillingReadinessReport,
  type BillableAgency,
  type BillingQueueRow,
  type ClaimLifecycleResponse,
  type ClaimsResponse,
  type DenialsAppealsSummaryResponse,
  type DenialsResponse,
  type NoeTrackingResponse,
  type RemittancesResponse,
  type TenantBillingReadinessReport,
} from "../api/dashboard";

const C = {
  navy: "#1f4a78",
  teal: "#10b7a2",
  green: "#059669",
  amber: "#f59e0b",
  red: "#dc2626",
  blue: "#2563eb",
  white: "#ffffff",
  gray100: "#f3f4f6",
  gray200: "#e5e7eb",
  gray600: "#4b5563",
  gray800: "#1f2937",
  slate500: "#64748b",
};

const cardStyle: CSSProperties = {
  backgroundColor: C.white,
  borderRadius: 12,
  boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  padding: 24,
};

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

function EmptyNoticeCard({ title, description }: { title: string; description: string }) {
  return (
    <div style={{ ...cardStyle, border: `1px dashed ${C.gray200}`, boxShadow: "none" }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>{title}</div>
      <div style={{ marginTop: 8, fontSize: 13, color: C.slate500 }}>{description}</div>
    </div>
  );
}

function formatInteger(value: number | null | undefined) {
  return (value ?? 0).toLocaleString();
}

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(1)}%`;
}

function statCard(label: string, value: string, subtext: string, color: string) {
  return (
    <div style={{ ...cardStyle, borderTop: `3px solid ${color}`, padding: 20 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: C.slate500, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 800, color }}>{value}</div>
      <div style={{ fontSize: 12, color: C.gray600, marginTop: 6 }}>{subtext}</div>
    </div>
  );
}

type BillingOutcomeState = {
  agencies: BillableAgency[];
  agenciesError: string | null;
  loading: boolean;
  sourceErrors: string[];
  readiness: TenantBillingReadinessReport | null;
  lifecycle: ClaimLifecycleResponse | null;
  claims: ClaimsResponse | null;
  denials: DenialsResponse | null;
  denialsSummary: DenialsAppealsSummaryResponse | null;
  remittances: RemittancesResponse | null;
  noe: NoeTrackingResponse | null;
  queue: BillingQueueRow[] | null;
};

const initialState: BillingOutcomeState = {
  agencies: [],
  agenciesError: null,
  loading: true,
  sourceErrors: [],
  readiness: null,
  lifecycle: null,
  claims: null,
  denials: null,
  denialsSummary: null,
  remittances: null,
  noe: null,
  queue: null,
};

export default function TenantBillingOutcomes() {
  const currentUser = getCurrentUser();
  const isBillingScope = currentUser?.access_scope === "billing";
  const [state, setState] = useState<BillingOutcomeState>(initialState);
  const [selectedTenantId, setSelectedTenantId] = useState<string>(() => {
    if (currentUser?.access_scope === "billing") {
      return localStorage.getItem("sns-analytics-billing-tenant") || "";
    }
    return currentUser?.tenant_id || "";
  });

  useEffect(() => {
    if (!isBillingScope) return;
    let mounted = true;
    fetchBillableAgencies()
      .then((res) => {
        if (!mounted) return;
        const agencies = res?.agencies ?? [];
        setState((previous) => ({ ...previous, agencies, agenciesError: null }));
        setSelectedTenantId((current) => {
          if (current && agencies.some((agency) => agency.tenant_id === current)) return current;
          return agencies[0]?.tenant_id ?? "";
        });
      })
      .catch((error) => {
        if (!mounted) return;
        setState((previous) => ({
          ...previous,
          agenciesError: error?.message || "Unable to load agency selector.",
        }));
      });
    return () => {
      mounted = false;
    };
  }, [isBillingScope]);

  useEffect(() => {
    if (isBillingScope && selectedTenantId) {
      localStorage.setItem("sns-analytics-billing-tenant", selectedTenantId);
    }
  }, [isBillingScope, selectedTenantId]);

  useEffect(() => {
    const effectiveTenantId = isBillingScope ? selectedTenantId : currentUser?.tenant_id;
    if (!effectiveTenantId) {
      setState((previous) => ({ ...previous, loading: false }));
      return;
    }

    let mounted = true;
    setState((previous) => ({ ...previous, loading: true, sourceErrors: [] }));

    Promise.allSettled([
      fetchTenantBillingReadinessReport(effectiveTenantId),
      fetchClaimLifecycle(effectiveTenantId),
      fetchClaims(effectiveTenantId, { limit: 1000 }),
      fetchDenials(effectiveTenantId, { limit: 500 }),
      fetchDenialsAppealsSummary(effectiveTenantId),
      fetchRemittances(effectiveTenantId, { limit: 500 }),
      fetchNoeTracking(effectiveTenantId, { limit: 500 }),
      fetchBillingQueue(effectiveTenantId),
    ]).then((results) => {
      if (!mounted) return;
      const sourceErrors = results
        .filter((result): result is PromiseRejectedResult => result.status === "rejected")
        .map((result) => result.reason?.message || "One billing source could not be loaded.");

      setState((previous) => ({
        ...previous,
        loading: false,
        sourceErrors,
        readiness: results[0].status === "fulfilled" ? results[0].value : null,
        lifecycle: results[1].status === "fulfilled" ? results[1].value : null,
        claims: results[2].status === "fulfilled" ? results[2].value : null,
        denials: results[3].status === "fulfilled" ? results[3].value : null,
        denialsSummary: results[4].status === "fulfilled" ? results[4].value : null,
        remittances: results[5].status === "fulfilled" ? results[5].value : null,
        noe: results[6].status === "fulfilled" ? results[6].value : null,
        queue: results[7].status === "fulfilled" ? results[7].value : null,
      }));
    });

    return () => {
      mounted = false;
    };
  }, [currentUser?.tenant_id, isBillingScope, selectedTenantId]);

  const selectedAgency = useMemo(() => {
    if (!isBillingScope) {
      return {
        tenant_id: currentUser?.tenant_id ?? "",
        display_name: currentUser?.tenant_name ?? "Current tenant",
        legal_name: currentUser?.tenant_name ?? "Current tenant",
      };
    }
    return state.agencies.find((agency) => agency.tenant_id === selectedTenantId) ?? null;
  }, [currentUser?.tenant_id, currentUser?.tenant_name, isBillingScope, selectedTenantId, state.agencies]);

  const blockerBreakdown = useMemo(() => {
    const counts = new Map<string, number>();
    for (const patient of state.readiness?.patients ?? []) {
      for (const blocker of patient.blockers) {
        const category = categorizeBlocker(blocker);
        counts.set(category, (counts.get(category) ?? 0) + 1);
      }
    }
    return [...counts.entries()]
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value || a.label.localeCompare(b.label));
  }, [state.readiness]);

  const queueTotals = useMemo(() => {
    const rows = state.queue ?? [];
    const billedAmount = rows.reduce((sum, row) => sum + (row.total_charge ?? 0), 0);
    const cycles = new Map<string, { cycleId: string; claimCount: number; generatedAmount: number }>();
    rows.forEach((row) => {
      const key = row.billing_cycle_id;
      if (!cycles.has(key)) {
        cycles.set(key, { cycleId: key, claimCount: 0, generatedAmount: 0 });
      }
      const current = cycles.get(key)!;
      current.claimCount += 1;
      current.generatedAmount += row.total_charge ?? 0;
    });
    return {
      billedAmount,
      cycles: [...cycles.values()].sort((a, b) => b.generatedAmount - a.generatedAmount),
    };
  }, [state.queue]);

  const collectionSummary = useMemo(() => {
    const collectedAmount =
      state.remittances?.payer_breakdown?.reduce((sum, payer) => sum + (payer.total_paid ?? 0), 0) ??
      state.remittances?.remittances?.reduce((sum, era) => sum + (era.total_paid_amount ?? 0), 0) ??
      0;
    const billedAmount = queueTotals.billedAmount;
    return {
      billedAmount,
      collectedAmount,
      rate: billedAmount > 0 ? (collectedAmount / billedAmount) * 100 : null,
    };
  }, [queueTotals.billedAmount, state.remittances]);

  const denialRate = useMemo(() => {
    const totalClaims = state.claims?.total_claims ?? 0;
    if (!totalClaims) return null;
    return ((state.claims?.denied_count ?? 0) / totalClaims) * 100;
  }, [state.claims]);

  const noeSummary = useMemo(() => {
    const rows = state.noe?.noe_tracking ?? [];
    let onTime = 0;
    let late = 0;
    let unfiled = 0;
    let exempt = 0;
    rows.forEach((row) => {
      if (row.is_exempt) {
        exempt += 1;
        return;
      }
      if (!row.noe_filed) {
        unfiled += 1;
        return;
      }
      if (row.is_late) {
        late += 1;
      } else {
        onTime += 1;
      }
    });
    const filedCount = onTime + late;
    return {
      onTime,
      late,
      unfiled,
      exempt,
      rate: filedCount > 0 ? (onTime / filedCount) * 100 : null,
    };
  }, [state.noe]);

  const tenantName =
    selectedAgency?.display_name ||
    selectedAgency?.legal_name ||
    currentUser?.tenant_name ||
    "selected tenant";

  return (
    <div style={{ padding: "24px 24px 40px", display: "grid", gap: 20 }}>
      <div style={{ ...cardStyle, display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 16, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: C.teal, letterSpacing: 0.5, textTransform: "uppercase" }}>
            Tenant billing analytics
          </div>
          <div style={{ marginTop: 6, fontSize: 24, fontWeight: 800, color: C.navy }}>
            Billing outcomes mirror
          </div>
          <div style={{ marginTop: 8, fontSize: 13, color: C.gray600, maxWidth: 720 }}>
            Mirrors the real readiness, claims, denials, remittance, and NOE outcomes already used on the Biller Dashboard,
            without exposing biller-only posting or EDI worklists.
          </div>
        </div>
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.slate500, textTransform: "uppercase", marginBottom: 6 }}>
            Viewing tenant
          </div>
          {isBillingScope ? (
            <select
              value={selectedTenantId}
              onChange={(event) => setSelectedTenantId(event.target.value)}
              style={{
                minWidth: 280,
                borderRadius: 8,
                border: `1px solid ${C.gray200}`,
                padding: "10px 12px",
                fontSize: 13,
                fontWeight: 600,
                color: C.gray800,
                backgroundColor: C.white,
              }}
            >
              {state.agencies.map((agency) => (
                <option key={agency.tenant_id} value={agency.tenant_id}>
                  {agency.display_name || agency.legal_name}
                </option>
              ))}
            </select>
          ) : (
            <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>{tenantName}</div>
          )}
        </div>
      </div>

      {state.agenciesError ? <EmptyNoticeCard title="Tenant selector unavailable" description={state.agenciesError} /> : null}
      {state.sourceErrors.length ? (
        <div style={{ ...cardStyle, padding: 16, borderLeft: `4px solid ${C.amber}`, backgroundColor: "#fffdf7" }}>
          <div style={{ fontSize: 12, fontWeight: 800, color: "#92400e", textTransform: "uppercase", letterSpacing: 0.5 }}>
            Source notice
          </div>
          <ul style={{ margin: "10px 0 0 18px", padding: 0, color: C.gray600, fontSize: 13 }}>
            {state.sourceErrors.map((warning, index) => (
              <li key={`${warning}-${index}`}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {state.loading ? (
        <div style={cardStyle}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>Loading live billing outcomes…</div>
          <div style={{ marginTop: 8, fontSize: 13, color: C.slate500 }}>Pulling the selected tenant's readiness, claims, denials, remittances, and NOE data.</div>
        </div>
      ) : !selectedTenantId ? (
        <EmptyNoticeCard
          title="Select a tenant to view billing outcomes"
          description="Billing-department users must pick one billable agency before the owner-style analytics mirror can load."
        />
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            {statCard(
              "Ready to bill",
              formatInteger(state.readiness?.ready_count),
              `${formatInteger(state.readiness?.total_patients)} active patient files evaluated`,
              C.green
            )}
            {statCard(
              "Claims in lifecycle",
              formatInteger(
                (state.lifecycle?.ready ?? 0) +
                  (state.lifecycle?.sent ?? 0) +
                  (state.lifecycle?.accepted ?? 0) +
                  (state.lifecycle?.denied ?? 0) +
                  (state.lifecycle?.paid ?? 0)
              ),
              "Ready + sent + accepted + denied + paid",
              C.blue
            )}
            {statCard(
              "Denial rate",
              formatPercent(denialRate),
              `${formatInteger(state.denials?.total_denials)} total denials`,
              (state.denials?.total_denials ?? 0) > 0 ? C.red : C.green
            )}
            {statCard(
              "Collection rate",
              formatPercent(collectionSummary.rate),
              `${formatCurrency(collectionSummary.collectedAmount)} collected vs ${formatCurrency(collectionSummary.billedAmount)} billed`,
              C.teal
            )}
            {statCard(
              "NOE on-time filings",
              formatPercent(noeSummary.rate),
              `${formatInteger(noeSummary.onTime)} on time · ${formatInteger(noeSummary.late)} late`,
              noeSummary.late > 0 ? C.amber : C.green
            )}
            {statCard(
              "Open appeals",
              formatInteger(state.denialsSummary?.appealed_denials),
              `${formatCurrency(state.denialsSummary?.open_denied_amount)} still at risk`,
              (state.denialsSummary?.appealed_denials ?? 0) > 0 ? C.amber : C.green
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 20 }}>
            <div style={cardStyle}>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>Billing readiness snapshot</div>
              <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
                {[
                  ["Ready", formatInteger(state.readiness?.ready_count)],
                  ["Not ready", formatInteger(state.readiness?.not_ready_count)],
                  ["Total patients", formatInteger(state.readiness?.total_patients)],
                ].map(([label, value]) => (
                  <div key={label} style={{ display: "flex", justifyContent: "space-between", gap: 16, borderBottom: `1px solid ${C.gray100}`, paddingBottom: 10 }}>
                    <span style={{ fontSize: 13, color: C.gray600 }}>{label}</span>
                    <strong style={{ fontSize: 13, color: C.navy }}>{value}</strong>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16, fontSize: 12, color: C.slate500, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5 }}>
                Blocker breakdown
              </div>
              <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
                {blockerBreakdown.length ? (
                  blockerBreakdown.map((item) => (
                    <div key={item.label} style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
                      <span style={{ fontSize: 13, color: C.gray600 }}>{item.label}</span>
                      <strong style={{ fontSize: 13, color: C.navy }}>{item.value.toLocaleString()}</strong>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: 13, color: C.slate500 }}>No unresolved readiness blockers in the current live report.</div>
                )}
              </div>
            </div>

            <div style={cardStyle}>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>Claims lifecycle mirror</div>
              <div style={{ marginTop: 16, display: "grid", gap: 10 }}>
                {[
                  ["Ready", state.lifecycle?.ready ?? 0],
                  ["Sent", state.lifecycle?.sent ?? 0],
                  ["Accepted", state.lifecycle?.accepted ?? 0],
                  ["Denied", state.lifecycle?.denied ?? 0],
                  ["Paid", state.lifecycle?.paid ?? 0],
                ].map(([label, value]) => (
                  <div key={label} style={{ display: "flex", justifyContent: "space-between", gap: 16, borderBottom: `1px solid ${C.gray100}`, paddingBottom: 10 }}>
                    <span style={{ fontSize: 13, color: C.gray600 }}>{label}</span>
                    <strong style={{ fontSize: 13, color: C.navy }}>{formatInteger(value as number)}</strong>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16, fontSize: 12, color: C.slate500 }}>
                Same lifecycle feed used for the biller's draft/submitted/accepted/denied/paid counts.
              </div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 20 }}>
            <div style={cardStyle}>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>Denials & appeals summary</div>
              <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
                {[
                  ["Total denials", formatInteger(state.denials?.total_denials)],
                  ["Denial rate", formatPercent(denialRate)],
                  ["Open appeals", formatInteger(state.denialsSummary?.appealed_denials)],
                  ["Recovered on appeals", formatCurrency(state.denialsSummary?.total_recovered_amount)],
                ].map(([label, value]) => (
                  <div key={label} style={{ display: "flex", justifyContent: "space-between", gap: 16, borderBottom: `1px solid ${C.gray100}`, paddingBottom: 10 }}>
                    <span style={{ fontSize: 13, color: C.gray600 }}>{label}</span>
                    <strong style={{ fontSize: 13, color: C.navy }}>{value}</strong>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16, fontSize: 12, color: C.slate500, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5 }}>
                Top CARC denial reasons
              </div>
              <div style={{ marginTop: 10, display: "grid", gap: 12 }}>
                {(state.denialsSummary?.top_denial_codes ?? []).length ? (
                  state.denialsSummary!.top_denial_codes.map((row) => (
                    <div key={`${row.carc_code}-${row.reason_description}`} style={{ borderBottom: `1px solid ${C.gray100}`, paddingBottom: 10 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
                        <strong style={{ fontSize: 13, color: C.navy }}>{row.carc_code || "Uncoded"}</strong>
                        <span style={{ fontSize: 12, color: C.gray600 }}>
                          {formatInteger(row.case_count)} denials · {formatCurrency(row.total_amount)}
                        </span>
                      </div>
                      <div style={{ marginTop: 4, fontSize: 12, color: C.gray600 }}>{row.reason_description || "No reason description on file."}</div>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: 13, color: C.slate500 }}>No CARC-coded denials are on file for this tenant.</div>
                )}
              </div>
            </div>

            <div style={cardStyle}>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>Collections mirror</div>
              <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
                {[
                  ["Collected", formatCurrency(collectionSummary.collectedAmount)],
                  ["Billed", formatCurrency(collectionSummary.billedAmount)],
                  ["Collection rate", formatPercent(collectionSummary.rate)],
                  ["ERAs received", formatInteger(state.remittances?.era_received_count)],
                ].map(([label, value]) => (
                  <div key={label} style={{ display: "flex", justifyContent: "space-between", gap: 16, borderBottom: `1px solid ${C.gray100}`, paddingBottom: 10 }}>
                    <span style={{ fontSize: 13, color: C.gray600 }}>{label}</span>
                    <strong style={{ fontSize: 13, color: C.navy }}>{value}</strong>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16, fontSize: 12, color: C.slate500 }}>
                Collected dollars come from posted remittance totals; billed dollars are summed from the tenant's real claim queue.
              </div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 20 }}>
            <div style={cardStyle}>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>NOE compliance mirror</div>
              <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
                {[
                  ["Filed on time", formatInteger(noeSummary.onTime)],
                  ["Late", formatInteger(noeSummary.late)],
                  ["Unfiled", formatInteger(noeSummary.unfiled)],
                  ["Exempt", formatInteger(noeSummary.exempt)],
                ].map(([label, value]) => (
                  <div key={label} style={{ display: "flex", justifyContent: "space-between", gap: 16, borderBottom: `1px solid ${C.gray100}`, paddingBottom: 10 }}>
                    <span style={{ fontSize: 13, color: C.gray600 }}>{label}</span>
                    <strong style={{ fontSize: 13, color: C.navy }}>{value}</strong>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16 }}>
                <EmptyNoticeCard
                  title="Penalty dollar impact is not available yet"
                  description="The live NOE feed exposes filing timeliness, exemption status, and non-covered-day calculations, but it does not currently expose a real reimbursement-dollar penalty amount to this analytics page."
                />
              </div>
            </div>

            <div style={cardStyle}>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>Billing cycle generated charges</div>
              <div style={{ marginTop: 14, display: "grid", gap: 12 }}>
                {queueTotals.cycles.length ? (
                  queueTotals.cycles.slice(0, 5).map((cycle) => (
                    <div key={cycle.cycleId} style={{ borderBottom: `1px solid ${C.gray100}`, paddingBottom: 10 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
                        <strong style={{ fontSize: 13, color: C.navy }}>{cycle.cycleId.slice(0, 8)}</strong>
                        <span style={{ fontSize: 12, color: C.gray600 }}>
                          {formatInteger(cycle.claimCount)} claims · {formatCurrency(cycle.generatedAmount)}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: 13, color: C.slate500 }}>No billed claim rows are available for cycle-level charge totals yet.</div>
                )}
              </div>
              <div style={{ marginTop: 16 }}>
                <EmptyNoticeCard
                  title="Cycle status values are not available yet"
                  description="Real claim rows expose billing_cycle_id and generated charges, but this owner-side mirror does not yet have a read endpoint for the billing_cycles OPEN/CLOSED/LOCKED status field."
                />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
