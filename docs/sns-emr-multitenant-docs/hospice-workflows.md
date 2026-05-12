# Hospice Workflow Overview
**Multi‑Tenant Enterprise | Authorization‑Aware Workflows**

---

## 1. Workflow Conventions (Enterprise)

- Every workflow action is tenant‑scoped.
- Each step lists the **Authorized Role(s)** and **Interface**.
- Finalization records immutable signer metadata: user + role + interface + timestamp.

---

## 2. Patient Admission

1) Referral received and intake created  
   **Authorized**: RN/Admissions Staff (if configured)  
   **Interface**: Clinical EMR

2) RN completes admission assessment  
   **Authorized**: RN  
   **Interface**: Clinical EMR

3) Provider certifies hospice eligibility (if implemented)  
   **Authorized**: MD/NP  
   **Interface**: Clinical EMR

4) Admission date established; MRN assigned (unique within tenant)  
   **Authorized**: RN / Tenant Admin (policy)  
   **Interface**: Clinical EMR / Admin Console

**Documentation**
- Admission note (draft → finalized)
- Eligibility certification evidence (where applicable)

---

## 3. Nursing Visits

1) RN/LVN performs visit and documents findings  
   **Authorized**: RN, LVN  
   **Interface**: Clinical EMR

2) Draft note editing (pre‑finalization)  
   **Authorized**: Note author or permitted clinician  
   **Interface**: Clinical EMR

3) Finalize visit note (signature event)  
   **Authorized**: RN/LVN (per tenant policy)  
   **Interface**: Clinical EMR

**Documentation**
- Visit note with date/time and immutable signer metadata

---

## 4. Pain and Symptom Management

1) Symptoms assessed each visit  
   **Authorized**: RN/LVN/NP/MD  
   **Interface**: Clinical EMR

2) Medication changes recorded  
   **Authorized**: RN (documentation), NP/MD (orders if implemented)  
   **Interface**: Clinical EMR

3) Communication documented (team + provider)  
   **Authorized**: RN/NP/MD/SW  
   **Interface**: Clinical EMR

---

## 5. Plan of Care (POC)

1) Interdisciplinary plan established  
   **Authorized**: RN (lead), SW, Chaplain, MD/NP (as applicable)  
   **Interface**: Clinical EMR

2) POC review at IDG intervals  
   **Authorized**: IDG participants (discipline roles)  
   **Interface**: Clinical EMR

3) POC update finalization (if versioned)  
   **Authorized**: RN (and provider if required by policy)  
   **Interface**: Clinical EMR

**Documentation**
- POC effective dates and review evidence
- Role‑appropriate participation attribution

---

## 6. IDG Review

1) IDG meeting recorded  
   **Authorized**: RN/QA/Compliance (policy)  
   **Interface**: Clinical EMR

2) Participant contributions linked to roles  
   **Authorized**: RN, SW, Chaplain, MD/NP  
   **Interface**: Clinical EMR

---

## 7. Death or Discharge

1) Death pronounced or discharge documented  
   **Authorized**: RN/MD (policy)  
   **Interface**: Clinical EMR

2) Discharge summary/death note finalized  
   **Authorized**: Responsible clinician  
   **Interface**: Clinical EMR

**Documentation**
- Time‑stamped, signed records
- Immutable audit trail
