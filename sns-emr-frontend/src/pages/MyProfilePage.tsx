import { useMemo, useState, type ReactNode } from "react";
import { Box, Button, Paper, Switch, TextField, Typography } from "@mui/material";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import DrawOutlinedIcon from "@mui/icons-material/DrawOutlined";
import NotificationsNoneOutlinedIcon from "@mui/icons-material/NotificationsNoneOutlined";

import { getCurrentUser } from "../api/session";
import PortalShell from "../components/PortalShell";

function SectionCard({
  title,
  icon,
  right,
  children,
}: {
  title: string;
  icon: ReactNode;
  right?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Paper
      variant="outlined"
      sx={{
        borderColor: "#dbe5ea",
        borderRadius: 1.5,
        background: "#fff",
        boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
        overflow: "hidden",
      }}
    >
      <Box sx={{ px: 1.25, py: 1, borderBottom: "1px solid #e5edf3", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1.5 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, minWidth: 0 }}>
          <Box sx={{ color: "#0f766e", display: "grid", placeItems: "center" }}>{icon}</Box>
          <Typography sx={{ fontSize: 11, fontWeight: 800, color: "#1f3552" }}>{title}</Typography>
        </Box>
        {right}
      </Box>
      <Box sx={{ p: 1.25 }}>{children}</Box>
    </Paper>
  );
}

function FieldRow({ label, value }: { label: string; value: string }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, py: 0.45, borderBottom: "1px solid #edf2f7" }}>
      <Typography sx={{ fontSize: 10.5, color: "#64748b" }}>{label}</Typography>
      <Typography sx={{ fontSize: 10.5, fontWeight: 700, color: "#1f2937", textAlign: "right", overflowWrap: "anywhere" }}>{value}</Typography>
    </Box>
  );
}

function LabeledInput({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <Box sx={{ display: "grid", gap: 0.35 }}>
      <Typography sx={{ fontSize: 10.5, fontWeight: 700, color: "#6b7280" }}>{label}</Typography>
      <TextField
        value={value}
        onChange={(event) => onChange(event.target.value)}
        type={type}
        size="small"
        fullWidth
        variant="outlined"
        placeholder=""
        sx={{
          "& .MuiOutlinedInput-root": {
            height: 28,
            borderRadius: 1,
            background: "#fff",
            "& input": {
              fontSize: 11,
              py: 0.6,
            },
          },
        }}
      />
    </Box>
  );
}

function ToggleRow({
  title,
  subtitle,
  checked,
  onChange,
}: {
  title: string;
  subtitle: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, py: 0.95, borderBottom: "1px solid #edf2f7" }}>
      <Box sx={{ minWidth: 0 }}>
        <Typography sx={{ fontSize: 10.5, fontWeight: 800, color: "#1f2937" }}>{title}</Typography>
        <Typography sx={{ fontSize: 9.5, color: "#64748b", mt: 0.15 }}>{subtitle}</Typography>
      </Box>
      <Switch
        checked={checked}
        onChange={(_, value) => onChange(value)}
        sx={{
          "& .MuiSwitch-switchBase.Mui-checked": { color: "#10b7a2" },
          "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": { backgroundColor: "#10b7a2" },
        }}
      />
    </Box>
  );
}

