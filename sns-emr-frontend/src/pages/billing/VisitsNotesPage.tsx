import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  FormControlLabel,
  Paper,
  Switch,
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

function StatusChip({ complete }: { complete: boolean }) {
  return (
    <Chip
      label={complete ? "Complete" : "Incomplete"}
      size="small"
      sx={{
        fontWeight: 700,
        fontSize: 11,
        height: 22,
        bgcolor: complete ? "#dcfce7" : "#fee2e2",
        color: complete ? "#166534" : "#991b1b",
      }}
    />
  );
}

export default function VisitsNotesPage() {
  const { selectedAgencyId } = useAgency();
  const [rows, setRows] = useState<VisitNoteRow[]>([]);
  const [unsignedOnly, setUnsignedOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedAgencyId) {
      setLoading(false);
      return;
    }
    let isMounted = true;
    setLoading(true);
    setError(null);
    fetchVisitsNotes(selectedAgencyId, { unsigned_only: unsignedOnly, limit: 500 })
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
  }, [selectedAgencyId, unsignedOnly]);

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Box>
          <Typography sx={{ fontSize: 20, fontWeight: 800, color: "#0f172a" }}>Visits &amp; Notes</Typography>
          <Typography sx={{ fontSize: 12.5, color: "#64748b" }}>
            Documentation status for real clinical notes tied to billable visits. Note content is never shown here.
          </Typography>
        </Box>
        <FormControlLabel
          control={<Switch checked={unsignedOnly} onChange={(e) => setUnsignedOnly(e.target.checked)} />}
          label="Unsigned only"
        />
      </Box>

      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its visits &amp; notes.</Alert>
      ) : loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : (
        <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: "#f1f5f9" }}>
                  <TableCell sx={{ fontWeight: 700 }}>Patient</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>MRN</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Encounter Date</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Discipline</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Note Type</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Author</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Signed</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Documentation</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} sx={{ textAlign: "center", color: "#94a3b8", py: 4 }}>
                      No visit notes found for this agency.
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((row) => (
                    <TableRow key={row.note_id} hover>
                      <TableCell>{row.patient_name || "—"}</TableCell>
                      <TableCell>{row.mrn || "—"}</TableCell>
                      <TableCell>{row.encounter_date || "—"}</TableCell>
                      <TableCell>{row.discipline || "—"}</TableCell>
                      <TableCell>{row.note_type || "—"}</TableCell>
                      <TableCell>{row.author_name || "—"}</TableCell>
                      <TableCell>{row.signed_at ? "Yes" : "No"}</TableCell>
                      <TableCell>
                        <StatusChip complete={row.documentation_complete} />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </Box>
  );
}
