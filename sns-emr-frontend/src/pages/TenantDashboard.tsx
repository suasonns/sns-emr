import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Button,
  Chip,
  type ChipProps,
  Paper,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import { fetchCensusWorkspace, type CensusCategory, type CensusPatientRow } from "../api/census";
import { getCurrentUser } from "../api/session";
import PortalShell from "../components/PortalShell";
import { portalTypography } from "../styles/portalTypography";
const PAGE_SIZE = 8;

const DEMO_PATIENTS: CensusPatientRow[] = [
  {
    patient_id: "demo-1",
    mrn: "847-293",
    full_name: "Albert Smith",
    date_of_birth: "1941-11-14",
    primary_diagnosis: "Heart Failure, unspecified",
    patient_status: "ACTIVE",
    admission_status: "ADMITTED",
    admission_at: "2024-10-12T00:00:00Z",
    discharge_date: null,
    discharge_reason: null,
    attending_physician: "Dr. Sarah Jenkins",
    payer_name: "Medicare",
    last_visit_at: "2024-10-12T00:00:00Z",
    census_bucket: "Active",
  },
  {
    patient_id: "demo-2",
    mrn: "492-104",
    full_name: "Eleanor Vance",
    date_of_birth: "1938-03-22",
    primary_diagnosis: "Alzheimer's Disease",
    patient_status: "ACTIVE",
    admission_status: "ADMITTED",
    admission_at: "2024-11-01T00:00:00Z",
    discharge_date: null,
    discharge_reason: null,
    attending_physician: "Dr. Robert Chen",
    payer_name: "Medicaid",
    last_visit_at: "2024-11-01T00:00:00Z",
    census_bucket: "Active",
  },
  {
    patient_id: "demo-3",
    mrn: "105-392",
    full_name: "George Henderson",
    date_of_birth: "1948-09-15",
    primary_diagnosis: "COPD, severe chronic",
    patient_status: "ACTIVE",
    admission_status: "ADMITTED",
    admission_at: "2024-09-15T00:00:00Z",
    discharge_date: null,
    discharge_reason: null,
    attending_physician: "Dr. Sarah Jenkins",
    payer_name: "Medicare",
    last_visit_at: "2024-09-15T00:00:00Z",
    census_bucket: "Active",
  },
  {
    patient_id: "demo-4",
    mrn: "392-817",
    full_name: "Mildred Coleman",
    date_of_birth: "1935-01-30",
    primary_diagnosis: "Malignant Neoplasm, lung",
    patient_status: "DISCHARGED",
    admission_status: "DISCHARGED",
    admission_at: "2024-07-04T00:00:00Z",
    discharge_date: "2024-12-20",
    discharge_reason: "Transferred",
    attending_physician: "Dr. Emily Taylor",
    payer_name: "Blue Cross",
    last_visit_at: "2024-12-20T00:00:00Z",
    census_bucket: "Discharged",
  },
  {
    patient_id: "demo-5",
    mrn: "721-048",
    full_name: "Thomas Sterling",
    date_of_birth: "1952-05-12",
    primary_diagnosis: "Renal Failure, chronic",
    patient_status: "REVOKED",
    admission_status: "REVOKED",
    admission_at: "2024-08-18T00:00:00Z",
    discharge_date: "2024-10-05",
    discharge_reason: "Revoked before SOC",
    attending_physician: "Dr. Robert Chen",
    payer_name: "Medicare",
    last_visit_at: "2024-10-05T00:00:00Z",
    census_bucket: "Revoked",
  },
  {
    patient_id: "demo-6",
    mrn: "830-412",
    full_name: "Alice Whittaker",
    date_of_birth: "1929-12-03",
    primary_diagnosis: "Parkinson's Disease",
    patient_status: "ACTIVE",
    admission_status: "ADMITTED",
    admission_at: "2024-12-01T00:00:00Z",
    discharge_date: null,
    discharge_reason: null,
    attending_physician: "Dr. Sarah Jenkins",
    payer_name: "Medicare",
    last_visit_at: "2024-12-01T00:00:00Z",
    census_bucket: "Active",
  },
  {
    patient_id: "demo-7",
    mrn: "204-184",
    full_name: "Arthur Pendleton",
    date_of_birth: "1939-07-19",
    primary_diagnosis: "Senile Degeneration",
    patient_status: "DECEASED",
    admission_status: "DISCHARGED",
    admission_at: "2024-11-02T00:00:00Z",
    discharge_date: "2024-09-14",
    discharge_reason: "Deceased",
    attending_physician: "Dr. Emily Taylor",
    payer_name: "Aetna",
    last_visit_at: "2024-09-14T00:00:00Z",
    census_bucket: "Deceased",
  },
  {
    patient_id: "demo-8",
    mrn: "502-991",
    full_name: "Clara Oswald",
    date_of_birth: "1936-10-24",
    primary_diagnosis: "End Stage Dementia",
    patient_status: "ACTIVE",
    admission_status: "ADMITTED",
    admission_at: "2024-11-15T00:00:00Z",
    discharge_date: null,
    discharge_reason: null,
    attending_physician: "Dr. Robert Chen",
    payer_name: "Medicaid",
    last_visit_at: "2024-11-15T00:00:00Z",
    census_bucket: "Active",
  },
];

