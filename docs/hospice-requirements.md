# Hospice EMR Requirements

## 1. Overview

This document describes the functional and clinical requirements for a hospice-focused Electronic Medical Record (EMR) system.

The goal of the system is to support hospice clinical documentation, patient management, and interdisciplinary care while maintaining compliance with hospice regulations and HIPAA requirements.

This document intentionally avoids technical implementation details.

---

## 2. Scope

The EMR shall support:
- Hospice patient intake and admission
- Ongoing clinical documentation
- Hospice interdisciplinary workflows
- Secure storage of patient medical records

The EMR is intended for use by authorized hospice personnel and approved external reviewers.

---

## 3. User Roles

The system shall support the following user roles with role-based access control.

### 3.1 Registered Nurse (RN)
- Document admissions
- Create and edit visit notes
- Perform skilled nursing visits
- View and update patient medications
- Participate in and update the plan of care

### 3.2 Licensed Vocational Nurse (LVN)
- Document assigned nursing visits
- View patient medications and care plans
- Record vital signs and clinical observations
- Cannot perform admissions independently

### 3.3 Nurse Practitioner (NP)
- Perform face-to-face encounters
- Document NP visits
- Participate in eligibility evaluations
- Review and contribute to plan of care

### 3.4 Physician / Medical Director
- Review clinical documentation
- Document face-to-face encounters
- Certify hospice eligibility
- Approve and sign medical orders

### 3.5 Certified Home Health Aide (CHHA)
- Document aide visits
- Record activities of daily living (ADLs)
- View assigned patient care plans
- No access to medication orders or clinical assessments

### 3.6 Social Worker
- Document psychosocial assessments
- Record care coordination and counseling notes
- Participate in interdisciplinary care planning

### 3.7 Chaplain
- Document spiritual care visits
- Record faith and spiritual support notes

### 3.8 Volunteer
- Document volunteer visit activity
- Record non-clinical support provided
- No access to clinical or medical records

### 3.9 Administrator
- Manage users and permissions
- Configure system settings
- View system-wide audit logs
- No clinical documentation unless separately credentialed

### 3.10 Surveyor (Read-Only)
- View patient records for compliance review
- Read-only access
- No data creation, editing, or deletion

---

## 4. Patient Lifecycle

The EMR shall support the full hospice patient lifecycle, including:

1. Referral and intake
2. Hospice admission
3. Ongoing interdisciplinary visits
4. Updates to plan of care
5. Interdisciplinary Group (IDG) review
6. Discharge, transfer, or death
7. Bereavement tracking (future version)

Each stage shall be time-stamped and associated with a responsible user.

---

## 5. Clinical Documentation Requirements

The system shall allow authorized clinicians to:

- Create visit notes
- Edit notes prior to finalization
- Finalize notes with date, time, and author
- View historical notes in chronological order

Once finalized:
- Notes shall not be deleted
- Amendments shall be tracked, time-stamped, and clearly labeled

---

## 6. Medication Management

The EMR shall support:
- Maintaining an active medication list
- Recording medication changes
- Viewing medication history

The system does not initially manage medication dispensing or pharmacy integrations.

---

## 7. Security & Access Control

The EMR shall:
- Require secure user authentication
- Enforce role-based access control
- Prevent unauthorized access to patient records
- Automatically log access to patient data

Users shall only access records necessary for their role and assignment.

---

## 8. Audit and Legal Record Rules

The EMR shall:
- Record who created, modified, or accessed clinical records
- Store timestamps for all actions
- Preserve historical versions of clinical documentation
- Prevent silent data modification or deletion

Clinical records constitute legal medical records.

---

## 9. Out of Scope (Initial Version)

The following are explicitly out of scope for the initial version:
- Billing and claims submission
- Medicare reporting and electronic submission
- Pharmacy and laboratory integrations
- Mobile applications
- AI or clinical decision support tools

---

## 10. Assumptions

- The system is not certified for production clinical use initially
- The system is developed incrementally
- Compliance and regulatory requirements may evolve