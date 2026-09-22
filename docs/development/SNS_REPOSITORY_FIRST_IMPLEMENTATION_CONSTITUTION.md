# SNS Hospice Solutions

# Repository-First Implementation Constitution

## Purpose

This document governs all development work performed within SNS Hospice Solutions.

Its purpose is to prevent:

- context loss
- repository drift
- duplicate architecture
- duplicate business rules
- requirements rediscovery
- unnecessary reports
- implementation inconsistency
- deviation from approved SNS workflows

This document applies to:

- RNICA
- Patient Chart
- HOPE
- Owner Platform
- Biller Platform
- Compliance
- Visit Management
- Orders
- Plan of Care
- Certifications
- Recertifications
- All SNS Hospice Solutions applications

# SECTION 1

# REPOSITORY FIRST

## Mandatory Rule

Before making ANY recommendation, design decision, implementation decision, UI change, refactor, migration, workflow modification, or architecture suggestion:

GitHub MUST inspect the repository.

Never assume.

Never rely on previous conversation memory.

Never rely on previous session memory.

Never assume implementation status.

Repository evidence is authoritative.

# SECTION 2

# MANDATORY SESSION START CHECKLIST

At the beginning of EVERY coding session GitHub must execute:

## Step 1

### Repository Refresh

Open and review:

- Current branch
- Current git status
- Current checkpoint
- Current active workstream

Return:

```
REPOSITORY REFRESH COMPLETE
```

## Step 2

### Current Implementation State

Inspect:

- Current route
- Current page
- Current component
- Current API
- Current tests
- Current styles

Return:

```
CURRENT IMPLEMENTATION FOUND
```

with exact file paths.

## Step 3

### Authority Refresh

Mandatory RNICA document refresh:

- RNICA_IMPLEMENTATION_AUTHORITY
- RNICA_SCREEN_AUTHORITY_MATRIX
- RNICA_WORKFLOW_AUTHORITY_MAP
- RNICA_DATA_MAPPING_MATRIX
- RNICA_AI_GOVERNANCE
- RNICA_LOCK_READINESS_MATRIX
- RNICA_GITHUB_HANDOFF_PLAN
- RNICA_REDESIGN_SOURCE_OF_TRUTH

Do not skip documents because they were read in a previous session.

## Step 4

### Current Progress Refresh

Return:

- CURRENT CHECKPOINT
- CURRENT SCREEN
- LAST COMPLETED SCREEN
- NEXT SCREEN
- KNOWN OPEN DEFECTS
- KNOWN CLOSED DEFECTS

before coding begins.

# SECTION 3

# NO ASSUMPTION RULE

GitHub may NOT assume:

- Field missing
- Validation missing
- Workflow missing
- Feature missing
- API missing
- Component missing
- Theme missing
- Design missing

until repository evidence proves it.

Required output:

```
IMPLEMENTATION FOUND
```

or

```
IMPLEMENTATION NOT FOUND
```

# SECTION 4

# REUSE BEFORE CREATE

Before creating:

- Component
- Context
- Store
- Hook
- Utility
- API
- Route
- CSS Module
- Tailwind Utility
- Theme Token

GitHub must search repository first.

Required output:

```
EXISTING IMPLEMENTATION FOUND
```

or

```
NO EXISTING IMPLEMENTATION FOUND
```

Only then may code be created.

# SECTION 5

# RNICA PRESERVATION RULE

RNICA redesign is:

- Presentation
- Navigation
- Usability
- Workflow organization

NOT:

- New clinical rules
- New validation
- New response values
- New ACP logic
- New HOPE logic
- New readiness engine

Preserve:

- Fields
- Storage
- Validation
- Responses
- Visibility
- Autosave
- Readiness
- Lock
- Amendments
- Audit

unless an approved defect specifically requires change.

# SECTION 6

# SHADCN UTILIZATION POLICY

## Approved Usage

GitHub SHOULD use shadcn/ui for:

- Card
- Badge
- Button
- Sheet
- Drawer
- Dialog
- AlertDialog
- Popover
- Tooltip
- Accordion
- Tabs
- Table
- Command
- ScrollArea
- Select
- Combobox
- Breadcrumb
- Skeleton
- Separator
- Alert
- Progress

These components are approved implementation primitives.

## Prohibited Usage

GitHub MUST NOT import:

- Complete dashboards
- Admin templates
- Generated EMR layouts
- Generated patient charts
- Generated navigation systems
- Generated sidebars
- Generated workflow screens

SNS owns:

- Workflow
- Navigation
- Branding
- Layout
- RNICA experience

shadcn provides:

- Primitives only

# SECTION 7

# SHADCN INTEGRATION REQUIREMENT

All shadcn components must use SNS theming.

Never use:

- Hardcoded shadcn colors

Always map to SNS tokens.

Required token categories:

- --sns-bg
- --sns-surface
- --sns-card
- --sns-border
- --sns-text
- --sns-text-muted
- --sns-primary
- --sns-accent
- --sns-success
- --sns-warning
- --sns-danger
- --sns-ai

# SECTION 8

# LIGHT AND DARK THEMES

Every new screen must support:

- Desktop Light
- Desktop Dark
- Mobile Light
- Mobile Dark

Theme verification required before completion.

No exceptions.

# SECTION 9

# SCREEN COMPLETION RULE

A screen is NOT complete because:

- Route exists
- Component renders
- Data loads
- Tests pass

A screen IS complete only when:

- Figma parity verified
- Desktop Light verified
- Desktop Dark verified
- Mobile Light verified
- Mobile Dark verified
- Functionality preserved
- Tests pass
- Build passes

# SECTION 10

# VISUAL AUTHORITY

Figma controls:

- Spacing
- Layout
- Hierarchy
- Navigation
- Card composition
- Information architecture

Repository controls:

- Data
- Behavior
- Validation
- Storage
- APIs
- Workflow

GitHub must align both.

Neither replaces the other.

# SECTION 11

# IMPLEMENTATION OVER REPORTS

If these already exist:

- Authority doc
- Source-of-truth doc
- Gap report
- Implementation plan

GitHub MUST implement.

Do not generate:

- Another authority matrix
- Another gap report
- Another roadmap
- Another inventory

unless specifically requested.

# SECTION 12

# VISUAL VERIFICATION RULE

Source inspection:

```
≠ Visual verification
```

Before declaring completion GitHub must:

- Load screen
- Render screen
- Verify screen
- Compare to reference

in all four modes.

# SECTION 13

# REQUIRED SESSION OUTPUT

Every session must begin with:

```
SESSION REFRESH COMPLETE

Branch:
Current checkpoint:
Current screen:
Last completed screen:
Next screen:

Authority documents reviewed:
Files inspected:
Components reused:
Open defects:
Closed defects:
```

before any implementation work begins.

# SECTION 14

# DEFAULT ACTION

Default action is:

```
Implement
```

not:

```
Analyze
```

not:

```
Report
```

not:

```
Rediscover
```

If enough repository evidence exists:

```
IMPLEMENT.
```

# Immediate Instruction to GitHub

Add this file to the repository and make it mandatory for every SNS Hospice Solutions session.

At the beginning of each coding session:

1. Load this constitution.
2. Execute the Session Start Checklist.
3. Refresh repository state.
4. Refresh RNICA authority documents.
5. Verify current checkpoint.
6. Then begin implementation.

Use shadcn/ui as an implementation toolkit to improve SNS component quality, accessibility, spacing, consistency, responsive behavior, dialogs, cards, tables, navigation controls, and workflow presentation.

Do not use shadcn templates or generated application layouts.

SNS remains the design system. shadcn remains the component toolkit.
