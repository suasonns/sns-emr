==================================================

ANALYTICS PAGE COMPLETE RE-DESIGN

==================================================

CURRENT ANALYTICS PAGE IS NOT MEETING THE OWNER PLATFORM MISSION.

The current page tracks:

- Daily Active Users

- Weekly Active Users

- Monthly Active Users

- Login Counts

This information provides little value to SNS operations and does not help determine agency struggles, platform weaknesses, or future development priorities.

==================================================

NEW PAGE NAME

==================================================

Agency Health Intelligence

OR

Operational Intelligence

Analytics should become:

A platform-learning and agency-health center.

==================================================

MISSION

==================================================

The purpose of Analytics is NOT:

- User engagement

- Login statistics

- Patient analysis

- Clinical reporting

The purpose IS:

Determine:

1. Are agencies healthy?

2. Are agencies struggling?

3. Are agencies falling behind?

4. What operational issues occur most often?

5. What workflow creates the most friction?

6. What assistance is requested most?

7. What should SNS improve next?

Analytics exists to identify:

Agency Problems

Platform Weaknesses

Future Development Priorities

==================================================

SECTION 1

AGENCY HEALTH OVERVIEW

==================================================

Display:

Healthy Agencies

Needs Attention

Critical Agencies

Training Agencies

Demo Agencies

Purpose:

Quick health assessment across all agencies.

==================================================

SECTION 2

TOP ALERT CATEGORIES

==================================================

Display:

Late Notes

Missing Assessments

Unsigned Orders

Overdue Tasks

Documentation Warnings

Finalization Warnings

Show:

Count

Trend

30 Day Comparison

Purpose:

Identify operational pain points.

==================================================

SECTION 3

WORKFLOW FRICTION

==================================================

Track:

Most Reopened Workflows

Most Corrected Workflows

Most Abandoned Workflows

Most Delayed Workflows

Examples:

RNICA

Admissions

IDG

Narrative Review

Medication Review

Purpose:

Identify workflow weaknesses.

==================================================

SECTION 4

MOST COMMON CORRECTIONS

==================================================

Display:

Fields most frequently corrected

Sections most frequently corrected

AI outputs most frequently corrected

Purpose:

Help identify weak areas for future development.

==================================================

SECTION 5

MOST COMMON HELP REQUESTS

==================================================

Display:

Guidance Requests

Navigation Requests

Documentation Assistance Requests

Most Viewed Help Topics

Purpose:

Identify areas where users struggle.

==================================================

SECTION 6

ALERT TREND INTELLIGENCE

==================================================

Show:

Late Notes

Missing Documentation

Assessment Delays

Workflow Delays

AI Review Warnings

Trend Direction:

Up

Down

Stable

Purpose:

Track whether problems are improving or worsening.

==================================================

SECTION 7

AGENCY COMPARISON

==================================================

Compare:

Love & Faith

Angela

Silva

Future Agencies

Show:

Alert Volume

Workflow Friction

Guidance Requests

Documentation Delays

Purpose:

Identify agencies requiring support.

==================================================

SECTION 8

SNS IMPROVEMENT SIGNALS

==================================================

This is the most important section.

Display:

Top Platform Problems

Top Documentation Problems

Top Workflow Bottlenecks

Top User Struggles

Purpose:

Generate future SNS development priorities directly from agency behavior.

==================================================

SECTION 9

DEVELOPMENT PRIORITY ENGINE

==================================================

Automatically rank:

Highest Friction Area

Highest Alert Category

Highest Correction Category

Highest Guidance Category

Purpose:

Transform operational data into future roadmap items.

==================================================

IMPORTANT RULE

==================================================

Analytics MUST NOT contain:

- Patient details

- Clinical documentation

- Clinical notes

- Diagnoses

- Patient-level information

Analytics should use:

Counts

Trends

Categories

Patterns

Health Indicators

The Platform Owner should be able to determine:

Where agencies struggle

Why agencies struggle

What SNS should improve next

Without opening a single patient chart.

---

## Status

Future Design Specification. **DO NOT IMPLEMENT UNTIL APPROVED.** This
document defines a complete re-design of the existing Owner Platform
Analytics page. No code, UI, or data model changes are authorized by
this document alone.

## Relationship to Other Documents

- Directly operationalizes
  `docs/roadmap/Analytics-And-Agency-Health-Roadmap.md`: that roadmap
  document states analytics exist to identify operational friction and
  future product opportunities, not for patient/clinical review; this
  specification is the concrete page design that fulfills that
  mission.
- Belongs to the Owner Platform per
  `docs/roadmap/Owner-Platform-Roadmap.md`'s scope (Agency Health
  Monitoring, Operational Intelligence, Trend Analysis, Alert
  Analytics, Growth Monitoring, Intervention Detection) — this page is
  where that vision becomes a concrete UI.
- Section 7 (Agency Comparison) explicitly includes Love & Faith,
  Angela, and Silva per
  `docs/production/PRODUCTION_READINESS_CLEANUP_CHECKLIST.md`'s
  Permanent Testing and Training Agencies and Production Data
  Migration Strategy sections — Angela/Silva are permanent synthetic
  agencies (training/marketing) and must be visually distinguishable
  from real production agencies like Love & Faith, consistent with
  Section 1's separate "Training Agencies" / "Demo Agencies" health
  categories.
- Section 9 (Development Priority Engine) feeds directly into
  `docs/roadmap/Future-Ideas-And-Research.md`: ranked friction/alert/
  correction/guidance signals become candidate entries there (Date
  Added, Platform Area, Problem Being Solved, Expected Benefit,
  Status), not automatic roadmap commitments.
- The "Important Rule" (no patient-level data) is the same
  patient-privacy boundary already established for the Owner Platform
  in `docs/roadmap/Owner-Platform-Roadmap.md` ("Owner Platform Does Not
  Contain: Patient Workflows, Clinical Documentation, RNICA
  Workflows...") — this page must never become a clinical review tool.

## Change Log

| Date | Change |
|---|---|
| 2026-09-16 | Document created — full Analytics page re-design specification: rationale for retiring DAU/WAU/MAU/login-count metrics, proposed rename ("Agency Health Intelligence" or "Operational Intelligence"), Mission, 9-section design (Agency Health Overview, Top Alert Categories, Workflow Friction, Most Common Corrections, Most Common Help Requests, Alert Trend Intelligence, Agency Comparison, SNS Improvement Signals, Development Priority Engine), and the no-patient-data Important Rule. Status: Future Design Specification — do not implement until approved. |
