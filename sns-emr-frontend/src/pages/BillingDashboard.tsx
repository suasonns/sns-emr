
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  MenuItem,
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

import DownloadIcon from "@mui/icons-material/Download";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import SendIcon from "@mui/icons-material/Send";
import TaskAltIcon from "@mui/icons-material/TaskAlt";
import PaidIcon from "@mui/icons-material/Paid";
import ErrorIcon from "@mui/icons-material/Error";

import api from "../api/client";
import BillingAuditHistoryPanel from "../components/BillingAuditHistoryPanel";

type ClaimLifecycleResponse = {
  ready?: number;
  sent?: number;
  accepted?: number;
  paid?: number;
  denied?: number;
};

type BillingQueueRow = {
  claim_id?: string;
  billing_cycle_id: string;
  patient_id: string;
  patient_name?: string | null;
  patient_mrn?: string | null;
  payer_name?: string | null;
  tenant_name?: string | null;
  tenant_id?: string | null;
  total_charge?: number | null;
  total_units?: number | null;
  risk_score?: number | null;
  status: string;
  service_date?: string | null;
};

type ExportResponse = {
  claim_control_number: string;
  edi_text?: string;
  warnings?: string[];
  errors?: string[];
};

type TenantOption = {
  tenant_id: string;
  display_name?: string;
  legal_name?: string;
};

const lifecycleCards = [
  {
    key: "ready",
    label: "Ready",
    icon: CheckCircleIcon,
    fg: "#0f766e",
    bg: "#ccfbf1",
  },
  {
    key: "sent",
    label: "Sent",
    icon: SendIcon,
    fg: "#4338ca",
    bg: "#e0e7ff",
  },
  {
    key: "accepted",
    label: "Accepted",
    icon: TaskAltIcon,
    fg: "#166534",
    bg: "#dcfce7",
  },
  {
    key: "paid",
    label: "Paid",
    icon: PaidIcon,
    fg: "#1d4ed8",
    bg: "#dbeafe",
  },
  {
    key: "denied",
    label: "Denied",
    icon: ErrorIcon,
    fg: "#b91c1c",
    bg: "#fee2e2",
  },
] as const;

