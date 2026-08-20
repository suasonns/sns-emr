import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { COLORS, S } from '../design';
import { changePassword, logout } from '../../api/auth';
import { getCurrentUser, setCurrentUser } from '../../api/session';

const initialSettings = {
  platformName: 'Grace Hospice Care',
  supportEmail: 'support@gracehospice.com',
  maintenanceMode: false,
  backupSchedule: 'Daily at 2:00 AM',
  faxEnabled: true,
  smsAlerts: true,
};

const AGENCY_MANAGEMENT_ROLES = ['ADMIN', 'ADMINISTRATOR', 'CLINICALADMIN', 'DPCS', 'DPCSADMIN', 'SUPERADMIN'];

function normalizeRole(value) {
  return String(value ?? '').trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
}

export default function Settings() {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();
  const normalizedRole = normalizeRole(currentUser?.role);
  const canManageAgency = AGENCY_MANAGEMENT_ROLES.some((role) => normalizedRole.includes(role));
  const [settings, setSettings] = useState(initialSettings);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const agencyOptions = useMemo(() => {
    const canonical = [
      { id: '01271980-0000-0000-0000-000005101977', name: 'Love & Faith Hospice Services, Inc.' },
      { id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', name: 'Angela Hospice (Training)' },
      { id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', name: 'Silva Hospice (Training)' },
      { id: '5224ceb6-e29d-4841-858e-e77f1b67fe65', name: 'Dev Tenant A' },
      { id: '85282f8b-fd5b-45e6-bb82-45394ef7a2f8', name: 'Dev Tenant B' },
    ];

    const stored = (() => {
      try {
        return JSON.parse(localStorage.getItem('sns-agency-options') || 'null');
      } catch {
        return null;
      }
    })();

    const fallback = Array.isArray(stored) && stored.length ? stored : canonical;

    if (!Array.isArray(stored) || !stored.length) {
      localStorage.setItem('sns-agency-options', JSON.stringify(fallback));
    }

    return fallback;
  }, []);

  const [activeAgency, setActiveAgency] = useState(() => {
    const stored = localStorage.getItem('sns-active-agency');
    const canonicalId = '01271980-0000-0000-0000-000005101977';
    if (stored && agencyOptions.some((agency) => agency.id === stored)) {
      return stored;
    }
    const nextAgencyId = currentUser?.tenant_id || canonicalId;
    localStorage.setItem('sns-active-agency', nextAgencyId);
    return nextAgencyId;
  });

  const fieldStyle = {
    width: '100%', background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8,
    color: COLORS.white, padding: '10px 12px', fontSize: 13,
  };

  const handlePasswordChange = async (event) => {
    event.preventDefault();
    setError('');
    setStatus('');

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New password and confirmation do not match.');
      return;
    }

    setLoading(true);
    try {
      await changePassword(currentPassword, newPassword);
      setStatus('Password updated successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update password.');
    } finally {
      setLoading(false);
    }
  };

  const handleAgencyChange = (event) => {
    const nextAgencyId = event.target.value;
    setActiveAgency(nextAgencyId);
    localStorage.setItem('sns-active-agency', nextAgencyId);

    const nextAgency = agencyOptions.find((agency) => agency.id === nextAgencyId) || agencyOptions[0];
    if (!currentUser) return;

    const updatedUser = {
      ...currentUser,
      tenant_id: nextAgency?.id || currentUser.tenant_id,
      tenant_name: nextAgency?.name || currentUser.tenant_name,
    };

    setCurrentUser(updatedUser);
    setStatus(`Active agency set to ${nextAgency?.name || 'current agency'}.`);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
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

      <div style={{ ...S.card, marginTop: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Account</h3>
        <div style={{ display: 'grid', gap: 14 }}>
        {canManageAgency ? (
          <label>
            <div style={{ color: COLORS.muted, fontSize: 12, marginBottom: 6 }}>Active agency</div>
            <select value={activeAgency} onChange={handleAgencyChange} style={fieldStyle}>
              {agencyOptions.map((agency) => (
                <option key={agency.id} value={agency.id}>{agency.name}</option>
              ))}
            </select>
          </label>
        ) : (
          <div style={{ color: COLORS.muted, fontSize: 12, lineHeight: 1.5 }}>
            Agency selection is managed by the hospice administrator or DPCS for this tenant.
          </div>
        )}

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button type="button" onClick={handleLogout} style={{ ...S.btn('#ef4444'), minWidth: 140 }}>
            Log out
          </button>
        </div>

        {status ? <div style={{ color: '#86efac', fontSize: 12 }}>{status}</div> : null}
      </div>
      </div>

      <div style={{ ...S.card, marginTop: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Change Password</h3>
        <form onSubmit={handlePasswordChange} style={{ display: 'grid', gap: 14 }}>
          <input type="password" placeholder="Current password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} style={fieldStyle} />
          <input type="password" placeholder="New password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} style={fieldStyle} />
          <input type="password" placeholder="Confirm new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} style={fieldStyle} />
          {error ? <div style={{ color: '#fca5a5', fontSize: 12 }}>{error}</div> : null}
          {status ? <div style={{ color: '#86efac', fontSize: 12 }}>{status}</div> : null}
          <button type="submit" disabled={loading} style={{ ...S.btn(COLORS.teal), cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}>
            {loading ? 'Updating...' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  );
}
