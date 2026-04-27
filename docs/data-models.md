# Hospice EMR Data Models

## 1. Overview

This document defines the core data entities required to support the hospice EMR clinical and functional requirements.

These models describe logical data structures and are not tied to any specific database or programming language.

---

## 2. Design Principles

- Data must reflect real hospice workflows
- Clinical records are legal documents
- Finalized clinical records cannot be deleted
- All changes must be auditable
- Access to data is role-based

---

## 3. Core Entities

### 3.1 User
Represents a system user.

Key attributes:
- User ID
- Full name
- Role (RN, LVN, NP, CHHA, Volunteer, Physician, Surveyor, Admin)
- License or credential (if applicable)
- Status (active, inactive)

---

### 3.2 Patient
Represents a hospice patient.

Key attributes:
- Patient ID (system-generated, immutable)
- Medical Record Number (MRN)
- Full name
- Date of birth
- Primary diagnosis
- Hospice start date
- Current status (active, discharged, deceased)

---

### 3.3 Admission
Represents hospice admission details.

Key attributes:
- Admission ID
- Patient ID
- Admission date
- Certifying provider
- Level of care

---

### 3.4 Visit
Represents a patient encounter.

Key attributes:
- Visit ID
- Patient ID
- User ID
- Visit type (RN, LVN, NP, CHHA, Volunteer)
- Visit date and time
- Status (draft, finalized)

---

### 3.5 Clinical Note
Represents documentation for a visit.

Key attributes:
- Note ID
- Visit ID
- Author ID
- Note type
- Content
- Finalized timestamp

---

### 3.6 Medication
Represents patient medications.

Key attributes:
- Medication ID
- Patient ID
- Medication name
- Dosage
- Route
- Start date
- End date

---

### 3.7 Plan of Care
Represents the interdisciplinary care plan.

Key attributes:
- Plan ID
- Patient ID
- Effective date
- Goals
- Interventions
- Review date

---

## 4. Entity Relationships

- A Patient may have one or more Admissions
- A Patient may have many Visits
- A Visit has one or more Clinical Notes
- A User may author many Visits and Notes
- A Patient has one active Plan of Care at a time

---

## 5. Audit Fields

All clinical entities shall include:
- Created by
- Created date/time
- Modified by
- Modified date/time

---

## 6. Out of Scope

- Billing and claims data
- Payer information
- External system integrations