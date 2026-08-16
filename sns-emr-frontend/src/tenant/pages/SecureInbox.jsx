import React from 'react';
import { COLORS, S } from '../design';

const MESSAGES = [
  { from: 'MD Office', subject: 'Updated orders for Martha Stevens', time: '08:14 AM', unread: true, tone: COLORS.teal },
  { from: 'Family Member', subject: 'Question about care plan update', time: 'Yesterday', unread: true, tone: COLORS.orange },
  { from: 'Clinical Team', subject: 'New visit note requires cosign', time: 'Mon', unread: false, tone: COLORS.blue },
  { from: 'Billing', subject: 'Claim status update', time: 'Sun', unread: false, tone: COLORS.green },
];

export default function SecureInbox() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.pageTitle}>Secure Inbox</h1>
          <p style={S.pageSubtitle}>Review secure messages, escalations, and team communication logs.</p>
        </div>
        <button style={S.btn(COLORS.teal)}>Compose Message</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 24 }}>
        <div style={S.card}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Folders</h3>
          {['Inbox', 'Unread', 'Flagged', 'Sent', 'Archive'].map((folder, i) => (
            <div key={folder} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              background: i === 0 ? `${COLORS.teal}12` : 'transparent',
              border: i === 0 ? `1px solid ${COLORS.teal}55` : `1px solid ${COLORS.border}`,
              borderRadius: 8, padding: '10px 12px', marginBottom: 8,
              color: i === 0 ? COLORS.white : COLORS.muted,
            }}>
              <span>{folder}</span>
              <span style={{ fontSize: 11, color: i === 0 ? COLORS.teal : COLORS.dim }}>{i === 0 ? '12' : '0'}</span>
            </div>
          ))}
        </div>

        <div style={S.card}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.white, margin: '0 0 16px' }}>Latest messages</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {MESSAGES.map((message) => (
              <div key={`${message.from}-${message.subject}`} style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: message.tone, display: 'inline-block' }} />
                    <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.white }}>{message.from}</span>
                  </div>
                  <span style={{ fontSize: 11, color: COLORS.dim }}>{message.time}</span>
                </div>
                <p style={{ margin: 0, color: message.unread ? COLORS.textPrimary : COLORS.muted, fontSize: 13 }}>{message.subject}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
