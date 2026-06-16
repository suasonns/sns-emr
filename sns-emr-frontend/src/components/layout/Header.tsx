import { Box, Typography } from "@mui/material";

export default function Header({
  user,
}: {
  user: { role: string; tenant_name?: string };
}) {
  return (
    <Box
      sx={{
        height: 64,
        px: 3,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid #e2e8f0",
        bgcolor: "white",
      }}
    >
      <Typography variant="h6">
        {user.tenant_name || "System Dashboard"}
      </Typography>

      <Typography variant="body2" color="text.secondary">
        Role: {user.role}
      </Typography>
    </Box>
  );
}
