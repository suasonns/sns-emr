import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import GppMaybeOutlinedIcon from "@mui/icons-material/GppMaybeOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";

import {
  fetchHospiceCapRecords,
  upsertHospiceCapRecord,
  type HospiceCapRecord,
} from "../../api/hospiceCap";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

// Dedicated presentation of the existing, production-real hospice
// aggregate cap capability (42 CFR 418.309). This page adds NO new
// calculation, table, or API -- it consumes the same
// hospice_cap_service.compute_agency_cap_usage() logic and the same
// GET/PUT /billing/hospice-cap[/{cap_year}] endpoints already used by the
// HospiceCapCard on the Reports page. This screen exists purely to give
// CAP its own dedicated nav destination matching the approved Figma
// "CAP Calculation" screen, per the 2026-09-05 discovery/approval:
// "CAP is an existing production capability that currently lacks a
// dedicated Billing Portal presentation layer."

// Cap year = the starting calendar year of the Nov 1 - Oct 31 hospice cap
// accounting year (42 CFR 418.309). Nov/Dec of year Y belong to cap year Y;
// Jan-Oct of year Y belong to cap year Y-1. Mirrors ReportsPage.tsx.
function currentCapYear(): number {
  const now = new Date();
  const year = now.getFullYear();
  return now.getMonth() >= 10 ? year : year - 1;
}

