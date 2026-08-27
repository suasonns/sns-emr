import { Box, Paper, Typography } from "@mui/material";

// Dark metric-card grid from the Figma reference: uppercase gray label,
// large colored number, one-line caption. Used on Dashboard, Visits & Notes,
// POC & Certifications, and NOE Tracking.
export type MetricCardDef = {
  label: string;
  value: string;
  caption: string;
  color?: string;
};

export function MetricCardRow({ metrics }: { metrics: MetricCardDef[] }) {
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: `repeat(${metrics.length}, 1fr)`,
        gap: 2,
        mb: 2.5,
        "@media (max-width: 900px)": { gridTemplateColumns: "1fr 1fr" },
      }}
    >
      {metrics.map((m) => (
        <Paper
          key={m.label}
          variant="outlined"
          sx={{
            bgcolor: "#0f1b2d",
            borderColor: "#1f3a5c",
            borderRadius: 2,
            p: 2,
          }}
        >
          <Typography sx={{ fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, color: "#7f97b3" }}>
            {m.label.toUpperCase()}
          </Typography>
          <Typography sx={{ fontSize: 26, fontWeight: 800, color: m.color || "#fff", lineHeight: 1.3 }}>
            {m.value}
          </Typography>
          <Typography sx={{ fontSize: 11.5, color: "#7f97b3" }}>{m.caption}</Typography>
        </Paper>
      ))}
    </Box>
  );
}
