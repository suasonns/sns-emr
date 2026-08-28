import { useEffect, useState } from "react";
import { Box, Chip, Tooltip } from "@mui/material";
import CloudOffIcon from "@mui/icons-material/CloudOff";
import CloudDoneIcon from "@mui/icons-material/CloudDone";
import CloudSyncIcon from "@mui/icons-material/CloudSync";
import { isOnline, subscribeConnectivity } from "./networkStatus";
import { subscribeSyncState, getSyncState, type SyncState } from "./syncManager";

// Small, always-visible indicator of offline/sync state so an RN working
// without a signal for hours has continuous, honest feedback that their
// documentation is captured locally and will sync automatically -- rather
// than silently wondering whether their work "went through."
export default function OfflineStatusBadge() {
  const [online, setOnline] = useState(isOnline());
  const [syncState, setSyncState] = useState<SyncState>(getSyncState());

  useEffect(() => {
    const unsubOnline = subscribeConnectivity(setOnline);
    const unsubSync = subscribeSyncState(setSyncState);
    return () => {
      unsubOnline();
      unsubSync();
    };
  }, []);

  if (online && syncState.pendingCount === 0 && !syncState.syncing) {
    return null; // nothing to report -- fully synced and online
  }

  let label: string;
  let icon: React.ReactElement;
  let color: "warning" | "info" | "success" = "info";

  if (!online) {
    label =
      syncState.pendingCount > 0
        ? `Offline — ${syncState.pendingCount} item${syncState.pendingCount === 1 ? "" : "s"} will sync automatically`
        : "Offline — documentation is saved on this device";
    icon = <CloudOffIcon fontSize="small" />;
    color = "warning";
  } else if (syncState.syncing) {
    label = `Syncing ${syncState.pendingCount} item${syncState.pendingCount === 1 ? "" : "s"}…`;
    icon = <CloudSyncIcon fontSize="small" />;
    color = "info";
  } else {
    label = `${syncState.pendingCount} item${syncState.pendingCount === 1 ? "" : "s"} pending sync`;
    icon = <CloudSyncIcon fontSize="small" />;
    color = "info";
  }

  return (
    <Box
      sx={{
        position: "fixed",
        bottom: 16,
        right: 16,
        zIndex: 2000,
      }}
    >
      <Tooltip
        title={
          online
            ? "Your work is saved locally and syncing to the chart now."
            : "No connectivity. Everything you document is saved on this device and will sync automatically once you're back in range — nothing is lost."
        }
      >
        <Chip icon={icon} label={label} color={color} variant="filled" />
      </Tooltip>
    </Box>
  );
}

// Re-exported so callers only need CloudDoneIcon when they want to show a
// one-off "fully synced" confirmation toast elsewhere in the app.
export { CloudDoneIcon };
