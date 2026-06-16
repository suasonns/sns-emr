
# SNS EMR — QAPI Dashboard Alignment (Quality Guardrails Integration)

**Purpose:** Explicitly map the Quality Guardrails plan into QAPI dashboards so tenants can opt-in without affecting bedside workflows.

---

## 1) Dashboard: "Visit Quality Signals" (Leadership only)

### Widgets
1. **Short Visit Trend (Non-punitive)**
   - Count and % of visits below tenant threshold (e.g., 30m / 45m)
   - Drilldown by discipline, provider, patient

2. **Assessment Completeness Signal**
   - % of visits with required symptom review fields completed
   - Focus areas: pain, bowel, dyspnea, agitation, skin integrity

3. **Vitals-only Pattern Flag (Heuristic)**
   - Visits where documentation contains only minimal fields and no narrative/intervention
   - Presented as a *review queue*, not an accusation

4. **Time vs AI Capture Delta (Metadata)**
   - Shows difference between time_in/out duration and AI capture duration
   - Used to improve training, not to punish staff

---

## 2) Dashboard: "Continuous Care Readiness" (Leadership + Clinical Leads)

### Widgets
1. **CHC Day Summary**
   - Days flagged as Continuous Care
   - Total documented hours per day

2. **RN Daily Assessment Coverage**
   - For multi-day Continuous Care: shows whether an RN assessment note exists each day

3. **Discipline Mix (Clinical)**
   - RN/LVN/CHHA/MSW/SC presence per day

4. **Crisis Reason Distribution**
   - Pain crisis, dyspnea crisis, agitation crisis, other

---

## 3) Survey Readiness View (Evidence Pack)

When `quality.philosophy.enabled = ON`, include:
- The locked philosophy statement
- A short explanation of how the organization balances patient-centered care with documentation credibility

---

## 4) Tenant Toggle Integration

- `quality.philosophy.enabled = OFF`
  - Dashboards show signals without philosophy context.

- `quality.philosophy.enabled = ON`
  - Dashboards add a "Quality Philosophy" panel displaying the locked statement.

---

## 5) Governance Rules

- Dashboards are advisory and non-punitive.
- No clinical workflow blocking.
- All views are tenant-scoped.