const CATEGORY_LABELS: Array<{ key: CensusCategory; label: string }> = [
  { key: "ALL", label: "All" },
  { key: "ACTIVE", label: "Active" },
  { key: "DISCHARGED", label: "Discharged" },
  { key: "DECEASED", label: "Deceased" },
  { key: "REVOKED", label: "Revoked" },
];

function formatDate(value: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", { month: "2-digit", day: "2-digit", year: "numeric" }).format(date);
}

function formatRelative(value: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const diff = Date.now() - date.getTime();
  const days = Math.round(diff / (1000 * 60 * 60 * 24));
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

function statusColor(bucket: string): ChipProps["color"] {
  switch (bucket) {
    case "Active":
      return "success";
    case "Discharged":
      return "info";
    case "Deceased":
      return "default";
    case "Revoked":
      return "warning";
    default:
      return "default";
  }
}

export default function TenantDashboard() {
  const workspaceName = getCurrentUser()?.tenant_name ?? "Love & Faith Hospice Services Inc.";
  const [rows, setRows] = useState<CensusPatientRow[]>(DEMO_PATIENTS);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<CensusCategory>("ALL");
  const [page, setPage] = useState(1);

  useEffect(() => {
    let mounted = true;

    fetchCensusWorkspace()
      .then((data) => {
        if (!mounted) return;

        if (data.patients.length > 0) {
          setRows(data.patients);
        }
      })
      .catch(() => undefined);

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    setPage(1);
  }, [category, query]);

  const filteredRows = useMemo(() => {
    const q = query.trim().toLowerCase();

    return rows.filter((row) => {
      const bucket = row.census_bucket.toUpperCase();
      const matchesCategory = category === "ALL" || bucket === category;
      const matchesQuery =
        !q ||
        row.mrn.toLowerCase().includes(q) ||
        row.full_name.toLowerCase().includes(q) ||
        (row.primary_diagnosis ?? "").toLowerCase().includes(q) ||
        (row.attending_physician ?? "").toLowerCase().includes(q) ||
        (row.payer_name ?? "").toLowerCase().includes(q);

      return matchesCategory && matchesQuery;
    });
  }, [rows, category, query]);

  const totals = useMemo(() => {
    const counts = { ALL: rows.length, ACTIVE: 0, DISCHARGED: 0, DECEASED: 0, REVOKED: 0 };
    rows.forEach((row) => {
      const bucket = row.census_bucket.toUpperCase() as keyof typeof counts;
      if (bucket in counts && bucket !== "ALL") {
        counts[bucket] += 1;
      }
    });
    return counts;
  }, [rows]);

  const pageCount = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE));
  const visibleRows = filteredRows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <PortalShell activeTab="Census">
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 2, flexWrap: "wrap" }}>
          <Box>
            <Typography sx={{ fontSize: 22, fontWeight: 800, color: "#1f3552", lineHeight: 1.05 }}>
              Patient Census Workspace
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap", mt: 0.7 }}>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: portalTypography.small }}>
                Active Agency Workspace:
              </Typography>
              <Chip label={workspaceName} size="small" sx={{ background: "#ccfbf1", color: "#0f766e", fontWeight: 700, height: 22, fontSize: portalTypography.chip }} />
            </Box>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 0.8, pt: 0.2, fontSize: portalTypography.small }}>
            <Box component="span" sx={{ width: 8, height: 8, borderRadius: "50%", background: "#64748b" }} />
            Last synced: Today at 08:30 AM
          </Typography>
        </Box>

        <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, flexDirection: { xs: "column", md: "row" } }}>
          <TextField
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by name, MRN, or doctor..."
            size="small"
            sx={{
              width: { xs: "100%", md: 360 },
              background: "#fff",
              borderRadius: 999,
              "& .MuiOutlinedInput-root": { borderRadius: 999, height: 30 },
            }}
          />

          <Button variant="contained" sx={{ background: "#10b7a2", fontWeight: 700, px: 3, height: 32, fontSize: portalTypography.small }}>
            + Add New Patient
          </Button>
        </Box>

        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
          {CATEGORY_LABELS.map((item) => (
            <Chip
              key={item.key}
              label={`${item.label}${totals[item.key] ? ` ${totals[item.key]}` : ""}`}
              onClick={() => setCategory(item.key)}
              color={category === item.key ? "primary" : "default"}
              sx={{
                backgroundColor: category === item.key ? "#0f766e !important" : "#fff",
                color: category === item.key ? "#fff !important" : "#3a4757",
                border: "1px solid",
                borderColor: category === item.key ? "#0f766e" : "#d7e0e8",
                fontWeight: 700,
                borderRadius: 999,
                height: 28,
              }}
            />
          ))}
        </Box>

        <Box sx={{ overflowX: "auto" }}>
          <Paper variant="outlined" sx={{ borderColor: "#dfe7ee", borderRadius: 2, overflow: "hidden", background: "#fff" }}>
            <Table size="small" sx={{ minWidth: 1100 }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>Status</TableCell>
                  <TableCell sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>MRN</TableCell>
                  <TableCell sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>Patient Name</TableCell>
                  <TableCell sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>DOB</TableCell>
                  <TableCell sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>Primary Diagnosis</TableCell>
                  <TableCell sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>Attending Physician</TableCell>
                  <TableCell sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>Payer</TableCell>
                  <TableCell sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>Adm. Date</TableCell>
                  <TableCell sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>Last Visit</TableCell>
                  <TableCell align="right" sx={{ fontSize: portalTypography.tableHeader, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.4 }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {visibleRows.map((row) => (
                  <TableRow key={row.patient_id} hover>
                    <TableCell>
                      <Chip
                        size="small"
                        label={row.census_bucket}
                        color={statusColor(row.census_bucket)}
                        sx={{ fontWeight: 700, height: 20, fontSize: portalTypography.chip }}
                      />
                    </TableCell>
                    <TableCell sx={{ fontSize: portalTypography.small }}>{row.mrn}</TableCell>
                    <TableCell sx={{ fontWeight: 700, fontSize: portalTypography.small }}>{row.full_name}</TableCell>
                    <TableCell sx={{ fontSize: portalTypography.small }}>{formatDate(row.date_of_birth)}</TableCell>
                    <TableCell sx={{ fontSize: portalTypography.small }}>{row.primary_diagnosis ?? "—"}</TableCell>
                    <TableCell sx={{ fontSize: portalTypography.small }}>{row.attending_physician ?? "—"}</TableCell>
                    <TableCell sx={{ fontSize: portalTypography.small }}>{row.payer_name ?? "—"}</TableCell>
                    <TableCell sx={{ fontSize: portalTypography.small }}>{formatDate(row.admission_at)}</TableCell>
                    <TableCell sx={{ fontSize: portalTypography.small }}>{formatRelative(row.last_visit_at)}</TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="outlined" sx={{ height: 28, fontSize: portalTypography.chip }}>
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!visibleRows.length ? (
                  <TableRow>
                    <TableCell colSpan={10} align="center" sx={{ py: 6, color: "text.secondary" }}>
                      No census patients match this filter.
                    </TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </Paper>
        </Box>

        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 2, flexDirection: { xs: "column", sm: "row" } }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: portalTypography.small }}>
            Showing {filteredRows.length ? (page - 1) * PAGE_SIZE + 1 : 0}-{Math.min(page * PAGE_SIZE, filteredRows.length)} of {filteredRows.length} patients
          </Typography>
          <Pagination count={pageCount} page={page} onChange={(_, value) => setPage(value)} color="primary" size="small" />
        </Box>
      </Box>
    </PortalShell>
  );
}
