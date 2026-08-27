import React from 'react';
import { COLORS, S } from '../design';

function EmptyStateCard({ title, description, subtitle }) {
  return (
    <div style={{ ...S.card, minHeight: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
      <div style={{ maxWidth: 540 }}>
        <div style={{ width: 56, height: 56, borderRadius: 999, background: `${COLORS.teal}18`, color: COLORS.teal, display: 'grid', placeItems: 'center', fontSize: 24, fontWeight: 700, margin: '0 auto 16px' }}>
          ⏱
        </div>
        <h3 style={{ fontSize: 18, fontWeight: 700, color: COLORS.textPrimary, margin: '0 0 8px' }}>{title}</h3>
        <p style={{ fontSize: 13, lineHeight: 1.6, color: COLORS.muted, margin: '0 0 8px' }}>{description}</p>
        {subtitle ? <p style={{ fontSize: 12, color: COLORS.dim, margin: 0 }}>{subtitle}</p> : null}
      </div>
    </div>
  );
}

export default function Scheduling() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: COLORS.white, margin: 0 }}>Scheduling</h1>
          <p style={S.pageSubtitle}>Coordinate clinician visits, manage assignments, and track visit completion across all active patients.</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={S.btnOutline}>Export Grid</button>
          <button style={S.btn(COLORS.teal)}>+ Schedule Visit</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 24, marginBottom: 24 }}>
        <EmptyStateCard
          title="Tenant-wide visit calendar unavailable"
          description="Visit scheduling is not wired to a live calendar backend yet."
          subtitle="Use patient charts to review real visit history and discipline assignments where those records are available."
        />

        <div style={S.card}>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.textPrimary, margin: '0 0 10px' }}>Current status</h3>
          <p style={{ fontSize: 13, lineHeight: 1.6, color: COLORS.muted, margin: '0 0 12px' }}>
            This workspace no longer shows fabricated visit counts, patient names, clinician assignments, or schedule times.
          </p>
          <div style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 14 }}>
            <p style={{ fontSize: 12, fontWeight: 700, color: COLORS.textPrimary, margin: '0 0 6px' }}>What is available now</p>
            <p style={{ fontSize: 12, color: COLORS.muted, margin: 0 }}>
              Patient-specific visit data remains available in the chart experience until a real agency-wide scheduling feed is implemented.
            </p>
          </div>
        </div>
      </div>

      <EmptyStateCard
        title="Staff availability and caseload metrics unavailable"
        description="Staff availability and caseload dashboards are not backed by a live tenant-wide scheduling model yet."
      />
    </div>
  );
}
