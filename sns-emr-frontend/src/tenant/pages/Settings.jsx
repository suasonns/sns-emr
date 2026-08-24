import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { COLORS, S } from '../design';
import { changePassword, getLinkedAgencies, logout, switchAgency } from '../../api/auth';
import { getCurrentUser } from '../../api/session';

const initialSettings = {
  platformName: 'Grace Hospice Care',
  supportEmail: 'support@gracehospice.com',
  maintenanceMode: false,
  backupSchedule: 'Daily at 2:00 AM',
  faxEnabled: true,
  smsAlerts: true,
};

export default function Settings() {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();
  const [settings, setSettings] = useState(initialSettings);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Real cross-agency identity linking: every other agency this same
  // physical person has a staff account in, matched server-side by SSN
  // (primary) or name + DOB + license (fallback) -- not a hardcoded/mock
  // tenant list. Replaces the old localStorage dev-tenant switcher.
  const [linkedAgencies, setLinkedAgencies] = useState([]);
  const [linkedAgenciesLoading, setLinkedAgenciesLoading] = useState(true);
  const [linkedAgenciesError, setLinkedAgenciesError] = useState('');
  const [switchTarget, setSwitchTarget] = useState(null);
  const [switchPassword, setSwitchPassword] = useState('');
  const [switchError, setSwitchError] = useState('');
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const agencies = await getLinkedAgencies();
        if (!cancelled) setLinkedAgencies(agencies);
      } catch (err) {
        if (!cancelled) setLinkedAgenciesError(err instanceof Error ? err.message : 'Unable to load linked agencies.');
      } finally {
        if (!cancelled) setLinkedAgenciesLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

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

  const openSwitchPrompt = (agency) => {
    setSwitchTarget(agency);
    setSwitchPassword('');
    setSwitchError('');
  };

  const closeSwitchPrompt = () => {
    setSwitchTarget(null);
    setSwitchPassword('');
    setSwitchError('');
  };

  const handleSwitchAgency = async (event) => {
    event.preventDefault();
    if (!switchTarget) return;
    setSwitchError('');
    setSwitching(true);
    try {
      await switchAgency(switchTarget.user_id, switchPassword);
      // switchAgency() already updated the stored session (token + user)
      // to the target agency; reload so the whole app re-reads it fresh.
      window.location.href = '/portal';
    } catch (err) {
      setSwitchError(err instanceof Error ? err.message : 'Unable to switch agency.');
      setSwitching(false);
    }
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
        <div>
          <div style={{ color: COLORS.muted, fontSize: 12, marginBottom: 6 }}>Other agencies you're connected to</div>
          {linkedAgenciesLoading ? (
            <div style={{ color: COLORS.muted, fontSize: 12 }}>Checking for linked agencies...</div>
          ) : linkedAgenciesError ? (
            <div style={{ color: '#fca5a5', fontSize: 12 }}>{linkedAgenciesError}</div>
          ) : linkedAgencies.length === 0 ? (
            <div style={{ color: COLORS.muted, fontSize: 12, lineHeight: 1.5 }}>
              No other agency accounts were found linked to your identity (matched by SSN, or name + date of birth + license number).
            </div>
          ) : (
            <div style={{ display: 'grid', gap: 8 }}>
              {linkedAgencies.map((agency) => (
                <div
                  key={agency.user_id}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: '10px 12px',
                  }}
                >
                  <div>
                    <div style={{ color: COLORS.white, fontSize: 13, fontWeight: 600 }}>{agency.tenant_name}</div>
                    <div style={{ color: COLORS.muted, fontSize: 11 }}>{agency.email}</div>
                  </div>
                  <button type="button" onClick={() => openSwitchPrompt(agency)} style={{ ...S.btn(COLORS.teal), minWidth: 90 }}>
                    Switch
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {switchTarget ? (
          <form
            onSubmit={handleSwitchAgency}
            style={{ display: 'grid', gap: 10, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 14 }}
          >
            <div style={{ color: COLORS.white, fontSize: 13, fontWeight: 700 }}>
              Sign in to {switchTarget.tenant_name}
            </div>
            <div style={{ color: COLORS.muted, fontSize: 12 }}>
              Enter the password for {switchTarget.email} to switch into this agency.
            </div>
            <input
              type="password"
              placeholder="Password"
              autoFocus
              value={switchPassword}
              onChange={(e) => setSwitchPassword(e.target.value)}
              style={fieldStyle}
            />
            {switchError ? <div style={{ color: '#fca5a5', fontSize: 12 }}>{switchError}</div> : null}
            <div style={{ display: 'flex', gap: 10 }}>
              <button type="submit" disabled={switching || !switchPassword} style={{ ...S.btn(COLORS.teal), opacity: switching ? 0.7 : 1 }}>
                {switching ? 'Switching...' : 'Switch agency'}
              </button>
              <button type="button" onClick={closeSwitchPrompt} disabled={switching} style={S.btn('#475569')}>
                Cancel
              </button>
            </div>
          </form>
        ) : null}

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
