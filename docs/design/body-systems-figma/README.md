# SNS Hospice Solutions — Body Systems Figma Reference

Status: canonical visual reference for the SNS Body Systems clinical register
(Initial Comprehensive RN Assessment, with reusable Routine RN and
Recertification modes).

**`SNS_Body_Systems_Engineering_Specification.md`** in this folder is the
governing engineering specification for the Body Systems rebuild. It is the
authority for domain model, ownership registry, visit-mode behavior, the
assessment state machine, validation/exception architecture, AI governance,
and testing requirements. Where any image in this folder appears to conflict
with that specification, **the specification wins** — per its own §16
("Figma-to-Code Interpretation Rules"), sample content, mock dates/counts/
statuses, and specific patient facts shown in these screenshots are fixtures
for illustrating layout and workflow only. They are **not** business rules,
default values, or schema requirements. Only the specification document (and
an approved field inventory, where referenced) defines behavior.

`SNS_DESIGN_SYSTEM_1.0.md` remains the single governing visual design system
(typography scale, color tokens, Facesheet Card Standard, Bold Text Policy,
Color Policy) for all SNS modules, including Body Systems. This folder
documents Body Systems' page-specific **layout/content/workflow** — it does
not introduce a separate theme or override those tokens.

## Screenshots in this folder

| File | Shows |
|---|---|
| `Desktop - Clinical register entry.png` | The ten-system register/navigation shell (entry point into Body Systems) |
| `Desktop - Admission comprehensive manual.png` | Initial Comprehensive RN Assessment, manual (non-AI) workflow |
| `Desktop - Routine manual - stable path.png` | Routine RN visit mode, manual workflow, a stable/no-change path |
| `Desktop - Recertification comparison.png` | Recertification mode's current-vs-prior-period comparison view |
| `Desktop - Unable-to-assess path.png` | The "unable to assess" situation branch (scope, reason, follow-up) |
| `Desktop - Matched manual symptom.png` | A matched/triggered symptom detail flow in manual documentation |
| `Desktop - AI-assisted symptom - exceptions.png` | AI-assisted extraction flow and the review-exception surface together |
| `Desktop - Final nurse review by exception.png` | The final nurse review-by-exception surface (not a second full re-assessment) |
| `Desktop - Integumentary - retained body diagram.png` | Integumentary's body-location diagram aid alongside the structured wound record |
| `Mobile - Manual continuous register.png` | Mobile single-column continuous register layout |
| `Mobile - AI-assisted exceptions.png` | Mobile AI-assisted + exceptions layout |
| `Owner priority - scenario worksheets and evidence.png` | Owner's prioritized scenario worksheets / supporting evidence (planning artifact, not a screen) |

## How to use this reference

1. Read `SNS_Body_Systems_Engineering_Specification.md` completely before
   implementing any slice of Body Systems.
2. Use these images only to classify visible elements per the
   specification's §16 categories (sample content / visual token / reusable
   component / workflow state / business rule / clinical requirement) —
   never copy a sample value, mock count, or specific patient fact as a
   default or validation rule.
3. Prefer the repository's actual installed stack and existing component
   conventions (see the specification's §3 and §19 preamble) over
   reproducing a screenshot pixel-for-pixel where the two conflict.
