import React, { useState } from 'react';
import { COLORS, S } from '../TenantDashboard';

const initialSettings = {
  platformName: 'Grace Hospice Care',
  supportEmail: 'support@gracehospice.com',
  maintenanceMode: false,
  backupSchedule: 'Daily at 2:00 AM',
  faxEnabled: true,
  smsAlerts: true,
};

export default function Settings() {
  const [settings, setSettings] = useState(initialSettings);

  const fieldStyle = {
    width: '100%', background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8,
    color: COLORS.white, padding: '10px 12px', fontSize: 13,
  };

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>System Settings</h1>
          <p style={S.pageSubtitle}>Manage agency preferences, automation rules, integrations, and operational defaults.</p>
        </div>
        <button style={S.btn(COLORS.teal)}>Save Changes</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div style={S.card}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>General</h3>
          <div style={{ display: 'grid', gap: 14 }}>
            <label>
              <div style={{ color: COLORS.muted, fontSize: 12, marginBottom: 6 }}>Agency Name</div>
              <input value={settings.platformName} onChange={(e) => setSettings({ ...settings, platformName: e.target.value })} style={fieldStyle} />
            </label>
            <label>
              <div style={{ color: COLORS.muted, fontSize: 12, marginBottom: 6 }}>Support Email</div>
              <input value={settings.supportEmail} onChange={(e) => setSettings({ ...settings, supportEmail: e.target.value })} style={fieldStyle} />
            </label>
            <label>
              <div style={{ color: COLORS.muted, fontSize: 12, marginBottom: 6 }}>Backup Schedule</div>
              <select value={settings.backupSchedule} onChange={(e) => setSettings({ ...settings, backupSchedule: e.target.value })} style={fieldStyle}>
                <option>Daily at 2:00 AM</option>
                <option>Twice Daily</option>
                <option>Weekly</option>
              </select>
            </label>
          </div>
        </div>

        <div style={S.card}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Automation & Integrations</h3>
          <div style={{ display: 'grid', gap: 14 }}>
            {[
              ['Maintenance Mode', 'maintenanceMode'],
              ['Faxing Enabled', 'faxEnabled'],
              ['SMS Alerts Active', 'smsAlerts'],
            ].map(([label, key]) => (
              <label key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: `1px solid ${COLORS.border}`, borderRadius: 8, background: COLORS.bg, padding: '12px 14px' }}>
                <span style={{ color: COLORS.textPrimary, fontSize: 13 }}>{label}</span>
                <input
                  type="checkbox"
                  checked={settings[key]}
                  onChange={(e) => setSettings({ ...settings, [key]: e.target.checked })}
                  style={{ width: 18, height: 18 }}
                />
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