function formatMoney(value?: number | null): string {
  if (typeof value !== "number") return "-";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatDate(value?: string | null): string {
  if (!value) return "-";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString();
}

function getStatusColor(
  status: string
): "success" | "warning" | "error" | "default" | "info" {
  switch (status.toUpperCase()) {
    case "READY":
      return "success";
    case "SENT":
      return "info";
    case "ACCEPTED":
      return "success";
    case "PAID":
      return "success";
    case "DENIED":
      return "error";
    case "WARNING":
      return "warning";
    default:
      return "default";
  }
}

export default function BillingDashboard() {
  const [lifecycle, setLifecycle] = useState<ClaimLifecycleResponse | null>(null);
  const [rows, setRows] = useState<BillingQueueRow[]>([]);
  const [tenants, setTenants] = useState<TenantOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [queueLoading, setQueueLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [tenantFilter, setTenantFilter] = useState("ALL");

  const [selectedClaim, setSelectedClaim] = useState<{
    patient_id: string;
    billing_cycle_id: string;
  } | null>(null);

  const firstFilteredRowRef = useRef<HTMLTableRowElement | null>(null);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [lifecycleRes, queueRes, tenantsRes] = await Promise.allSettled([
        api.get<ClaimLifecycleResponse>("/dashboard/claim-lifecycle"),
        api.get<BillingQueueRow[]>("/billing/queue"),
        api.get<TenantOption[]>("/billing/tenants"),
      ]);

      if (lifecycleRes.status === "fulfilled") {
        setLifecycle(lifecycleRes.value.data);
      } else {
        throw lifecycleRes.reason;
      }

      setRows(
        queueRes.status === "fulfilled" && Array.isArray(queueRes.value.data)
          ? queueRes.value.data
          : []
      );

      setTenants(
        tenantsRes.status === "fulfilled" && Array.isArray(tenantsRes.value.data)
          ? tenantsRes.value.data
          : []
      );
    } catch (err) {
      console.error("Billing dashboard load error:", err);
      setError("Failed to load billing dashboard.");
    } finally {
      setLoading(false);
    }
  };

  const reloadQueue = async () => {
    try {
      setQueueLoading(true);

      const res = await api.get<BillingQueueRow[]>("/billing/queue");
      setRows(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error("Billing queue reload error:", err);
      setError("Failed to refresh billing queue.");
    } finally {
      setQueueLoading(false);
    }
  };

  useEffect(() => {
    void loadDashboard();
  }, []);

  const filteredRows = useMemo(() => {
    return rows.filter((row) => {
      const statusOk =
        statusFilter === "ALL" || row.status.toUpperCase() === statusFilter;

      const tenantOk =
        tenantFilter === "ALL" || row.tenant_id === tenantFilter;

      const q = search.trim().toLowerCase();

      const searchOk =
        q.length === 0 ||
        row.patient_id.toLowerCase().includes(q) ||
        (row.patient_name ?? "").toLowerCase().includes(q) ||
        (row.patient_mrn ?? "").toLowerCase().includes(q) ||
        row.billing_cycle_id.toLowerCase().includes(q) ||
        (row.payer_name ?? "").toLowerCase().includes(q);

      return statusOk && tenantOk && searchOk;
    });
  }, [rows, search, statusFilter, tenantFilter]);

  useEffect(() => {
    if (firstFilteredRowRef.current) {
      firstFilteredRowRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [statusFilter, tenantFilter, search]);

  const summary = useMemo(() => {
    return {
      totalClaims: rows.length,
      filteredClaims: filteredRows.length,
      filteredCharge: filteredRows.reduce(
        (sum, row) =>
          sum + (typeof row.total_charge === "number" ? row.total_charge : 0),
        0
      ),
      filteredDenied: filteredRows.filter(
        (r) => r.status.toUpperCase() === "DENIED"
      ).length,
    };
  }, [rows, filteredRows]);

  const totalLifecycle =
    (lifecycle?.ready ?? 0) +
    (lifecycle?.sent ?? 0) +
    (lifecycle?.accepted ?? 0) +
    (lifecycle?.paid ?? 0) +
    (lifecycle?.denied ?? 0);

  const getPercent = (value?: number) => {
    if (!totalLifecycle || !value) return 0;
    return Math.round((value / totalLifecycle) * 100);
  };

  const handleExport = async (row: BillingQueueRow) => {
    try {
      setSuccessMessage(null);
      setError(null);

      const res = await api.post<ExportResponse>(
        "/billing/export-patient-claim-edi",
        {
          patient_id: row.patient_id,
          billing_cycle_id: row.billing_cycle_id,
        }
      );

      setSuccessMessage(
        `Claim export created successfully — Control # ${res.data.claim_control_number}`
      );

      setTimeout(() => setSuccessMessage(null), 3000);

      await reloadQueue();
      await loadDashboard();
    } catch (err) {
      console.error("Claim export error:", err);
      setError("Failed to export selected claim.");
    }
  };

  const handleExportFiltered = async () => {
    if (filteredRows.length === 0) {
      setError("There are no filtered claims to export.");
      return;
    }

    try {
      setSuccessMessage(null);
      setError(null);

      for (const row of filteredRows) {
        await api.post<ExportResponse>("/billing/export-patient-claim-edi", {
          patient_id: row.patient_id,
          billing_cycle_id: row.billing_cycle_id,
        });
      }

      setSuccessMessage(
        `Exported ${filteredRows.length} filtered claim(s) successfully.`
      );

      setTimeout(() => setSuccessMessage(null), 3000);

      await reloadQueue();
      await loadDashboard();
    } catch (err) {
      console.error("Bulk export error:", err);
      setError("Failed to export one or more filtered claims.");
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 5 }}>
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 5 }}>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 700 }}>
            Billing Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor claim lifecycle, filter the billing queue, export claims,
            and review audit history safely.
          </Typography>
        </Box>

        {error && <Alert severity="error">{error}</Alert>}
        {successMessage && <Alert severity="success">{successMessage}</Alert>}

        {/* KPI cards */}
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(5, 1fr)",
            },
            gap: 2,
          }}
        >
          {lifecycleCards.map((card) => {
            const Icon = card.icon;
            const value = lifecycle?.[card.key] ?? 0;

            return (
              <Card
                key={card.key}
                onClick={() => setStatusFilter(card.key.toUpperCase())}
                sx={{
                  borderRadius: 3,
                  boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
                  background: `linear-gradient(135deg, ${card.bg} 0%, #ffffff 100%)`,
                  cursor: "pointer",
                }}
              >
                <CardContent>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {card.label}
                      </Typography>
                      <Typography
                        variant="h4"
                        sx={{ fontWeight: 700, color: card.fg }}
                      >
                        {value}
                      </Typography>
                    </Box>

                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        borderRadius: 2,
                        backgroundColor: "rgba(255,255,255,0.7)",
                      }}
                    >
                      <Icon sx={{ color: card.fg, fontSize: 28 }} />
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            );
          })}
        </Box>

        {/* Lifecycle distribution */}
        <Paper
          sx={{
            p: 3,
            borderRadius: 3,
            boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
          }}
        >
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
            Claim Lifecycle Distribution
          </Typography>

          <Box
            sx={{
              width: "100%",
              height: 20,
              borderRadius: 999,
              overflow: "hidden",
              display: "flex",
              backgroundColor: "#e5e7eb",
              mb: 2,
            }}
          >
            <Box
              sx={{
                width: `${getPercent(lifecycle?.ready)}%`,
                backgroundColor: "#0f766e",
              }}
            />
            <Box
              sx={{
                width: `${getPercent(lifecycle?.sent)}%`,
                backgroundColor: "#4338ca",
              }}
            />
            <Box
              sx={{
                width: `${getPercent(lifecycle?.accepted)}%`,
                backgroundColor: "#166534",
              }}
            />
            <Box
              sx={{
                width: `${getPercent(lifecycle?.paid)}%`,
                backgroundColor: "#1d4ed8",
              }}
            />
            <Box
              sx={{
                width: `${getPercent(lifecycle?.denied)}%`,
                backgroundColor: "#b91c1c",
              }}
            />
          </Box>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", md: "repeat(5, 1fr)" },
              gap: 1,
            }}
          >
            <Typography variant="body2">
              Ready: {lifecycle?.ready ?? 0} ({getPercent(lifecycle?.ready)}%)
            </Typography>
            <Typography variant="body2">
              Sent: {lifecycle?.sent ?? 0} ({getPercent(lifecycle?.sent)}%)
            </Typography>
            <Typography variant="body2">
              Accepted: {lifecycle?.accepted ?? 0} (
              {getPercent(lifecycle?.accepted)}%)
            </Typography>
            <Typography variant="body2">
              Paid: {lifecycle?.paid ?? 0} ({getPercent(lifecycle?.paid)}%)
            </Typography>
            <Typography variant="body2">
              Denied: {lifecycle?.denied ?? 0} (
              {getPercent(lifecycle?.denied)}%)
            </Typography>
          </Box>
        </Paper>

        {/* Summary cards */}
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "repeat(3, 1fr)" },
            gap: 2,
          }}
        >
          <Card
            sx={{
              borderRadius: 3,
              boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
            }}
          >
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Claims in Queue
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {summary.totalClaims}
              </Typography>
            </CardContent>
          </Card>

          <Card
            sx={{
              borderRadius: 3,
              boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
            }}
          >
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Filtered Total Charge
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {formatMoney(summary.filteredCharge)}
              </Typography>
            </CardContent>
          </Card>

          <Card
            sx={{
              borderRadius: 3,
              boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
            }}
          >
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                Filtered Denials
              </Typography>
              <Typography
                variant="h4"
                sx={{ fontWeight: 700, color: "error.main" }}
              >
                {summary.filteredDenied}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Filters */}
        <Paper
          sx={{
            p: 3,
            borderRadius: 3,
            boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
            position: "sticky",
            top: 0,
            zIndex: 10,
          }}
        >
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", md: "2fr 1fr 1fr 1fr" },
              gap: 2,
            }}
          >
            <TextField
              fullWidth
              label="Search"
              placeholder="Patient, MRN, billing cycle, payer"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <TextField
              fullWidth
              label="Status"
              select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="ALL">All Statuses</MenuItem>
              <MenuItem value="READY">Ready</MenuItem>
              <MenuItem value="SENT">Sent</MenuItem>
              <MenuItem value="ACCEPTED">Accepted</MenuItem>
              <MenuItem value="PAID">Paid</MenuItem>
              <MenuItem value="DENIED">Denied</MenuItem>
            </TextField>

            <TextField
              fullWidth
              label="Tenant"
              select
              value={tenantFilter}
              onChange={(e) => setTenantFilter(e.target.value)}
            >
              <MenuItem value="ALL">All Tenants</MenuItem>
              {tenants.map((tenant) => (
                <MenuItem key={tenant.tenant_id} value={tenant.tenant_id}>
                  {tenant.display_name || tenant.legal_name || tenant.tenant_id}
                </MenuItem>
              ))}
            </TextField>

            <Button
              fullWidth
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={handleExportFiltered}
              sx={{ minHeight: 56 }}
              disabled={filteredRows.length === 0}
            >
              Export All
            </Button>
          </Box>
        </Paper>

        {/* Claims table */}
        <Paper
          sx={{
            borderRadius: 3,
            boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
            overflow: "hidden",
          }}
        >
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: "#f8fafc" }}>
                  <TableCell>
                    <strong>Patient</strong>
                  </TableCell>
                  <TableCell>
                    <strong>MRN</strong>
                  </TableCell>
                  <TableCell>
                    <strong>Billing Cycle</strong>
                  </TableCell>
                  <TableCell>
                    <strong>Payer</strong>
                  </TableCell>
                  <TableCell>
                    <strong>Service Date</strong>
                  </TableCell>
                  <TableCell>
                    <strong>Total Charge</strong>
                  </TableCell>
                  <TableCell>
                    <strong>Status</strong>
                  </TableCell>
                  <TableCell align="right">
                    <strong>Action</strong>
                  </TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {queueLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Box sx={{ py: 4 }}>
                        <CircularProgress size={28} />
                      </Box>
                    </TableCell>
                  </TableRow>
                ) : filteredRows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      No claims match the current filters.
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRows.map((row, index) => (
                    <TableRow
                      key={`${row.billing_cycle_id}-${row.patient_id}`}
                      ref={index === 0 ? firstFilteredRowRef : null}
                      onClick={() =>
                        setSelectedClaim({
                          patient_id: row.patient_id,
                          billing_cycle_id: row.billing_cycle_id,
                        })
                      }
                      sx={{
                        cursor: "pointer",
                        transition: "background-color 0.3s ease",
                        "&:hover": { backgroundColor: "#f8fafc" },
                        ...(row.status === "DENIED" && {
                          backgroundColor: "#FEF2F2",
                        }),
                        ...(selectedClaim?.patient_id === row.patient_id &&
                          selectedClaim?.billing_cycle_id ===
                            row.billing_cycle_id && {
                            outline: "2px solid #2563eb",
                            outlineOffset: "-2px",
                          }),
                      }}
                    >
                      <TableCell>{row.patient_name || row.patient_id}</TableCell>
                      <TableCell>{row.patient_mrn || "-"}</TableCell>
                      <TableCell>{row.billing_cycle_id}</TableCell>
                      <TableCell>{row.payer_name || "-"}</TableCell>
                      <TableCell>{formatDate(row.service_date)}</TableCell>
                      <TableCell>{formatMoney(row.total_charge)}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={row.status}
                          color={getStatusColor(row.status)}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          variant="outlined"
                          startIcon={<DownloadIcon />}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleExport(row);
                          }}
                          disabled={row.status !== "READY"}
                        >
                          Export
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {/* Audit panel */}
        <BillingAuditHistoryPanel
          patientId={selectedClaim?.patient_id}
          billingCycleId={selectedClaim?.billing_cycle_id}
        />
      </Box>
    </Container>
  );
}
