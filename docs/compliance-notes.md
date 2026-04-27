# Hospice EMR Compliance Notes

## 1. Overview

This document outlines compliance considerations for the hospice EMR system, including privacy, security, and regulatory requirements.

The EMR is designed to support HIPAA compliance and Medicare hospice Conditions of Participation.

---

## 2. HIPAA Compliance

The EMR shall:
- Protect the confidentiality of patient health information
- Restrict access to authorized users only
- Ensure availability and integrity of clinical records

Patient data shall not be accessed without a legitimate hospice-related purpose.

---

## 3. Role-Based Access Control

- Users are assigned roles based on job function
- Access is limited to the minimum necessary information
- Users may only access patients assigned to them where applicable

Surveyors are provided read-only access.

---

## 4. Audit Logging

The EMR shall maintain audit logs that record:
- User access to patient records
- Creation of clinical documentation
- Modification of draft records
- Finalization of clinical records

Audit logs shall include:
- User identity
- Date and time
- Action performed

Audit logs are not editable by standard users.

---

## 5. Clinical Record Integrity

- Finalized clinical documentation shall not be deleted
- Corrections are made through amendments
- Original documentation remains preserved
- All amendments are time-stamped and attributed

Clinical documentation constitutes a legal medical record.

---

## 6. Data Retention

- Clinical records are retained according to hospice regulatory requirements
- Audit logs are retained for the life of the record
- Data deletion is restricted and controlled

---

## 7. Surveyor and External Review Access

- Surveyors are granted read-only access
- No ability to create, edit, or delete records
- Access is time-limited and logged

---

## 8. Assumptions and Limitations

- The system is not initially certified for production use
- Compliance requirements may change
- Additional safeguards may be added over time
``