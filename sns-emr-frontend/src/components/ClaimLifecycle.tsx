import { useEffect, useState } from "react";
import { Alert, Box, Paper, Typography } from "@mui/material";
import axios from "axios";

type ClaimLifecycleResponse = {
  ready: number;
  sent: number;
  accepted: number;
  paid: number;
  denied: number;
};

export default function ClaimLifecycle() {
  const [data, setData] = useState<ClaimLifecycleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setAuthError(false);
        setLoadError(null);

        const res = await axios.get<ClaimLifecycleResponse>(
          "/dashboard/claim-lifecycle",
          {
            withCredentials: true,
          }
        );

        setData(res.data);
      } catch (err: any) {
        const status = err?.response?.status;

        if (status === 401) {
          setAuthError(true);
          setData(null);
          return;
        }

        setLoadError("Failed to load claim lifecycle.");
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  if (loading) {
    return (
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Loading claim lifecycle...
        </Typography>
      </Paper>
    );
  }

  if (authError) {
    return (
      <Alert severity="warning" sx={{ mb: 3 }}>
        Claim lifecycle is unavailable because the session is not authenticated.
      </Alert>
    );
  }

  if (loadError) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {loadError}
      </Alert>
    );
  }

  if (!data) {
    return (
      <Alert severity="info" sx={{ mb: 3 }}>
        No claim lifecycle data available.
      </Alert>
    );
  }

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Claim Lifecycle
      </Typography>

      <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
        <Typography>Ready: {data.ready}</Typography>
        <Typography>Sent: {data.sent}</Typography>
        <Typography>Accepted: {data.accepted}</Typography>
        <Typography>Paid: {data.paid}</Typography>
        <Typography>Denied: {data.denied}</Typography>
      </Box>
    </Paper>
  );
}
