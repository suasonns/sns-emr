import React from 'react';
import { COLORS, S } from '../TenantDashboard';

const DAYS = ['Mon 10/24', 'Tue 10/25', 'Wed 10/26', 'Thu 10/27', 'Fri 10/28', 'Sat 10/29', 'Sun 10/30'];
const TIMES = ['08:00 AM', '10:00 AM', '12:00 PM', '02:00 PM', '04:00 PM'];

const GRID = [
  [{ init: 'MS', cl: 'S. Jenkins', color: COLORS.teal }, null, { init: 'JC', cl: 'K. Taylor', color: COLORS.blue }, { init: 'EV', cl: 'S. Jenkins', color: COLORS.teal }, null, null, null],
  [{ init: 'AC', cl: 'R. Chen', color: COLORS.purple }, null, { init: 'DB', cl: 'A. Vance', color: COLORS.orange }, null, { init: 'FS', cl: 'M. Ramirez', color: COLORS.blue }, null, null],
  [{ init: 'JM', cl: 'R. Chen', color: COLORS.purple }, { init: 'MP', cl: 'S. Jenkins', color: COLORS.teal }, null, { init: 'JD', cl: 'S. Jenkins', color: COLORS.teal }, null, null, null],
  [{ init: 'FS', cl: 'M. Ramirez', color: COLORS.blue }, null, { init: 'JC', cl: 'K. Taylor', color: COLORS.blue }, null, { init: 'DB', cl: 'A. Vance', color: COLORS.orange }, null, null],
  [{ init: 'EV', cl: 'S. Jenkins', color: COLORS.teal }, { init: 'AC', cl: 'R. Chen', color: COLORS.purple }, null, { init: 'MS', cl: 'S. Jenkins', color: COLORS.teal }, null, null, null],
];

const TODAY = [
  { name: 'John Doe', detail: 'S. Jenkins, RN • RN Visit', time: '08:00 AM' },
  { name: 'Alice Cooper', detail: 'R. Chen, MSW • MSW Visit', time: '09:30 AM' },
  { name: 'Mary Poppins', detail: 'S. Jenkins, RN • RN Visit', time: '11:00 AM' },
  { name: 'D. Bowie', detail: 'A. Vance, Chaplain • Chaplain Visit', time: '11:30 AM' },
  { name: 'Frank Sinatra', detail: 'M. Ramirez, Aide • Aide Visit', time: '01:00 PM' },
  { name: 'Eleanor Vance', detail: 'S. Jenkins, RN • RN Visit', time: '02:30 PM' },
  { name: 'Johnny Cash', detail: 'K. Taylor, PT • PT Visit', time: '03:45 PM' },
  { name: 'Martha Stevens', detail: 'S. Jenkins, RN • RN Visit', time: '05:00 PM' },
];

const STAFF = [
  { name: 'Sarah Jenkins, RN', patients: '12 patients', capacity: '80%', width: '80%' },
  { name: 'Robert Chen, MSW', patients: '18 patients', capacity: '90%', width: '90%' },
  { name: 'A. Vance, Chaplain', patients: '25 patients', capacity: '50%', width: '50%' },
  { name: 'M. Ramirez, Aide', patients: '14 patients', capacity: '70%', width: '70%' },
  { name: 'K. Taylor, PT', patients: '10 patients', capacity: '60%', width: '60%' },
  { name: 'Dr. Allen Patel, MD', patients: '45 patients', capacity: '30%', width: '30%' },
];

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

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Scheduled Today', value: '18' },
          { label: 'Completed', value: '6' },
          { label: 'In Progress', value: '4' },
          { label: 'Unassigned Visits', value: '3' },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <p style={{ fontSize: 13, fontWeight: 500, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.textPrimary, margin: '6px 0 0' }}>{s.value}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 24, marginBottom: 24 }}>
        <div style={S.card}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ ...S.tableHeader, textAlign: 'left', fontSize: 12, color: COLORS.dim }}>Time</th>
                {DAYS.map((d) => (
                  <th key={d} style={{ ...S.tableHeader, textAlign: 'center', fontSize: 12, fontWeight: 600, color: COLORS.textPrimary }}>{d}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {TIMES.map((time, ri) => (
                <tr key={ri}>
                  <td style={{ ...S.tableCell, fontSize: 11, color: COLORS.dim }}>{time}</td>
                  {GRID[ri].map((cell, ci) => (
                    <td key={ci} style={{ ...S.tableCell, textAlign: 'center', padding: 6 }}>
                      {cell && (
                        <div style={{ background: `${cell.color}22`, border: `1px solid ${cell.color}44`, borderRadius: 6, padding: '6px 4px' }}>
                          <p style={{ fontSize: 12, fontWeight: 700, color: COLORS.textPrimary, margin: 0 }}>{cell.init}</p>
                          <p style={{ fontSize: 10, color: COLORS.muted, margin: '2px 0 0' }}>{cell.cl}</p>
                        </div>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: COLORS.textPrimary, margin: 0 }}>Today's Schedule</h3>
            <span style={{ fontSize: 12, color: '#14b8a6' }}>8 Visits</span>
          </div>
          {TODAY.map((v, i) => (
            <div key={i} style={{ padding: '10px 0', borderBottom: i < TODAY.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.textPrimary }}>{v.name}</span>
                <span style={{ fontSize: 11, color: COLORS.dim }}>{v.time}</span>
              </div>
              <p style={{ fontSize: 11, color: COLORS.muted, margin: '2px 0 0' }}>{v.detail}</p>
            </div>
          ))}
        </div>
      </div>

      <div style={S.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: COLORS.textPrimary, margin: '0 0 4px' }}>Staff Availability & Caseloads</h3>
            <p style={{ fontSize: 12, color: COLORS.muted, margin: 0 }}>Daily capacity utilization and current patient assignments</p>
          </div>
          <button style={{ fontSize: 12, color: COLORS.textPrimary, background: 'transparent', border: 'none', cursor: 'pointer' }}>Refresh Status</button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {STAFF.map((s, i) => (
            <div key={i} style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: COLORS.textPrimary }}>{s.name}</span>
              </div>
              <p style={{ fontSize: 11, color: COLORS.muted, margin: '0 0 8px' }}>{s.patients}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontSize: 10, color: COLORS.dim }}>Daily Capacity</span>
                <span style={{ fontSize: 10, fontWeight: 600, color: COLORS.textPrimary }}>{s.capacity}</span>
              </div>
              <div style={{ height: 6, background: COLORS.border, borderRadius: 3 }}>
                <div style={{ width: s.width, height: '100%', background: COLORS.teal, borderRadius: 3 }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
