import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { fetchPocCertificationStatus, type PocCertificationRow } from "../../api/dashboard";
import { useAgency } from "../../components/billing/AgencyContext";

function ReadyChip({ ready }: { ready: boolean }) {
  return (
    <Chip
      label={ready ? "Billing Ready" : "Not Ready"}
      size="small"
      sx={{
        fontWeight: 700,
        fontSize: 11,
        height: 22,
        bgcolor: ready ? "#dcfce7" : "#fee2e2",
        color: ready ? "#166534" : "#991b1b",
      }}
    />
  );
}

export default function PocCertificationPage() {
  const { selectedAgencyId } = useAgency();
  const [rows, setRows] = useState<PocCertificationRow[]>([]);
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
    fetchPocCertificationStatus(selectedAgencyId, { current_period_only: true, limit: 500 })
      .then((res) => {
        if (isMounted) setRows(res.poc_certification_status);
      })
      .catch((err) => {
        if (isMounted) setError(err?.message || "Unable to load POC & certification status.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgencyId]);

  return (
    <Box>
      <Typography sx={{ fontSize: 20, fontWeight: 800, color: "#0f172a" }}>POC &amp; Certifications</Typography>
      <Typography sx={{ fontSize: 12.5, color: "#64748b", mb: 2 }}>
        Current benefit period, certification, plan of care, and (for recerts) face-to-face status per patient --
        the exact CMS-required records billing readiness depends on.
      </Typography>

      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}

      {!selectedAgencyId ? (
        <Alert severity="info">Select an agency to view its POC &amp; certification status.</Alert>
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
                  <TableCell sx={{ fontWeight: 700 }}>Benefit Period</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Certification</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>POC Physician Approval</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>F2F (Recert)</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} sx={{ textAlign: "center", color: "#94a3b8", py: 4 }}>
                      No current benefit periods found for this agency.
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((row) => (
                    <TableRow key={`${row.patient_id}-${row.benefit_period.id}`} hover>
                      <TableCell>{row.patient_name || "—"}</TableCell>
                      <TableCell>{row.mrn || "—"}</TableCell>
                      <TableCell>
                        {row.benefit_period.benefit_type} #{row.benefit_period.period_number}
                      </TableCell>
                      <TableCell>{row.certification ? row.certification.status : "Missing"}</TableCell>
                      <TableCell>
                        {row.plan_of_care?.physician_approval_status || "Missing"}
                      </TableCell>
                      <TableCell>
                        {row.benefit_period.benefit_type === "RECERT"
                          ? row.f2f_encounter?.status || "Missing"
                          : "N/A"}
                      </TableCell>
                      <TableCell>
                        <ReadyChip ready={row.billing_ready} />
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
