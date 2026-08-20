import React, { useState } from 'react';
import { COLORS, S } from '../design';
import VendorManagement from './VendorManagement';
import OrderPackManagement from './OrderPackManagement';

const settingsTabs = [
  { label: 'General' },
  { label: 'Notifications' },
  { label: 'Clinical' },
  { label: 'Billing' },
  { label: 'Vendors' },
  { label: 'Order Packs' },
  { label: 'Integrations' },
  { label: 'Users & Permissions' },
];

function GeneralTab() {
  const agencyInfo = [
    { label: 'Agency Name', value: 'Grace Hospice Care' },
    { label: 'NPI Number', value: '1234567890' },
    { label: 'Medicare Provider ID', value: '45-1234' },
    { label: 'State License', value: 'TX-HC-2024-0891' },
    { label: 'Address', value: '4521 Oak Lawn Ave, Suite 200, Dallas, TX 75219' },
    { label: 'Phone', value: '(214) 555-0182' },
    { label: 'Administrator', value: 'Sarah Jenkins, RN' },
  ];

  const accessRoles = [
    { label: 'Administrator', enabled: true },
    { label: 'DPCS', enabled: true },
    { label: 'RN / Clinical Staff', enabled: false },
    { label: 'Billing Staff', enabled: false },
    { label: 'Physician', enabled: false },
  ];

  const operatingHours = [
    { day: 'Monday – Friday', hours: '8:00 AM – 6:00 PM' },
    { day: 'Saturday', hours: '9:00 AM – 1:00 PM' },
    { day: 'Sunday', hours: 'Closed (On-Call Only)' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white }}>Agency Information</div>
          <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.white, fontSize: 12, cursor: 'pointer' }}>Edit</button>
        </div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Core agency details, license, and contact information.</div>
        {agencyInfo.map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < agencyInfo.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
            <span style={{ fontSize: 13, color: COLORS.muted }}>{item.label}</span>
            <span style={{ fontSize: 13, color: COLORS.white, fontWeight: 500 }}>{item.value}</span>
          </div>
        ))}
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Access Level Visibility</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Control which roles can see Agency Settings in the sidebar.</div>
        {accessRoles.map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < accessRoles.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
            <span style={{ fontSize: 13, color: COLORS.white }}>{item.label}</span>
            <div style={{ width: 40, height: 22, borderRadius: 11, position: 'relative', background: item.enabled ? COLORS.teal : COLORS.border }}>
              <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#fff', position: 'absolute', top: 3, left: item.enabled ? 21 : 3, transition: 'left 0.2s' }} />
            </div>
          </div>
        ))}
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white }}>Operating Hours</div>
          <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.white, fontSize: 12, cursor: 'pointer' }}>Edit</button>
        </div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Standard business hours and on-call schedule.</div>
        {operatingHours.map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < operatingHours.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
            <span style={{ fontSize: 13, color: COLORS.muted }}>{item.day}</span>
            <span style={{ fontSize: 13, color: COLORS.white, fontWeight: 500 }}>{item.hours}</span>
          </div>
        ))}
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Service Areas</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 16 }}>Counties and zip codes covered by this agency.</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {['Dallas County', 'Tarrant County', 'Collin County', 'Denton County', 'Rockwall County'].map((area, i) => (
            <span key={i} style={{ padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 500, background: `${COLORS.teal}1a`, color: COLORS.teal, border: `1px solid ${COLORS.teal}33` }}>{area}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function NotificationsTab() {
  const emailNotifs = [
    { label: 'New patient admission alerts', enabled: true },
    { label: 'POC expiration reminders (72hr, 48hr, 24hr)', enabled: true },
    { label: 'Unsigned order reminders', enabled: true },
    { label: 'Claims denial notifications', enabled: true },
    { label: 'Staff credential expiration warnings', enabled: true },
    { label: 'QAPI measure threshold alerts', enabled: false },
    { label: 'Weekly census summary digest', enabled: true },
  ];

  const smsNotifs = [
    { label: 'Critical patient status changes', enabled: true },
    { label: 'On-call visit assignments', enabled: true },
    { label: 'System downtime alerts', enabled: true },
    { label: 'Missed visit alerts (same-day)', enabled: false },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Email Notifications</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Agency-wide email alert settings. Individual users can override in personal Settings.</div>
        {emailNotifs.map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < emailNotifs.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
            <span style={{ fontSize: 13, color: COLORS.white }}>{item.label}</span>
            <div style={{ width: 40, height: 22, borderRadius: 11, position: 'relative', background: item.enabled ? COLORS.teal : COLORS.border }}>
              <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#fff', position: 'absolute', top: 3, left: item.enabled ? 21 : 3 }} />
            </div>
          </div>
        ))}
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>SMS / Text Notifications</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Critical alerts sent via SMS to on-call and administrative staff.</div>
        {smsNotifs.map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < smsNotifs.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
            <span style={{ fontSize: 13, color: COLORS.white }}>{item.label}</span>
            <div style={{ width: 40, height: 22, borderRadius: 11, position: 'relative', background: item.enabled ? COLORS.teal : COLORS.border }}>
              <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#fff', position: 'absolute', top: 3, left: item.enabled ? 21 : 3 }} />
            </div>
          </div>
        ))}
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Quiet Hours</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Suppress non-critical notifications during off-hours. Critical alerts always go through.</div>
        <div style={{ display: 'flex', gap: 16 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: COLORS.muted, marginBottom: 6, display: 'block' }}>Start Time</label>
            <input defaultValue="10:00 PM" style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.white, fontSize: 13, outline: 'none' }} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: COLORS.muted, marginBottom: 6, display: 'block' }}>End Time</label>
            <input defaultValue="7:00 AM" style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.white, fontSize: 13, outline: 'none' }} />
          </div>
        </div>
      </div>
    </div>
  );
}

