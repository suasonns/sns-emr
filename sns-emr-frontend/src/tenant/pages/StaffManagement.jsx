import React from 'react';
import { COLORS, S } from '../TenantDashboard';

const STAFF = [
  { name: 'Emily Watson', role: 'RN', license: 'RN-48291', expiry: '12/15/2025', patients: '7', status: 'Active', statusColor: '#10b796', phone: '(512) 555-0143', highlight: true },
  { name: 'David Miller', role: 'PT', license: 'PT-99381', expiry: '04/22/2025', patients: '5', status: 'Active', statusColor: '#10b796', phone: '(512) 555-0198' },
  { name: 'Marcus Chen', role: 'Physician', license: 'MD-22910', expiry: '08/11/2024', patients: '2', status: 'Active', statusColor: '#10b796', phone: '(512) 555-0221' },
  { name: 'Sarah Higgins', role: 'MSW', license: 'SW-88394', expiry: '11/02/2025', patients: '8', status: 'Active', statusColor: '#10b796', phone: '(512) 555-0210' },
  { name: 'Aris Thorne', role: 'Chaplain', license: 'CH-33291', expiry: '10/30/2024', patients: '6', status: 'Active', statusColor: '#10b796', phone: '(512) 555-0112' },
  { name: 'Elena Rostova', role: 'LPN', license: 'LP-33821', expiry: '01/15/2024', patients: '4', status: 'Pending', statusColor: COLORS.orange, phone: '(512) 555-0156' },
  { name: 'James Carter', role: 'Aide', license: 'AC-11920', expiry: '06/18/2025', patients: '5', status: 'Active', statusColor: '#10b796', phone: '(512) 555-0175' },
  { name: 'Rebecca Low', role: 'RN', license: 'RN-48110', expiry: '09/05/2025', patients: '0', status: 'On Leave', statusColor: COLORS.blue, phone: '(512) 555-0284' },
  { name: 'Thomas Sterling', role: 'Chaplain', license: 'CH-32210', expiry: '03/12/2025', patients: '6', status: 'Active', statusColor: '#10b796', phone: '(512) 555-0199' },
  { name: 'Linda Vance', role: 'LPN', license: 'LP-39912', expiry: '07/21/2025', patients: '5', status: 'Active', statusColor: '#10b796', phone: '(512) 555-0131' },
];

const CASELOAD = [
  { name: 'Robert J. Peterson', loc: 'Room 104A', priority: 'High', priColor: COLORS.red },
  { name: 'Alice M. Vance', loc: 'Home Care', priority: 'Medium', priColor: COLORS.orange },
  { name: 'John H. Albright', loc: 'Home Care', priority: 'Stable', priColor: '#10b796' },
];

export default function StaffManagement() {
  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: COLORS.white, margin: 0 }}>Staff Management</h1>
          <p style={{ fontSize: 14, fontWeight: 400, color: COLORS.muted, margin: '4px 0 0' }}>Manage clinical staff credentials, assignments, caseloads, and compliance tracking.</p>
        </div>
        <button style={S.btn(COLORS.teal)}>Add Staff Member</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Total Staff', value: '32', desc: 'All clinical & admin roles' },
          { label: 'Active Clinicians', value: '28', desc: 'On-duty caseload managers' },
          { label: 'Pending Credentials', value: '4', desc: 'Action required soon' },
          { label: 'Avg Caseload', value: '6.2', desc: 'Patients per clinician' },
        ].map((s, i) => (
          <div key={i} style={S.statCard}>
            <p style={{ fontSize: 13, fontWeight: 500, color: COLORS.muted, margin: 0 }}>{s.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: COLORS.offWhite, margin: '6px 0 4px' }}>{s.value}</p>
            <p style={{ fontSize: 12, color: COLORS.dim, margin: 0 }}>{s.desc}</p>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{ position: 'absolute', left: 12, top: 10, fontSize: 14, color: COLORS.dim }}>🔍</span>
          <input style={S.searchBar} placeholder="Search staff by name or license..." readOnly />
        </div>
        {['Role: All', 'Department: All', 'Status: Active'].map((f) => (
          <select key={f} style={S.select}><option>{f}</option></select>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24 }}>
        <div style={S.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: COLORS.offWhite, margin: 0 }}>Staff Roster</h3>
            <span style={{ fontSize: 13, color: COLORS.muted }}>Showing 10 of 32 results</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Name', 'Role', 'License', 'License Expiry', 'Patients', 'Status', 'Phone'].map((h) => (
                  <th key={h} style={{ ...S.tableHeader, textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.muted }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {STAFF.map((s, i) => (
                <tr key={i}>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.offWhite }}>{s.name}</td>
                  <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: COLORS.muted }}>{s.role}</span></td>
                  <td style={S.tableCell}>{s.license}</td>
                  <td style={{ ...S.tableCell, fontWeight: 500, color: COLORS.red }}>{s.expiry}</td>
                  <td style={{ ...S.tableCell, fontWeight: 600, color: COLORS.offWhite }}>{s.patients}</td>
                  <td style={S.tableCell}><span style={{ fontSize: 11, fontWeight: 600, color: s.statusColor }}>{s.status}</span></td>
                  <td style={S.tableCell}>{s.phone}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={S.card}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: COLORS.offWhite, margin: '0 0 4px' }}>Emily Watson, RN</h3>
          <p style={{ fontSize: 13, fontWeight: 600, color: COLORS.teal, margin: '0 0 16px' }}>Case Manager / RN Supervisor</p>

          {[
            { label: 'License Number', value: 'RN-48291' },
            { label: 'Hire Date', value: 'Jan 15, 2021' },
            { label: 'License Renewal', value: 'Dec 15, 2025' },
          ].map((f, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <p style={{ fontSize: 12, color: COLORS.muted, margin: '0 0 2px' }}>{f.label}</p>
              <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.offWhite, margin: 0 }}>{f.value}</p>
            </div>
          ))}

          <p style={{ fontSize: 12, fontWeight: 700, color: COLORS.muted, margin: '16px 0 8px' }}>Certifications</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
            {['BLS (AHA)', 'CHPN (Hospice)', 'Wound Care Cert', 'PALS'].map((c) => (
              <span key={c} style={{ fontSize: 11, fontWeight: 600, color: COLORS.offWhite, padding: '4px 10px', borderRadius: 6, background: COLORS.bg, border: `1px solid ${COLORS.border}` }}>{c}</span>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: COLORS.muted }}>Current Caseload (7)</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: COLORS.teal, cursor: 'pointer' }}>View Schedule</span>
          </div>
          {CASELOAD.map((c, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: i < CASELOAD.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
              <div>
                <p style={{ fontSize: 12, fontWeight: 600, color: COLORS.offWhite, margin: 0 }}>{c.name}</p>
                <p style={{ fontSize: 11, color: COLORS.dim, margin: '2px 0 0' }}>{c.loc}</p>
              </div>
              <span style={{ fontSize: 10, fontWeight: 600, color: c.priColor }}>{c.priority}</span>
            </div>
          ))}

          <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
            <button style={S.btn(COLORS.teal)}>Assign New Patient</button>
            <button style={S.btnOutline}>Update Credentials</button>
          </div>
        </div>
      </div>
    </div>
  );
}
