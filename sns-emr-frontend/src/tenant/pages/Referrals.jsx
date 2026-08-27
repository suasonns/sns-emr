import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { COLORS, S } from '../design';
import { listReferrals, acceptReferral, declineReferral } from '../../api/referrals';
import { setActivePatientId } from '../../utils/activePatient';

const STATUS_TABS = ['PENDING', 'ACCEPTED', 'DECLINED'];

function formatDate(value) {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return value;
  }
}

const statusColor = {
  PENDING: COLORS.orange,
  ACCEPTED: COLORS.green,
  DECLINED: COLORS.red,
};

export default function Referrals({ onPatientCreated }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('PENDING');
  const [referrals, setReferrals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState(null);
  const [declineTargetId, setDeclineTargetId] = useState(null);
  const [declineReason, setDeclineReason] = useState('');

  const load = (status) => {
    setLoading(true);
    setError('');
    listReferrals(status)
      .then((rows) => setReferrals(rows))
      .catch((err) => setError(err?.response?.data?.detail ? String(err.response.data.detail) : 'Failed to load referrals.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load(activeTab);
  }, [activeTab]);

  const handleAccept = async (referral) => {
    setBusyId(referral.id);
    setError('');
    try {
      const result = await acceptReferral(referral.id);
      onPatientCreated?.();
      load(activeTab);
      if (result?.id) {
        setActivePatientId(result.id);
        navigate(`/chart/${encodeURIComponent(result.id)}`);
      }
    } catch (err) {
      setError(err?.response?.data?.detail ? String(err.response.data.detail) : 'Failed to accept referral.');
    } finally {
      setBusyId(null);
    }
  };

  const openDeclineForm = (referral) => {
    setDeclineTargetId(referral.id);
    setDeclineReason('');
  };

  const submitDecline = async (referral) => {
    if (!declineReason.trim()) {
      setError('A decline reason is required.');
      return;
    }
    setBusyId(referral.id);
    setError('');
    try {
      await declineReferral(referral.id, declineReason.trim());
      setDeclineTargetId(null);
      setDeclineReason('');
      load(activeTab);
    } catch (err) {
      setError(err?.response?.data?.detail ? String(err.response.data.detail) : 'Failed to decline referral.');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Referrals</h1>
          <p style={S.pageSubtitle}>Review incoming referrals, then accept to admit or decline with a reason.</p>
        </div>
        <button style={S.btn(COLORS.teal)} onClick={() => load(activeTab)} disabled={loading}>Refresh</button>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '8px 16px',
              borderRadius: 999,
              border: `1px solid ${activeTab === tab ? COLORS.teal : COLORS.border}`,
              background: activeTab === tab ? 'rgba(20,184,166,0.12)' : 'transparent',
              color: activeTab === tab ? COLORS.teal : COLORS.muted,
              fontSize: 12,
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            {tab.charAt(0) + tab.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {error ? (
        <div style={{ marginBottom: 16, padding: '10px 12px', borderRadius: 8, background: 'rgba(220,53,69,0.12)', color: COLORS.red, fontSize: 13 }}>
          {error}
        </div>
      ) : null}

      <div style={S.card}>
        {loading ? (
          <div style={{ color: COLORS.muted }}>Loading referrals…</div>
        ) : referrals.length === 0 ? (
          <div style={{ color: COLORS.muted }}>No {activeTab.toLowerCase()} referrals.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {referrals.map((referral) => (
              <div key={referral.id} style={{ border: `1px solid ${COLORS.border}`, borderRadius: 10, padding: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontWeight: 700, color: COLORS.textPrimary, fontSize: 14 }}>
                      {[referral.first_name, referral.middle_name, referral.last_name].filter(Boolean).join(' ')}
                    </div>
                    <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 2 }}>
                      DOB {formatDate(referral.date_of_birth)} • Referred by {referral.referral_source || 'Unknown source'} on {formatDate(referral.referral_date)}
                    </div>
                    <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 2 }}>
                      Dx: {referral.primary_diagnosis || '—'} • Payer: {referral.primary_payer || '—'}
                    </div>
                    {referral.status === 'DECLINED' && referral.decline_reason ? (
                      <div style={{ fontSize: 12, color: COLORS.red, marginTop: 6 }}>Declined: {referral.decline_reason}</div>
                    ) : null}
                  </div>
                  <span style={{ fontSize: 10, fontWeight: 800, color: statusColor[referral.status] || COLORS.muted, textTransform: 'uppercase' }}>
                    {referral.status}
                  </span>
                </div>

                {referral.status === 'PENDING' ? (
                  <div style={{ marginTop: 12 }}>
                    {declineTargetId === referral.id ? (
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <input
                          type="text"
                          placeholder="Reason for declining"
                          value={declineReason}
                          onChange={(event) => setDeclineReason(event.target.value)}
                          style={{ flex: 1, padding: '8px 10px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.textPrimary, fontSize: 13 }}
                        />
                        <button type="button" style={S.btn(COLORS.red)} disabled={busyId === referral.id} onClick={() => submitDecline(referral)}>
                          Confirm Decline
                        </button>
                        <button type="button" style={S.btnOutline} onClick={() => setDeclineTargetId(null)}>Cancel</button>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button type="button" style={S.btn(COLORS.teal)} disabled={busyId === referral.id} onClick={() => handleAccept(referral)}>
                          {busyId === referral.id ? 'Accepting…' : 'Accept & Admit'}
                        </button>
                        <button type="button" style={S.btnOutline} disabled={busyId === referral.id} onClick={() => openDeclineForm(referral)}>
                          Decline
                        </button>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