export default function MyProfilePage() {
  const user = getCurrentUser();
  const workspaceName = user?.tenant_name ?? "Love & Faith Hospice Services Inc.";
  const displayName = user?.full_name ?? "Signed-in User";
  const role = user?.role === "ADMINISTRATOR" ? "RN Case Manager" : user?.role ?? "Clinical Staff";
  const initials = (displayName.match(/\b\w/g) ?? []).slice(0, 2).join("").toUpperCase() || "SU";

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [smsAlerts, setSmsAlerts] = useState(true);
  const [browserNotifications, setBrowserNotifications] = useState(false);
  const [dailyDigest, setDailyDigest] = useState(true);

  const signatureName = useMemo(() => displayName, [displayName]);

  return (
    <PortalShell activeTab="My Profile">
      <Box sx={{ display: "flex", flexDirection: "column", gap: 1.1 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 2, flexWrap: "wrap" }}>
          <Box>
            <Typography sx={{ fontSize: 16, fontWeight: 800, color: "#1f3552", lineHeight: 1.1 }}>
              My EMR Account Profile
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap", mt: 0.75 }}>
              <Typography sx={{ fontSize: 10.5, color: "#64748b" }}>Active Agency Workspace:</Typography>
              <Box
                sx={{
                  display: "inline-flex",
                  alignItems: "center",
                  px: 1,
                  py: 0.2,
                  borderRadius: 999,
                  background: "#ccfbf1",
                  color: "#0f766e",
                  fontSize: 9.5,
                  fontWeight: 800,
                }}
              >
                {workspaceName}
              </Box>
            </Box>
          </Box>
          <Typography sx={{ fontSize: 10.5, color: "#64748b", display: "flex", alignItems: "center", gap: 0.8, pt: 0.2 }}>
            <Box component="span" sx={{ width: 8, height: 8, borderRadius: "50%", background: "#64748b" }} />
            Last synced: Today at 08:30 AM
          </Typography>
        </Box>

        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "300px 1fr" }, gap: 1.25, alignItems: "start" }}>
          <Box sx={{ display: "grid", gap: 1 }}>
            <Paper
              variant="outlined"
              sx={{
                borderColor: "#dbe5ea",
                borderRadius: 1.5,
                background: "#fff",
                boxShadow: "0 1px 2px rgba(15, 23, 42, 0.04)",
                p: 1.25,
              }}
            >
              <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 0.55 }}>
                <Box
                  sx={{
                    width: 54,
                    height: 54,
                    borderRadius: "50%",
                    background: "#ccfbf1",
                    color: "#0f766e",
                    display: "grid",
                    placeItems: "center",
                    fontSize: 17,
                    fontWeight: 900,
                  }}
                >
                  {initials}
                </Box>
                <Typography sx={{ fontSize: 13.5, fontWeight: 800, color: "#1f2937", textAlign: "center" }}>{displayName}</Typography>
                <Typography sx={{ fontSize: 10.5, color: "#64748b", textAlign: "center" }}>{role}</Typography>
                <Box sx={{ px: 1, py: 0.2, borderRadius: 999, background: "#ccfbf1", color: "#0f766e", fontSize: 9.5, fontWeight: 800 }}>
                  Sunrise Hospice Care
                </Box>
              </Box>
              <Box sx={{ mt: 1.2 }}>
                <FieldRow label="Email" value={user?.email ?? "—"} />
                <FieldRow label="Phone" value="(555) 482-1920" />
                <FieldRow label="Employee ID" value="EMP-98341" />
              </Box>
            </Paper>

            <Button
              variant="outlined"
              fullWidth
              sx={{
                height: 27,
                borderColor: "#ef4444",
                color: "#ef4444",
                fontSize: 9.5,
                fontWeight: 800,
                textTransform: "none",
                background: "#fff",
              }}
            >
              Log Out of Secure EMR Session
            </Button>
          </Box>

          <Box sx={{ display: "grid", gap: 1 }}>
            <SectionCard title="Change Password" icon={<LockOutlinedIcon sx={{ fontSize: 12 }} />}>
              <Box sx={{ display: "grid", gap: 0.9 }}>
                <LabeledInput label="Current Password" value={currentPassword} onChange={setCurrentPassword} type="password" />
                <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" }, gap: 1 }}>
                  <LabeledInput label="New Password" value={newPassword} onChange={setNewPassword} type="password" />
                  <LabeledInput label="Confirm New Password" value={confirmPassword} onChange={setConfirmPassword} type="password" />
                </Box>
                <Box>
                  <Button variant="contained" sx={{ background: "#10b7a2", height: 26, fontSize: 9.5, fontWeight: 800, textTransform: "none", px: 1.2 }}>
                    Update Password
                  </Button>
                </Box>
              </Box>
            </SectionCard>

            <SectionCard
              title="Electronic Clinical Signature"
              icon={<DrawOutlinedIcon sx={{ fontSize: 12 }} />}
              right={
                <Box sx={{ fontSize: 9.5, color: "#0f766e", fontWeight: 800, background: "#dcfce7", px: 1, py: 0.2, borderRadius: 999 }}>
                  Signature on File
                </Box>
              }
            >
              <Box
                sx={{
                  minHeight: 82,
                  borderRadius: 1,
                  border: "1px solid #e5edf3",
                  background: "#f7fafc",
                  display: "grid",
                  placeItems: "center",
                  textAlign: "center",
                  color: "#334155",
                  px: 1.5,
                }}
              >
                <Typography sx={{ fontSize: 17, fontWeight: 700, color: "#1e3a5f", fontFamily: "cursive", lineHeight: 1 }}>{signatureName}</Typography>
                <Typography sx={{ fontSize: 9.5, color: "#94a3b8", mt: 0.4 }}>Digitally Signed for HIPAA EMR Submissions</Typography>
              </Box>
              <Box sx={{ display: "flex", gap: 0.75, flexWrap: "wrap", mt: 1 }}>
                <Button variant="contained" sx={{ background: "#10b7a2", height: 26, fontSize: 9.5, fontWeight: 800, textTransform: "none" }}>
                  Capture New Signature
                </Button>
                <Button variant="outlined" sx={{ height: 26, fontSize: 9.5, fontWeight: 800, textTransform: "none" }}>
                  Clear Area
                </Button>
              </Box>
            </SectionCard>

            <SectionCard title="Secure Portal Notification Preferences" icon={<NotificationsNoneOutlinedIcon sx={{ fontSize: 12 }} />}>
              <ToggleRow
                title="Email Alerts"
                subtitle="Receive secure clinical alerts, QA comments, and messages via email"
                checked={emailAlerts}
                onChange={setEmailAlerts}
              />
              <ToggleRow
                title="SMS Urgent Alerts"
                subtitle="Get real-time text notifications for critical patient and workflow alerts"
                checked={smsAlerts}
                onChange={setSmsAlerts}
              />
              <ToggleRow
                title="Browser Notifications"
                subtitle="Show instant alerts on your desktop when active in other clinical apps"
                checked={browserNotifications}
                onChange={setBrowserNotifications}
              />
              <ToggleRow
                title="Daily Digest Summary"
                subtitle="A comprehensive end-of-day summary email of pending QA alerts and signings"
                checked={dailyDigest}
                onChange={setDailyDigest}
              />
            </SectionCard>
          </Box>
        </Box>
      </Box>
    </PortalShell>
  );
}
