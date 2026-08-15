import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Paper,
  TextField,
  Typography,
} from "@mui/material";

import { fetchClinicalAlerts, type ClinicalAlertsResponse } from "../api/dashboard";
import { getCurrentUser } from "../api/session";
import PortalShell from "../components/PortalShell";
import { portalTypography } from "../styles/portalTypography";
type AlertPriority = "Critical" | "High" | "Medium";

const FILTERS = ["All Open", "Critical", "High", "Medium", "Resolved Logs"] as const;
const C = {
  navy: "#1f4a78",
  teal: "#10b7a2",
  tealDark: "#0f766e",
  tealLight: "#ccfbf1",
  white: "#ffffff",
  slate200: "#dbe5ee",
  slate500: "#64748b",
  gray100: "#f3f4f6",
  gray200: "#e5e7eb",
  gray500: "#6b7280",
  gray600: "#4b5563",
  gray800: "#1f2937",
  blue: "#2563eb",
  blueLight: "#dbeafe",
  green: "#059669",
  greenLight: "#dcfce7",
  amber: "#f59e0b",
  amberLight: "#fef3c7",
  red: "#dc2626",
  redLight: "#fee2e2",
};

function PriorityPill({ priority }: { priority: AlertPriority }) {
  return (
    <Box
      sx={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        px: 1,
        height: 18,
        borderRadius: 0.75,
        fontSize: 10,
        fontWeight: 800,
        color: priority === "Critical" ? C.red : priority === "High" ? C.amber : C.blue,
        background: priority === "Critical" ? C.redLight : priority === "High" ? C.amberLight : C.blueLight,
      }}
    >
      {priority}
    </Box>
  );
}

function normalizePriority(value: string): AlertPriority {
  const normalized = value.toLowerCase();
  if (normalized === "critical") return "Critical";
  if (normalized === "high") return "High";
  return "Medium";
}

