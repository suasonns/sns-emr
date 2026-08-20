import { useCallback, useState } from "react";

const PILOT_STORAGE_KEY = "sns-rnica-command-workspace";

export function getRnIcaCommandWorkspaceEnabled(): boolean {
  const deploymentSetting = import.meta.env.VITE_RNICA_COMMAND_WORKSPACE;
  if (deploymentSetting === "false") {
    return false;
  }

  if (typeof window === "undefined") {
    return deploymentSetting === "true";
  }

  const queryValue = new URLSearchParams(window.location.search).get("workspace");
  if (queryValue === "1" || queryValue === "0") {
    const enabled = queryValue === "1";
    window.localStorage.setItem(PILOT_STORAGE_KEY, enabled ? "enabled" : "disabled");
    return enabled;
  }

  const stored = window.localStorage.getItem(PILOT_STORAGE_KEY);
  if (stored === "enabled" || stored === "disabled") {
    return stored === "enabled";
  }

  return deploymentSetting === "true";
}

export function setRnIcaCommandWorkspaceEnabled(enabled: boolean): void {
  window.localStorage.setItem(PILOT_STORAGE_KEY, enabled ? "enabled" : "disabled");
  const url = new URL(window.location.href);
  url.searchParams.delete("workspace");
  window.history.replaceState(null, "", url);
}

export function useRnIcaCommandWorkspace() {
  const [enabled, setEnabled] = useState(getRnIcaCommandWorkspaceEnabled);
  const disable = useCallback(() => {
    setRnIcaCommandWorkspaceEnabled(false);
    setEnabled(false);
  }, []);

  return { enabled, disable };
}
