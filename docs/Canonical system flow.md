**PHASE 1 — CLINICAL ELIGIBILITY (NO BILLING YET)**



Referral received

&#x20;  ↓

Eligibility run

&#x20;  ↓

CTI signed

&#x20;  ↓

RN initial assessment (SOC)

&#x20;  ↓

Hospice diagnosis confirmed

&#x20;  ↓

NOE sent



**PHASE 2 — ADMINISTRATIVE ENABLEMENT**



Admin / DPCS sets benefit period

&#x20;  ↓

System validates:

&#x20;  - CTI date

&#x20;  - SOC date

&#x20;  - NOE status



**PHASE 3 — OPERATIONAL SCHEDULING**





Admin / Office Manager schedules visits

&#x20;  ↓

Visit calendar created

&#x20;  ↓

Visits occur and are finalized



**PHASE 4 — BILLING EXTRACTION (MONTHLY)**



Billing month selected

&#x20;  ↓

System pulls:

&#x20;  - visits (finalized, within benefit period)

&#x20;  - POC active during month

&#x20;  - IDG(s) covering month

&#x20;  - Orders active during month



**PHASE 5 — ELECTRONIC CLAIM FILE (ECF)**



Visits → claim lines

Benefit period → claim header



**PHASE 6 — REMITTANCE ADVICE (RA)**



Payer adjudicates claim

&#x20;  ↓

RA received

&#x20;  ↓

RA mapped back to:

&#x20;  - claim

&#x20;  - claim lines

&#x20;  - visits





**Minimal data mapping (no over‑build)**

patient

&#x20;└─ benefit\_period

&#x20;    ├─ visits (FINALIZED)

&#x20;    │    └─ claim\_lines

&#x20;    ├─ plan\_of\_care (effective dates)

&#x20;    ├─ idg\_meetings (monthly)

&#x20;    ├─ orders

&#x20;    └─ claims

&#x20;         └─ remittances