export default function ClinicalAlertsDataPage() {
  const workspaceName = getCurrentUser()?.tenant_name ?? "Love & Faith Hospice Services Inc.";
  const [data, setData] = useState<ClinicalAlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<(typeof FILTERS)[number]>("All Open");

  useEffect(() => {
    let mounted = true;

    fetchClinicalAlerts()
      .then((result) => {
        if (mounted) setData(result);
      })
      .catch(() => {
        if (mounted) setError("Unable to load live clinical alerts.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const alerts = data?.alerts ?? [];

    return alerts.filter((alert) => {
      const matchesQuery =
        !q ||
        alert.alert_type.toLowerCase().includes(q) ||
        alert.patient_name.toLowerCase().includes(q) ||
        alert.description.toLowerCase().includes(q);
      if (!matchesQuery) return false;
      if (activeFilter === "All Open") return alert.status === "Open";
      if (activeFilter === "Resolved Logs") return alert.status !== "Open";
      return normalizePriority(alert.priority) === activeFilter;
    });
  }, [activeFilter, data?.alerts, query]);

  const metrics = useMemo(() => {
    const map = new Map((data?.metrics ?? []).map((metric) => [metric.key, metric.value]));
    return {
      open: map.get("open_alerts") ?? 0,
      critical: map.get("critical_alerts") ?? 0,
      resolved: map.get("resolved_alerts") ?? 0,
    };
  }, [data?.metrics]);

  return (
    <PortalShell activeTab="Clinical Alerts">
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 2, flexWrap: "wrap" }}>
          <Box>
        <Typography sx={{ fontSize: portalTypography.title, fontWeight: 800, color: C.gray800, lineHeight: 1.05, fontFamily: "'Inter', sans-serif" }}>
              Clinical Alerts Center Workspace
            </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap", mt: 0.7 }}>
              <Typography variant="body2" color="text.secondary" sx={{ fontFamily: "'Inter', sans-serif", fontSize: portalTypography.subtitle }}>
                Active Agency Workspace:
              </Typography>
              <Chip label={workspaceName} size="small" sx={{ background: C.tealLight, color: C.tealDark, fontWeight: 700, height: 24, fontFamily: "'Inter', sans-serif" }} />
            </Box>
          </Box>
      <Typography variant="body2" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 0.8, pt: 0.2, fontFamily: "'Inter', sans-serif", fontSize: portalTypography.subtitle }}>
            <Box component="span" sx={{ width: 8, height: 8, borderRadius: "50%", background: C.slate500 }} />
            Last synced: Today at 08:30 AM
          </Typography>
        </Box>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" }, gap: 1.25 }}>
          {[
            { label: "Total Open Alerts", value: metrics.open, badge: "Requires clinician review", color: C.navy },
            { label: "Critical Priority", value: metrics.critical, badge: "Immediate action required", color: C.red },
            { label: "Resolved Today", value: metrics.resolved, badge: "Successfully documented", color: C.green },
          ].map((card) => (
            <Paper key={card.label} variant="outlined" sx={{ borderColor: C.gray200, borderRadius: 1.5, p: 1.3, minHeight: 68, background: C.white }}>
              <Typography sx={{ fontSize: portalTypography.small, letterSpacing: 0.3, color: C.slate500, fontWeight: 700, mb: 0.7, fontFamily: "'Inter', sans-serif" }}>
                {card.label.toUpperCase()}
              </Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Typography sx={{ fontSize: 28, fontWeight: 800, color: card.color, lineHeight: 1, fontFamily: "'Inter', sans-serif" }}>
                  {card.value}
                </Typography>
                <Chip
                  label={card.badge}
                  size="small"
                  sx={{
                    height: 20,
                    fontSize: 9.5,
                    fontWeight: 700,
                    color: card.color,
                    background: card.color === C.red ? C.redLight : card.color === C.green ? C.greenLight : C.blueLight,
                  }}
                />
              </Box>
            </Paper>
          ))}
        </Box>

        <Paper variant="outlined" sx={{ borderColor: C.gray200, borderWidth: 2, borderRadius: 2, overflow: "hidden", background: C.white }}>
          <Box sx={{ px: 1.2, py: 1.05, display: "flex", alignItems: "center", gap: 0.8, flexWrap: "wrap", borderBottom: `1px solid ${C.gray200}` }}>
            {FILTERS.map((filter) => (
              <Chip
                key={filter}
                label={filter}
                onClick={() => setActiveFilter(filter)}
                size="small"
                sx={{
                  height: 24,
                  fontWeight: 700,
                  background: activeFilter === filter ? C.teal : C.white,
                  color: activeFilter === filter ? C.white : C.gray800,
                  border: "1px solid",
                  borderColor: activeFilter === filter ? C.teal : C.gray200,
                  fontFamily: "'Inter', sans-serif",
                }}
              />
            ))}
            <Box sx={{ flex: 1 }} />
            <Typography sx={{ fontSize: portalTypography.subtitle, color: C.slate500, fontFamily: "'Inter', sans-serif" }}>
              Logged under Sunset Clinician Protocol
            </Typography>
          </Box>

          <Box sx={{ px: 1.2, py: 1.15, display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap", borderBottom: `1px solid ${C.gray200}` }}>
            <TextField
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search alerts..."
              size="small"
              sx={{ width: { xs: "100%", md: 300 }, "& .MuiOutlinedInput-root": { height: 30, borderRadius: 999, background: C.white } }}
            />
          </Box>

          <Box sx={{ overflowX: "auto" }}>
            <Box sx={{ minWidth: 1100, width: "max-content" }}>
              <Box sx={{ display: "grid", gridTemplateColumns: "90px 170px 170px 360px 130px 120px 160px", px: 2, py: 1, fontSize: portalTypography.tableHeader, color: C.slate500, fontWeight: 700, background: "#f8fafc", borderBottom: `1px solid ${C.gray200}` }}>
                <Box sx={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Priority</Box>
                <Box sx={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Alert Type</Box>
                <Box sx={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Patient Name</Box>
                <Box sx={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Alert Description</Box>
                <Box sx={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Generated</Box>
                <Box sx={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Status</Box>
                <Box sx={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Actions</Box>
              </Box>

              {loading ? (
                <Box sx={{ p: 3, color: "text.secondary" }}>Loading live alert rows...</Box>
              ) : error ? (
                <Box sx={{ p: 3, color: "#b42318" }}>{error}</Box>
              ) : rows.length ? (
                rows.map((alert) => (
                  <Box
                    key={alert.alert_id}
                    sx={{
                      display: "grid",
                      gridTemplateColumns: "90px 170px 170px 360px 130px 120px 160px",
                      px: 2,
                      py: 1,
                      alignItems: "center",
                      borderBottom: `1px solid ${C.gray100}`,
                      fontSize: portalTypography.tableBody,
                      "&:hover": { background: "#fbfdff" },
                    }}
                  >
                    <Box sx={{ minWidth: 0 }}><PriorityPill priority={normalizePriority(alert.priority)} /></Box>
                    <Box sx={{ fontWeight: 700, minWidth: 0, color: C.gray800, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{alert.alert_type}</Box>
                    <Box sx={{ color: C.tealDark, fontWeight: 700, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{alert.patient_name}</Box>
                    <Box sx={{ color: C.gray600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", minWidth: 0 }}>
                      {alert.description}
                    </Box>
                    <Box sx={{ color: C.gray600, fontSize: portalTypography.subtitle, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{alert.generated ?? "—"}</Box>
                    <Box sx={{ color: alert.status === "Open" ? C.tealDark : C.blue, fontWeight: 700, fontSize: portalTypography.subtitle, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {alert.status}
                    </Box>
                    <Box sx={{ display: "flex", gap: 0.6, flexWrap: "wrap", justifyContent: "flex-start", minWidth: 0 }}>
                      <Button size="small" sx={{ height: 22, minWidth: 74, fontSize: portalTypography.chip, fontWeight: 700, background: C.teal, color: C.white, "&:hover": { background: C.tealDark } }}>
                        Acknowledge
                      </Button>
                      <Button size="small" variant="outlined" sx={{ height: 22, minWidth: 70, fontSize: portalTypography.chip, fontWeight: 700 }}>
                        View Chart
                      </Button>
                    </Box>
                  </Box>
                ))
              ) : (
                <Box sx={{ p: 3, color: "text.secondary" }}>No live alerts found.</Box>
              )}
            </Box>
          </Box>
        </Paper>
      </Box>
    </PortalShell>
  );
}
