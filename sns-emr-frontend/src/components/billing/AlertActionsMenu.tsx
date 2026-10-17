import { useState } from "react";
import {
  Alert as MuiAlert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Menu,
  MenuItem,
  TextField,
} from "@mui/material";

import {
  ALERT_DISMISSAL_REASON_CODES,
  ALERT_SNOOZE_PRESETS,
  DashboardApiError,
  acknowledgeAlert,
  dismissAlert,
  reassignAlert,
  resolveFacilityCollectionAlert,
  snoozeAlert,
  startAlertProgress,
  type FacilityCollectionAlert,
} from "../../api/dashboard";

const NON_TERMINAL_STATUSES = new Set(["OPEN", "ACKNOWLEDGED", "IN_PROGRESS", "SNOOZED"]);

function summarizeError(error: unknown, fallback: string): string {
  if (error instanceof DashboardApiError) {
    if (error.status === 403) return "Authorization denied for this action.";
    if (error.status === 409) return error.message || "Concurrent update conflict.";
    return error.message || fallback;
  }
  if (error instanceof Error) return error.message || fallback;
  return fallback;
}

type DialogKind = "snooze" | "dismiss" | "reassign" | "resolve" | null;

// The single source of write actions for a facility collection alert.
// Mirrors the six lifecycle endpoints on
// app/billing/api/facility_payment_router.py exactly -- no client-side
// state machine, the backend is the sole authority on legal transitions
// (409 responses are surfaced verbatim via summarizeError).
export default function AlertActionsMenu({
  alert,
  onUpdated,
}: {
  alert: FacilityCollectionAlert;
  onUpdated: (alert: FacilityCollectionAlert) => void;
}) {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [dialogKind, setDialogKind] = useState<DialogKind>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [snoozePreset, setSnoozePreset] = useState<string>(ALERT_SNOOZE_PRESETS[0]);
  const [snoozeNote, setSnoozeNote] = useState("");
  const [dismissReason, setDismissReason] = useState<string>(ALERT_DISMISSAL_REASON_CODES[0]);
  const [dismissComment, setDismissComment] = useState("");
  const [reassignTo, setReassignTo] = useState("");
  const [reassignNote, setReassignNote] = useState("");
  const [resolutionEvidence, setResolutionEvidence] = useState("");

  const canAct = NON_TERMINAL_STATUSES.has(alert.status);

  function closeMenu() {
    setAnchorEl(null);
  }

  function closeDialog() {
    setDialogKind(null);
    setError(null);
  }

  async function run(action: () => Promise<FacilityCollectionAlert>) {
    setBusy(true);
    setError(null);
    try {
      const updated = await action();
      onUpdated(updated);
      setDialogKind(null);
    } catch (err) {
      setError(summarizeError(err, "Unable to complete this action."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Button
        size="small"
        variant="outlined"
        disabled={!canAct}
        onClick={(e) => setAnchorEl(e.currentTarget)}
        sx={{ borderColor: "#334155", color: "#cbd5e1", textTransform: "none", fontWeight: 700 }}
      >
        Actions
      </Button>
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={closeMenu}>
        <MenuItem
          disabled={alert.status !== "OPEN"}
          onClick={() => {
            closeMenu();
            run(() => acknowledgeAlert(alert.id));
          }}
        >
          Acknowledge
        </MenuItem>
        <MenuItem
          onClick={() => {
            closeMenu();
            run(() => startAlertProgress(alert.id));
          }}
        >
          Start Progress
        </MenuItem>
        <MenuItem
          onClick={() => {
            closeMenu();
            setDialogKind("snooze");
          }}
        >
          Snooze
        </MenuItem>
        <MenuItem
          onClick={() => {
            closeMenu();
            setDialogKind("dismiss");
          }}
        >
          Dismiss
        </MenuItem>
        <MenuItem
          onClick={() => {
            closeMenu();
            setDialogKind("resolve");
          }}
        >
          Resolve
        </MenuItem>
        <MenuItem
          onClick={() => {
            closeMenu();
            setDialogKind("reassign");
          }}
        >
          Reassign
        </MenuItem>
      </Menu>

      <Dialog open={dialogKind === "snooze"} onClose={closeDialog} maxWidth="xs" fullWidth>
        <DialogTitle>Snooze Alert</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {error && <MuiAlert severity="error">{error}</MuiAlert>}
          <TextField
            select
            label="Snooze for"
            value={snoozePreset}
            onChange={(e) => setSnoozePreset(e.target.value)}
            size="small"
          >
            {ALERT_SNOOZE_PRESETS.map((preset) => (
              <MenuItem key={preset} value={preset}>
                {preset.replace("_", " ").toLowerCase()}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Note (optional)"
            value={snoozeNote}
            onChange={(e) => setSnoozeNote(e.target.value)}
            size="small"
            multiline
            minRows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog} disabled={busy}>
            Cancel
          </Button>
          <Button
            variant="contained"
            disabled={busy}
            onClick={() => run(() => snoozeAlert(alert.id, snoozePreset, snoozeNote))}
          >
            Snooze
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={dialogKind === "dismiss"} onClose={closeDialog} maxWidth="xs" fullWidth>
        <DialogTitle>Dismiss Alert</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {error && <MuiAlert severity="error">{error}</MuiAlert>}
          <TextField
            select
            label="Reason"
            value={dismissReason}
            onChange={(e) => setDismissReason(e.target.value)}
            size="small"
          >
            {ALERT_DISMISSAL_REASON_CODES.map((code) => (
              <MenuItem key={code} value={code}>
                {code.replace("_", " ").toLowerCase()}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Comment (optional)"
            value={dismissComment}
            onChange={(e) => setDismissComment(e.target.value)}
            size="small"
            multiline
            minRows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog} disabled={busy}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            disabled={busy}
            onClick={() => run(() => dismissAlert(alert.id, dismissReason, dismissComment))}
          >
            Dismiss
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={dialogKind === "resolve"} onClose={closeDialog} maxWidth="xs" fullWidth>
        <DialogTitle>Resolve Alert</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {error && <MuiAlert severity="error">{error}</MuiAlert>}
          <TextField
            label="Resolution evidence"
            value={resolutionEvidence}
            onChange={(e) => setResolutionEvidence(e.target.value)}
            size="small"
            multiline
            minRows={3}
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog} disabled={busy}>
            Cancel
          </Button>
          <Button
            variant="contained"
            disabled={busy || !resolutionEvidence.trim()}
            onClick={() => run(() => resolveFacilityCollectionAlert(alert.id, resolutionEvidence))}
          >
            Resolve
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={dialogKind === "reassign"} onClose={closeDialog} maxWidth="xs" fullWidth>
        <DialogTitle>Reassign Alert</DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 1 }}>
          {error && <MuiAlert severity="error">{error}</MuiAlert>}
          <TextField
            label="Assign to (user ID)"
            value={reassignTo}
            onChange={(e) => setReassignTo(e.target.value)}
            size="small"
            helperText="Leave blank to unassign."
          />
          <TextField
            label="Note"
            value={reassignNote}
            onChange={(e) => setReassignNote(e.target.value)}
            size="small"
            multiline
            minRows={2}
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog} disabled={busy}>
            Cancel
          </Button>
          <Button
            variant="contained"
            disabled={busy || !reassignNote.trim()}
            onClick={() =>
              run(() => reassignAlert(alert.id, reassignTo.trim() || null, reassignNote))
            }
          >
            Reassign
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
