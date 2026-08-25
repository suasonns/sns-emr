import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { fetchVisitsNotes, type VisitNoteRow } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";
import PageHeader from "../../components/billing/PageHeader";
import HipaaBanner from "../../components/billing/HipaaBanner";
import { MetricCardRow } from "../../components/billing/MetricCardRow";

const PAGE_SIZE = 15;

type NoteStatus = "Signed" | "Pending" | "Missing";

// Derives an honest 3-state status from the real fields the backend returns
// -- never invents a status the data doesn't support.
function noteStatus(row: VisitNoteRow): NoteStatus {
  if (row.signed_at) return "Signed";
  if (row.documentation_complete) return "Pending";
  return "Missing";
}

function StatusChip({ status }: { status: NoteStatus }) {
  const styles: Record<NoteStatus, { bg: string; fg: string }> = {
    Signed: { bg: "#dcfce7", fg: "#166534" },
    Pending: { bg: "#fef3c7", fg: "#92400e" },
    Missing: { bg: "#fee2e2", fg: "#991b1b" },
  };
  const s = styles[status];
  return <Chip label={status} size="small" sx={{ fontWeight: 700, fontSize: 11, height: 22, bgcolor: s.bg, color: s.fg }} />;
}

export default function VisitsNotesPage() {
  const { selectedAgencyId } = useAgency();
  const [rows, setRows] = useState<VisitNoteRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [disciplineFilter, setDisciplineFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | NoteStatus>("ALL");
  const [page, setPage] = useState(0);

  useEffect(() => {
    if (!selectedAgencyId) {
      setLoading(false);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    fetchVisitsNotes(selectedAgencyId, { limit: 500 })
      .then((res) => {
        if (isMounted) setRows(res.visits_notes);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load visits & notes.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  useEffect(() => {
    setPage(0);
  }, [disciplineFilter, statusFilter, selectedAgencyId]);

  const disciplines = useMemo(
    () => Array.from(new Set(rows.map((r) => r.discipline).filter(Boolean))) as string[],
    [rows]
  );

  const filteredRows = useMemo(
    () =>
      rows.filter((r) => {
        if (disciplineFilter !== "ALL" && r.discipline !== disciplineFilter) return false;
        if (statusFilter !== "ALL" && noteStatus(r) !== statusFilter) return false;
        return true;
      }),
    [rows, disciplineFilter, statusFilter]
  );

  const metrics = useMemo(() => {
    const total = rows.length;
    const signed = rows.filter((r) => r.signed_at).length;
    const pending = total - signed;
    const signedPct = total > 0 ? Math.round((signed / total) * 1000) / 10 : 0;
    const pendingPct = total > 0 ? Math.round((pending / total) * 1000) / 10 : 0;
    return [
      { label: "Total Visits (This Billing Cycle)", value: String(total), caption: "Visits recorded for submission audit" },
      { label: "Notes Completed & Signed", value: String(signed), caption: `${signedPct}% compliance rate`, color: "#4ade80" },
      { label: "Documentation Pending", value: String(pending), caption: `${pendingPct}% outstanding clinician signatures`, color: pending > 0 ? "#fbbf24" : "#4ade80" },
    ];
  }, [rows]);

  const pageCount = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE));
  const pageRows = filteredRows.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);

  return (
    <Box>
      <PageHeader
        title="Visits & Notes Status"
        subtitle="Check clinical documentation and signature compliance on individual visits without narrative content access."
      />
      <HipaaBanner />

      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its visits &amp; notes.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <>
          <MetricCardRow metrics={metrics} />

          <Box sx={{ display: "flex", gap: 1.5, alignItems: "center", mb: 1.5 }}>
            <Typography sx={{ fontSize: 11.5, fontWeight: 700, color: "#94a3b8" }}>FILTERS:</Typography>
            <Select
              size="small"
              value={disciplineFilter}
              onChange={(e) => setDisciplineFilter(e.target.value)}
              sx={{ fontSize: 13, minWidth: 160 }}
            >
              <MenuItem value="ALL">Discipline: All Types</MenuItem>
              {disciplines.map((d) => (
                <MenuItem key={d} value={d}>
                  {d}
                </MenuItem>
              ))}
            </Select>
            <Select
              size="small"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as "ALL" | NoteStatus)}
              sx={{ fontSize: 13, minWidth: 160 }}
            >
              <MenuItem value="ALL">Status: All Statuses</MenuItem>
              <MenuItem value="Signed">Signed</MenuItem>
              <MenuItem value="Pending">Pending</MenuItem>
              <MenuItem value="Missing">Missing</MenuItem>
            </Select>
          </Box>

          <TableContainer sx={{ bgcolor: "#0f1b2d", borderRadius: 2, border: "1px solid #1f3a5c" }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {["Visit Date", "Patient ID (MRN)", "Visit Type", "Assigned Clinician", "Note Status", "Signature Date"].map(
                    (h) => (
                      <TableCell
                        key={h}
                        sx={{ color: "#7f97b3", fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, borderColor: "#1f3a5c" }}
                      >
                        {h.toUpperCase()}
                      </TableCell>
                    )
                  )}
                </TableRow>
              </TableHead>
              <TableBody>
                {pageRows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: "center", color: "#7f97b3", py: 4, borderColor: "#1f3a5c" }}>
                      No visit notes match the current filters.
                    </TableCell>
                  </TableRow>
                ) : (
                  pageRows.map((row) => (
                    <TableRow key={row.note_id} hover>
                      <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                        {row.encounter_date || "—"}
                      </TableCell>
                      <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                        {row.mrn || row.patient_id || "—"}
                      </TableCell>
                      <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                        {row.note_type || row.visit_type || "—"}
                      </TableCell>
                      <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                        {row.author_name || "—"}
                      </TableCell>
                      <TableCell sx={{ borderColor: "#1f3a5c" }}>
                        <StatusChip status={noteStatus(row)} />
                      </TableCell>
                      <TableCell sx={{ color: "#e2e8f0", fontSize: 13, borderColor: "#1f3a5c" }}>
                        {row.signed_at ? row.signed_at.slice(0, 10) : "—"}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 1.5 }}>
            <Typography sx={{ fontSize: 12, color: "#94a3b8" }}>
              Showing {filteredRows.length === 0 ? 0 : page * PAGE_SIZE + 1}-
              {Math.min(filteredRows.length, page * PAGE_SIZE + PAGE_SIZE)} of {filteredRows.length} entries
            </Typography>
            <Box sx={{ display: "flex", gap: 1 }}>
              <Chip
                label="Previous"
                size="small"
                clickable={page > 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                sx={{ opacity: page === 0 ? 0.5 : 1 }}
              />
              <Chip
                label="Next"
                size="small"
                clickable={page < pageCount - 1}
                onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
                sx={{ opacity: page >= pageCount - 1 ? 0.5 : 1 }}
              />
            </Box>
          </Box>
        </>
      )}
    </Box>
  );
}
