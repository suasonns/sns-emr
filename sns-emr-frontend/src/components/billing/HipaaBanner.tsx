import { Box, Typography } from "@mui/material";
import ShieldOutlinedIcon from "@mui/icons-material/ShieldOutlined";

// Amber left-border HIPAA "minimum necessary" banner matching the Figma
// reference (used identically on every billing page there). Kept as a
// single shared component so copy/color never drifts per-page again.
export default function HipaaBanner({ message }: { message?: string }) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "flex-start",
        gap: 1,
        bgcolor: "#fef3c7",
        border: "1px solid #f59e0b",
        borderLeft: "4px solid #f59e0b",
        borderRadius: 1.5,
        px: 2,
        py: 1.2,
        mb: 2.5,
      }}
    >
      <ShieldOutlinedIcon sx={{ color: "#b45309", fontSize: 18, mt: 0.1 }} />
      <Typography sx={{ fontSize: 12, color: "#78350f" }}>
        <Box component="span" sx={{ fontWeight: 800 }}>
          MINIMUM DATA PRINCIPLE ACCESS
        </Box>{" "}
        —{" "}
        {message ??
          "Billing credentials provide view-only status tracking. Access to clinical narratives, subjective clinician comments, and raw medical record files is restricted per HIPAA Minimum Necessary standard."}
      </Typography>
    </Box>
  );
}