function ClinicalTab() {
  const docTemplates = [
    { name: 'Nursing Visit Note', type: 'Visit Note', status: 'Active', lastModified: 'Aug 10, 2026' },
    { name: 'Aide Visit Documentation', type: 'Visit Note', status: 'Active', lastModified: 'Aug 05, 2026' },
    { name: 'MSW Assessment', type: 'Assessment', status: 'Active', lastModified: 'Jul 28, 2026' },
    { name: 'Chaplain Spiritual Care', type: 'Visit Note', status: 'Active', lastModified: 'Jul 22, 2026' },
    { name: 'Bereavement Follow-Up', type: 'Follow-Up', status: 'Draft', lastModified: 'Jul 15, 2026' },
  ];

  const assessmentSchedules = [
    { name: 'Comprehensive Assessment', frequency: 'Admission + every 15 days', required: true },
    { name: 'Pain Assessment (PPS)', frequency: 'Every visit', required: true },
    { name: 'Fall Risk Assessment', frequency: 'Admission + quarterly', required: true },
    { name: 'Wound Assessment', frequency: 'Every skilled nursing visit', required: false },
    { name: 'Nutritional Screening', frequency: 'Admission + monthly', required: false },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 12, overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white }}>Documentation Templates</div>
            <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 2 }}>Manage clinical documentation templates used across the agency.</div>
          </div>
          <button style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: COLORS.teal, color: COLORS.white, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>+ Add Template</button>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
              {['Template Name', 'Type', 'Status', 'Last Modified', ''].map((h) => (
                <th key={h} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.muted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {docTemplates.map((t, i) => (
              <tr key={i} style={{ borderBottom: i < docTemplates.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                <td style={{ padding: '12px 20px', fontSize: 13, fontWeight: 500, color: COLORS.white }}>{t.name}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.muted }}>{t.type}</td>
                <td style={{ padding: '12px 20px' }}>
                  <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: t.status === 'Active' ? `${COLORS.green}22` : `${COLORS.orange}22`, color: t.status === 'Active' ? COLORS.green : COLORS.orange }}>{t.status}</span>
                </td>
                <td style={{ padding: '12px 20px', fontSize: 12, color: COLORS.muted }}>{t.lastModified}</td>
                <td style={{ padding: '12px 20px' }}><span style={{ fontSize: 12, color: COLORS.teal, cursor: 'pointer' }}>Edit</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Assessment Schedules</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Configure assessment frequency and requirements per CMS guidelines.</div>
        {assessmentSchedules.map((item, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < assessmentSchedules.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: COLORS.white }}>{item.name}</div>
              <div style={{ fontSize: 11, color: COLORS.muted, marginTop: 2 }}>{item.frequency}</div>
            </div>
            <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: item.required ? `${COLORS.red}22` : `${COLORS.teal}22`, color: item.required ? COLORS.red : COLORS.teal }}>{item.required ? 'Required' : 'Optional'}</span>
          </div>
        ))}
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Clinical Protocols</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 16 }}>Standing orders, symptom management, and emergency protocols.</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
          {['Comfort Kit Standing Orders', 'Symptom Management Protocol', 'Emergency Comfort Measures', 'Continuous Care Criteria', 'GIP Admission Criteria', 'Respite Care Guidelines'].map((p, i) => (
            <div key={i} style={{ padding: '12px 16px', borderRadius: 8, border: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13, color: COLORS.white }}>{p}</span>
              <span style={{ fontSize: 11, color: COLORS.teal }}>View →</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function BillingTab() {
  const inputStyle = {
    width: '100%', padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`,
    background: COLORS.bg, color: COLORS.white, fontSize: 13, outline: 'none',
  };

  const labelStyle = { fontSize: 12, fontWeight: 600, color: COLORS.muted, marginBottom: 6, display: 'block' };

  const rateSchedule = [
    { level: 'Routine Home Care', rate: '$203.79', code: '0651' },
    { level: 'Continuous Home Care', rate: '$1,432.41', code: '0652' },
    { level: 'General Inpatient Care', rate: '$803.25', code: '0656' },
    { level: 'Inpatient Respite Care', rate: '$183.10', code: '0655' },
    { level: 'Service Intensity Add-On (SIA)', rate: '$41.39', code: '0657' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Billing Configuration</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Agency billing defaults and submission settings.</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
          <div><label style={labelStyle}>Default Payer</label><select style={inputStyle}><option>Medicare</option><option>Medicaid</option><option>Private Insurance</option></select></div>
          <div><label style={labelStyle}>Billing Cycle</label><select style={inputStyle}><option>Monthly</option><option>Bi-Weekly</option><option>Weekly</option></select></div>
          <div><label style={labelStyle}>Claims Submission</label><select style={inputStyle}><option>Electronic (EDI 837)</option><option>Paper (CMS-1500)</option></select></div>
          <div><label style={labelStyle}>Auto-Submit NOE</label><select style={inputStyle}><option>Within 5 calendar days</option><option>Within 3 calendar days</option><option>Manual</option></select></div>
        </div>
      </div>

      <div style={{ background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 12, overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white }}>Medicare Rate Schedule (FY 2026)</div>
            <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 2 }}>Current per-diem rates for hospice levels of care.</div>
          </div>
          <button style={{ padding: '8px 16px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.white, fontSize: 12, cursor: 'pointer' }}>Update Rates</button>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
              {['Level of Care', 'Revenue Code', 'Per Diem Rate'].map((h) => (
                <th key={h} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.muted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rateSchedule.map((r, i) => (
              <tr key={i} style={{ borderBottom: i < rateSchedule.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                <td style={{ padding: '12px 20px', fontSize: 13, fontWeight: 500, color: COLORS.white }}>{r.level}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, color: COLORS.muted }}>{r.code}</td>
                <td style={{ padding: '12px 20px', fontSize: 13, fontWeight: 600, color: COLORS.teal }}>{r.rate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Auto-Billing Rules</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Automated billing triggers and validation rules.</div>
        {[
          { label: 'Auto-generate claims when visit notes are signed', enabled: true },
          { label: 'Block claim submission if POC unsigned', enabled: true },
          { label: 'Auto-submit NOE within 5 days of admission', enabled: true },
          { label: 'Flag duplicate billing entries', enabled: true },
          { label: 'Auto-calculate SIA eligibility', enabled: false },
        ].map((rule, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: i < 4 ? `1px solid ${COLORS.border}` : 'none' }}>
            <span style={{ fontSize: 13, color: COLORS.white }}>{rule.label}</span>
            <div style={{ width: 40, height: 22, borderRadius: 11, position: 'relative', background: rule.enabled ? COLORS.teal : COLORS.border }}>
              <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#fff', position: 'absolute', top: 3, left: rule.enabled ? 21 : 3 }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function IntegrationsTab() {
  const integrations = [
    { name: 'Palmetto GBA (Medicare MAC)', type: 'Claims / NOE', status: 'Connected', lastSync: '2 min ago' },
    { name: 'SHP for Hospice', type: 'Quality / Benchmarking', status: 'Connected', lastSync: '1 hr ago' },
    { name: 'DocuSign', type: 'E-Signatures', status: 'Connected', lastSync: '15 min ago' },
    { name: 'QuickBooks Online', type: 'Accounting', status: 'Connected', lastSync: '4 hr ago' },
    { name: 'Surescripts', type: 'E-Prescribing', status: 'Disconnected', lastSync: 'N/A' },
    { name: 'HL7 FHIR Gateway', type: 'Interoperability', status: 'Connected', lastSync: '30 min ago' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
        {integrations.map((item, i) => (
          <div key={i} style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white }}>{item.name}</div>
              <span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: item.status === 'Connected' ? `${COLORS.green}22` : `${COLORS.red}22`, color: item.status === 'Connected' ? COLORS.green : COLORS.red }}>{item.status}</span>
            </div>
            <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>{item.type}</div>
            <div style={{ fontSize: 11, color: COLORS.muted, marginBottom: 12 }}>Last sync: {item.lastSync}</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.white, fontSize: 12, cursor: 'pointer' }}>Configure</button>
              <button style={{ padding: '6px 14px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.white, fontSize: 12, cursor: 'pointer' }}>{item.status === 'Connected' ? 'Sync Now' : 'Reconnect'}</button>
            </div>
          </div>
        ))}
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>API Access</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Manage API keys for third-party integrations.</div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
          <div style={{ flex: 1, padding: '10px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.muted, fontSize: 13, fontFamily: 'monospace' }}>sk-live-••••••••••••••••••••3f8a</div>
          <button style={{ padding: '8px 16px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.white, fontSize: 12, cursor: 'pointer' }}>Reveal</button>
          <button style={{ padding: '8px 16px', borderRadius: 6, border: `1px solid ${COLORS.border}`, background: 'transparent', color: COLORS.white, fontSize: 12, cursor: 'pointer' }}>Regenerate</button>
        </div>
        <div style={{ fontSize: 11, color: COLORS.muted }}>Created: Jul 01, 2026 · Last used: Aug 15, 2026 · Scopes: read, write, admin</div>
      </div>
    </div>
  );
}

function UsersTab() {
  const users = [
    { name: 'Sarah Jenkins', email: 'sarah.jenkins@gracehospice.com', role: 'Administrator', status: 'Active', lastLogin: 'Today, 8:15 AM' },
    { name: 'Emily Watson', email: 'emily.watson@gracehospice.com', role: 'RN', status: 'Active', lastLogin: 'Today, 9:02 AM' },
    { name: 'Dr. Albert Chen', email: 'albert.chen@gracehospice.com', role: 'Physician', status: 'Active', lastLogin: 'Yesterday' },
    { name: 'Maria Ramirez', email: 'maria.ramirez@gracehospice.com', role: 'HHA', status: 'Active', lastLogin: 'Today, 7:45 AM' },
    { name: 'Robert Chen', email: 'robert.chen@gracehospice.com', role: 'MSW', status: 'Active', lastLogin: '2 days ago' },
    { name: 'Dr. Allen Patel', email: 'allen.patel@gracehospice.com', role: 'Physician', status: 'Active', lastLogin: 'Today, 10:30 AM' },
    { name: 'Patricia Holmes', email: 'patricia.holmes@gracehospice.com', role: 'Billing Admin', status: 'Active', lastLogin: 'Yesterday' },
    { name: 'David Kowalski', email: 'david.kowalski@gracehospice.com', role: 'DPCS', status: 'Active', lastLogin: '3 days ago' },
    { name: 'Laura Chen', email: 'laura.chen@gracehospice.com', role: 'RN', status: 'Invited', lastLogin: 'Never' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[
          { label: 'Total Users', value: '9' },
          { label: 'Active', value: '8' },
          { label: 'Pending Invite', value: '1' },
          { label: 'Roles Configured', value: '6' },
        ].map((stat, i) => (
          <div key={i} style={{ background: COLORS.card, borderRadius: 10, border: `1px solid ${COLORS.border}`, padding: '14px 20px' }}>
            <div style={{ fontSize: 12, color: COLORS.muted }}>{stat.label}</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: COLORS.white, marginTop: 4 }}>{stat.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <input placeholder="Search users..." style={{ padding: '8px 14px', borderRadius: 8, border: `1px solid ${COLORS.border}`, background: COLORS.bg, color: COLORS.white, fontSize: 13, outline: 'none', width: 260 }} />
          <button style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: COLORS.teal, color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>+ Invite User</button>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
              {['Name', 'Email', 'Role', 'Status', 'Last Login', ''].map((h) => (
                <th key={h} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: COLORS.muted }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map((u, i) => (
              <tr key={i} style={{ borderBottom: i < users.length - 1 ? `1px solid ${COLORS.border}` : 'none' }}>
                <td style={{ padding: '12px 20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 30, height: 30, borderRadius: '50%', background: COLORS.teal, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 11 }}>{u.name.split(' ').map((n) => n[0]).join('')}</div>
                    <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.white }}>{u.name}</span>
                  </div>
                </td>
                <td style={{ padding: '12px 20px', fontSize: 12, color: COLORS.muted }}>{u.email}</td>
                <td style={{ padding: '12px 20px' }}><span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: `${COLORS.teal}22`, color: COLORS.teal }}>{u.role}</span></td>
                <td style={{ padding: '12px 20px' }}><span style={{ padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 600, background: u.status === 'Active' ? `${COLORS.green}22` : `${COLORS.orange}22`, color: u.status === 'Active' ? COLORS.green : COLORS.orange }}>{u.status}</span></td>
                <td style={{ padding: '12px 20px', fontSize: 12, color: COLORS.muted }}>{u.lastLogin}</td>
                <td style={{ padding: '12px 20px' }}><span style={{ fontSize: 12, color: COLORS.teal, cursor: 'pointer' }}>Manage</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ ...S.card, marginBottom: 0, padding: 24 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>Role Permissions</div>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 20 }}>Configure what each role can view and modify across the platform.</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {[
            { role: 'Administrator', perms: 'Full access to all modules, settings, and user management' },
            { role: 'DPCS', perms: 'Clinical oversight, agency settings, staff management, QAPI' },
            { role: 'Physician', perms: 'Sign orders, review POC, certify/recertify, view census' },
            { role: 'RN / LVN', perms: 'Visit notes, assessments, POC, orders, patient records' },
            { role: 'Billing Admin', perms: 'Claims, billing reports, payer management, financial analytics' },
            { role: 'HHA / Aide', perms: 'Aide visit documentation, schedule view, assigned patients' },
          ].map((r, i) => (
            <div key={i} style={{ padding: '14px 16px', borderRadius: 8, border: `1px solid ${COLORS.border}` }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: COLORS.white, marginBottom: 4 }}>{r.role}</div>
              <div style={{ fontSize: 12, color: COLORS.muted, lineHeight: 1.5 }}>{r.perms}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function AgencySettings() {
  const [activeTab, setActiveTab] = useState('General');

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: COLORS.white, margin: 0 }}>Agency Settings</h1>
        <p style={{ fontSize: 13, color: COLORS.muted, margin: '6px 0 0' }}>
          Configure Grace Hospice Care preferences, integrations, notifications, and compliance parameters.
          <span style={{ color: '#f59e0b', marginLeft: 8, fontSize: 11, fontWeight: 600 }}>Administrator / DPCS Access Only</span>
        </p>
      </div>

      <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid ${COLORS.border}`, marginBottom: 24 }}>
        {settingsTabs.map((tab) => (
          <button key={tab.label} onClick={() => setActiveTab(tab.label)} style={{
            padding: '12px 20px', background: 'transparent', border: 'none', cursor: 'pointer',
            fontSize: 13, fontWeight: 600,
            color: activeTab === tab.label ? COLORS.teal : COLORS.muted,
            borderBottom: activeTab === tab.label ? `2px solid ${COLORS.teal}` : '2px solid transparent',
          }}>{tab.label}</button>
        ))}
      </div>

      {activeTab === 'General' && <GeneralTab />}
      {activeTab === 'Notifications' && <NotificationsTab />}
      {activeTab === 'Clinical' && <ClinicalTab />}
      {activeTab === 'Billing' && <BillingTab />}
      {activeTab === 'Vendors' && <VendorManagement />}
      {activeTab === 'Order Packs' && <OrderPackManagement />}
      {activeTab === 'Integrations' && <IntegrationsTab />}
      {activeTab === 'Users & Permissions' && <UsersTab />}
    </div>
  );
}
