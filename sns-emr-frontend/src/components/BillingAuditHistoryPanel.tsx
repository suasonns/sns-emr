import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  MenuItem,
  Paper,
  TextField,
  Typography,
} from "@mui/material";

import api from "../api/client";

type AuditEvent = {
  audit_id: string;
  timestamp: string;
  event_type: string;
  patient_id: string;
  billing_cycle_id: string;
  actor: string;
  previous_status?: string | null;
  new_status?: string | null;
  reason?: string | null;
  claim_control_number?: string | null;
  details?: Record<string, unknown>;
};

type Props = {
  patientId?: string;
  billingCycleId?: string;
};

function getSeverity(event: AuditEvent): "success" | "warning" | "error" | "info" | "default" {
  const eventType = event.event_type.toUpperCase();
  const nextStatus = (event.new_status || "").toUpperCase();

  if (nextStatus === "DENIED" || eventType.includes("DENIED")) return "error";
  if (nextStatus === "PAID") return "success";
  if (nextStatus === "ACCEPTED") return "success";
  if (nextStatus === "SENT" || eventType.includes("EXPORTED")) return "info";
  if (eventType.includes("WARNING")) return "warning";

  return "default";
}

function formatEventLabel(eventType: string): string {
  return eventType
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\w/g, (char) => char.toUpperCase());
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default function BillingAuditHistoryPanel({
  patientId,
  billingCycleId,
}: Props) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [eventTypeFilter, setEventTypeFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  const loadHistory = async () => {
    if (!patientId || !billingCycleId) {
      setEvents([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const res = await api.get<AuditEvent[]>("/billing/audit-history", {
        params: {
          patient_id: patientId,
          billing_cycle_id: billingCycleId,
        },
      });

      setEvents(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error("Audit history load error:", err);
      setError("Failed to load audit history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadHistory();
  }, [patientId, billingCycleId]);

  const eventTypeOptions = useMemo(() => {
    const unique = Array.from(new Set(events.map((event) => event.event_type))).sort();
    return ["ALL", ...unique];
  }, [events]);

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      const severity = getSeverity(event);
      const normalizedSearch = search.trim().toLowerCase();

      const eventTypeOk =
        eventTypeFilter === "ALL" || event.event_type === eventTypeFilter;

      const severityOk =
        severityFilter === "ALL" || severity === severityFilter.toLowerCase();

      const searchOk =
        normalizedSearch.length === 0 ||
        event.actor.toLowerCase().includes(normalizedSearch) ||
        event.event_type.toLowerCase().includes(normalizedSearch) ||
        (event.reason || "").toLowerCase().includes(normalizedSearch) ||
        (event.claim_control_number || "").toLowerCase().includes(normalizedSearch);

      return eventTypeOk && severityOk && searchOk;
    });
  }, [events, eventTypeFilter, severityFilter, search]);

  return (
    <Paper
      sx={{
        p: 3,
        borderRadius: 3,
        boxShadow: "0 10px 30px rgba(15, 23, 42, 0.08)",
      }}
    >
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2, gap: 2, flexWrap: "wrap" }}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Claim Audit History
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Timeline of export and status change events for the selected claim.
          </Typography>
        </Box>

        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr 1fr" }, gap: 2, minWidth: { xs: "100%", md: 560 } }}>
          <TextField
            size="small"
            label="Search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Actor, reason, control #"
          />

          <TextField
            size="small"
            select
            label="Event Type"
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
          >
            {eventTypeOptions.map((value) => (
              <MenuItem key={value} value={value}>
                {value === "ALL" ? "All Event Types" : formatEventLabel(value)}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            size="small"
            select
            label="Severity"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <MenuItem value="ALL">All Severities</MenuItem>
            <MenuItem value="INFO">Info</MenuItem>
            <MenuItem value="SUCCESS">Success</MenuItem>
            <MenuItem value="WARNING">Warning</MenuItem>
            <MenuItem value="ERROR">Error</MenuItem>
            <MenuItem value="DEFAULT">Default</MenuItem>
          </TextField>
        </Box>
      </Box>

      {!patientId || !billingCycleId ? (
        <Typography variant="body2" color="text.secondary">
          Select a claim row to view export and status history.
        </Typography>
      ) : loading ? (
        <Box sx={{ py: 4, display: "flex", justifyContent: "center" }}>
          <CircularProgress size={28} />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : filteredEvents.length === 0 ? (
        <Alert severity="info">No audit events match the current filters.</Alert>
      ) : (
        <Box sx={{ position: "relative", mt: 1, pl: 2 }}>
          <Box
            sx={{
              position: "absolute",
              top: 12,
              bottom: 12,
              left: 12,
              width: 2,
              backgroundColor: "#dbeafe",
            }}
          />

          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {filteredEvents.map((event) => {
              const severity = getSeverity(event);

              return (
                <Box
                  key={event.audit_id}
                  sx={{
                    position: "relative",
                    ml: 2,
                    p: 2,
                    border: "1px solid #e5e7eb",
                    borderRadius: 2,
                    backgroundColor: "#fafafa",
                  }}
                >
                  <Box
                    sx={{
                      position: "absolute",
                      left: -20,
                      top: 18,
                      width: 12,
                      height: 12,
                      borderRadius: "50%",
                      backgroundColor:
                        severity === "error"
                          ? "#dc2626"
                          : severity === "success"
                          ? "#16a34a"
                          : severity === "warning"
                          ? "#d97706"
                          : severity === "info"
                          ? "#2563eb"
                          : "#6b7280",
                      border: "2px solid white",
                      boxShadow: "0 0 0 2px #dbeafe",
                    }}
                  />

                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 2, flexWrap: "wrap" }}>
                    <Box>
                      <Typography variant="body1" sx={{ fontWeight: 700 }}>
                        {formatEventLabel(event.event_type)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatTimestamp(event.timestamp)}
                      </Typography>
                    </Box>

                    <Chip size="small" label={severity.toUpperCase()} color={severity} />
                  </Box>

                  <Box sx={{ mt: 1.5, display: "grid", gap: 0.75 }}>
                    <Typography variant="body2">
                      <strong>Actor:</strong> {event.actor}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Status:</strong> {event.previous_status || "-"} → {event.new_status || "-"}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Reason:</strong> {event.reason || "-"}
                    </Typography>
                    {event.claim_control_number && (
                      <Typography variant="body2">
                        <strong>Control #:</strong> {event.claim_control_number}
                      </Typography>
                    )}
                  </Box>
                </Box>
              );
            })}
          </Box>
        </Box>
      )}
    </Paper>
  );
}
