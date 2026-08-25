import { Box, Paper, Typography } from "@mui/material";

// Honest placeholder for Figma-designed nav items that don't have real
// backend data wired yet (Claims / Denials & Appeals / Eligibility /
// Payment Posting / Reports). Per this project's standing "never fabricate
// dashboard data" policy, these show an explicit not-yet-available state
// instead of the mock numbers from the Figma mockups.
export default function ComingSoonPage({ title, note }: { title: string; note?: string }) {
  return (
    <Box>
      <Typography sx={{ fontSize: 20, fontWeight: 800, color: "#0f172a", mb: 2 }}>{title}</Typography>
      <Paper
        variant="outlined"
        sx={{
          p: 4,
          borderRadius: 2,
          borderStyle: "dashed",
          borderColor: "#cbd5e1",
          bgcolor: "#fff",
          textAlign: "center",
        }}
      >
        <Typography sx={{ fontWeight: 700, color: "#334155", mb: 1 }}>Not available yet</Typography>
        <Typography sx={{ fontSize: 13.5, color: "#64748b", maxWidth: 520, mx: "auto" }}>
          {note ||
            "This page is on the implementation plan but the real backend data source hasn't been built yet. It will not show placeholder or sample numbers until it is wired to real records."}
        </Typography>
      </Paper>
    </Box>
  );
}