function currency(value: string | undefined | null): string {
  if (value === undefined || value === null || value === "") return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

type EditForm = {
  capYear: number;
  beneficiaryCount: string;
  grossCollected: string;
  sourceNote: string;
};

export default function CapCalculationPage() {
  const { selectedAgencyId } = useAgency();
  const [records, setRecords] = useState<HospiceCapRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const capYear = useMemo(() => currentCapYear(), []);

  const load = () => {
    if (!selectedAgencyId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    fetchHospiceCapRecords(selectedAgencyId)
      .then((res) => setRecords(res))
      .catch((err) => setError(err?.message || "Unable to load hospice cap records."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAgencyId]);

  const currentYearRecord = records.find((r) => r.cap_year === capYear) || null;
  const priorYears = records.filter((r) => r.cap_year !== capYear);

  const openEdit = (year: number) => {
    const existing = records.find((r) => r.cap_year === year);
    setSaveError(null);
    setEditForm({
      capYear: year,
      beneficiaryCount: existing?.beneficiary_count ?? "",
      grossCollected: existing?.gross_reimbursement_collected ?? "",
      sourceNote: existing?.source_note ?? "",
    });
  };

  const handleSave = async () => {
    if (!editForm || !selectedAgencyId) return;
    setSaving(true);
    setSaveError(null);
    try {
      await upsertHospiceCapRecord(
        editForm.capYear,
        {
          cap_year: editForm.capYear,
          beneficiary_count: editForm.beneficiaryCount,
          gross_reimbursement_collected: editForm.grossCollected,
          source_note: editForm.sourceNote || undefined,
        },
        selectedAgencyId
      );
      setEditForm(null);
      load();
    } catch (err: any) {
      setSaveError(err?.message || "Unable to save hospice cap data.");
    } finally {
      setSaving(false);
    }
  };

  const usage = currentYearRecord?.cap_usage;

  const metrics = useMemo(
    () => [
      { label: "Cap Year", value: String(capYear), caption: "Nov 1 – Oct 31 accounting year" },
      { label: "Allowed Amount", value: usage ? currency(usage.allowed_amount) : "—", caption: "Beneficiary count × per-beneficiary cap" },
      {
        label: "Gross Collected",
        value: usage ? currency(usage.gross_reimbursement_collected) : "—",
        caption: "PS&R / remittance-sourced",
      },
      {
        label: usage?.is_over_cap ? "Over Cap" : "Available",
        value: usage ? currency(usage.is_over_cap ? usage.over_cap_amount : usage.available_amount) : "—",
        caption: usage?.is_over_cap ? "Repayment liability" : "Remaining before cap is reached",
        color: usage ? (usage.is_over_cap ? "#f87171" : "#4ade80") : undefined,
      },
    ],
    [capYear, usage]
  );

  const usagePct = usage ? Math.min(100, (Number(usage.gross_reimbursement_collected) / Number(usage.allowed_amount)) * 100) : 0;

  return (
    <Box>
      <PageHeader
        title="CAP Calculation"
        subtitle="Hospice aggregate cap (42 CFR 418.309) — agency-level Medicare payment cap tracking"
        actions={
          <Button
            variant="contained"
            size="small"
            startIcon={<EditOutlinedIcon fontSize="small" />}
            onClick={() => openEdit(capYear)}
            disabled={!selectedAgencyId}
            sx={{ bgcolor: "#10b7a2", textTransform: "none", fontWeight: 700, "&:hover": { bgcolor: "#0f766e" } }}
          >
            {currentYearRecord ? "Update Figures" : "Log Cap Data"}
          </Button>
        }
      />

      <HipaaBanner message={"Under HIPAA \"Minimum Necessary\" guidelines, this view shows administrative financial tallies only. Beneficiary count and collected amount are billing-department-entered figures sourced from the agency's real NGS PS&R cap report — this system does not compute or fabricate them."} />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its hospice aggregate cap tracking.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics} />

          <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", p: 2, mb: 2.5 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
              <GppMaybeOutlinedIcon sx={{ fontSize: 20, color: "#14b8a6" }} />
              <Typography sx={{ fontSize: 14, fontWeight: 800, color: "#fff" }}>
                Current Cap Year Utilization
              </Typography>
            </Box>

            {!currentYearRecord ? (
              <>
                <Typography sx={{ fontSize: 12.5, color: "#7f97b3", mb: 1 }}>
                  Not configured yet. This app cannot compute the aggregate cap on its own — it needs the agency's
                  real, cross-provider beneficiary count and collected reimbursement from the NGS PS&R cap report.
                </Typography>
                <Button size="small" variant="outlined" onClick={() => openEdit(capYear)} sx={{ color: "#14b8a6", borderColor: "#14b8a6" }}>
                  Log cap data
                </Button>
              </>
            ) : usage ? (
              <>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 1.5 }}>
                  <Chip
                    label={`Allowed: ${currency(usage.allowed_amount)}`}
                    size="small"
                    sx={{ fontSize: 11.5, fontWeight: 700, bgcolor: "#0b1626", color: "#e2e8f0", border: "1px solid #1f3a5c" }}
                  />
                  <Chip
                    label={`Collected: ${currency(usage.gross_reimbursement_collected)}`}
                    size="small"
                    sx={{ fontSize: 11.5, fontWeight: 700, bgcolor: "#0b1626", color: "#e2e8f0", border: "1px solid #1f3a5c" }}
                  />
                  <Chip
                    label={usage.is_over_cap ? `Over cap: ${currency(usage.over_cap_amount)}` : `Available: ${currency(usage.available_amount)}`}
                    size="small"
                    sx={{
                      fontSize: 11.5,
                      fontWeight: 700,
                      bgcolor: "#0b1626",
                      color: usage.is_over_cap ? "#f87171" : "#4ade80",
                      border: "1px solid #1f3a5c",
                    }}
                  />
                </Box>
                <Typography sx={{ fontSize: 11.5, color: "#7f97b3", mb: 0.75 }}>
                  Collected vs. Allowed —{" "}
                  <Box component="span" sx={{ color: usage.is_over_cap ? "#f87171" : "#4ade80", fontWeight: 700 }}>
                    {usagePct.toFixed(1)}%
                  </Box>
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={usagePct}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    bgcolor: "#1f3a5c",
                    "& .MuiLinearProgress-bar": { bgcolor: usage.is_over_cap ? "#f87171" : "#4ade80" },
                  }}
                />
                <Typography sx={{ fontSize: 11.5, color: "#7f97b3", mt: 1.5 }}>
                  Beneficiary count and collected amount are biller-entered from the agency's NGS PS&R cap report —{" "}
                  {currentYearRecord.source_note ? `${currentYearRecord.source_note}.` : "no source note on file."}
                </Typography>
              </>
            ) : (
              <Typography sx={{ fontSize: 12.5, color: "#7f97b3" }}>
                {currentYearRecord.cap_error || "Cap amount not on file for this cap year."}
              </Typography>
            )}
          </Paper>

          <Paper sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c", overflow: "hidden" }}>
            <Typography sx={{ fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3", px: 2, pt: 1.5 }}>
              CAP YEAR HISTORY
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {["Cap Year", "Beneficiary Count", "Gross Collected", "Allowed", "Status", "Source", "Action"].map((h) => (
                      <TableCell
                        key={h}
                        sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, borderColor: "#1f3a5c" }}
                      >
                        {h.toUpperCase()}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {priorYears.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                        No other cap years logged for this agency yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    priorYears.map((r) => (
                      <TableRow key={r.cap_year} hover>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{r.cap_year}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>{r.beneficiary_count ?? "—"}</TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                          {currency(r.gross_reimbursement_collected)}
                        </TableCell>
                        <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                          {r.cap_usage ? currency(r.cap_usage.allowed_amount) : "—"}
                        </TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          {r.cap_usage ? (
                            <Chip
                              label={r.cap_usage.is_over_cap ? "Over Cap" : "Within Cap"}
                              size="small"
                              sx={{
                                fontWeight: 700,
                                fontSize: 11,
                                height: 22,
                                bgcolor: r.cap_usage.is_over_cap ? "#7f1d1d" : "#14532d",
                                color: r.cap_usage.is_over_cap ? "#fca5a5" : "#86efac",
                              }}
                            />
                          ) : (
                            <Chip label="No cap amount on file" size="small" sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: "#334155", color: "#cbd5e1" }} />
                          )}
                        </TableCell>
                        <TableCell sx={{ color: "#7f97b3", fontSize: 12, borderColor: "#1f3a5c" }}>{r.source_note || "—"}</TableCell>
                        <TableCell sx={{ borderColor: "#1f3a5c" }}>
                          <Button size="small" onClick={() => openEdit(r.cap_year)} sx={{ color: "#14b8a6", fontSize: 12, textTransform: "none" }}>
                            Edit
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </>
      )}

      <Dialog open={editForm !== null} onClose={() => (!saving ? setEditForm(null) : undefined)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontSize: 15, fontWeight: 800 }}>
          {editForm ? `Hospice Aggregate Cap — Cap Year ${editForm.capYear}` : ""}
        </DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          <Typography sx={{ fontSize: 12, color: "#64748b" }}>
            Enter the real, PS&R-sourced beneficiary count and gross reimbursement collected for this cap year. This
            app cannot derive these cross-provider proportional figures on its own.
          </Typography>
          <TextField
            label="Beneficiary count (NGS/PS&R report)"
            size="small"
            value={editForm?.beneficiaryCount ?? ""}
            onChange={(e) => setEditForm((f) => (f ? { ...f, beneficiaryCount: e.target.value } : f))}
          />
          <TextField
            label="Gross reimbursement collected"
            size="small"
            value={editForm?.grossCollected ?? ""}
            onChange={(e) => setEditForm((f) => (f ? { ...f, grossCollected: e.target.value } : f))}
          />
          <TextField
            label="Source note (e.g. NGS PS&R report date)"
            size="small"
            value={editForm?.sourceNote ?? ""}
            onChange={(e) => setEditForm((f) => (f ? { ...f, sourceNote: e.target.value } : f))}
          />
          {saveError ? (
            <Alert severity="error" sx={{ fontSize: 12 }}>
              {saveError}
            </Alert>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditForm(null)} disabled={saving}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
