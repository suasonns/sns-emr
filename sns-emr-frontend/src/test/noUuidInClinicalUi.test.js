import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { describe, it, expect } from "vitest";

// Owner directive ("RECURRING DEFECT"): internal identifiers
// (assessmentId/visitId/patientId/documentId/recordId/noteId/uuid and
// their *_id / *.id snake_case/camelCase forms) must never be rendered
// as visible text in clinician-facing screens -- only used as React
// `key`s, API call parameters, or `data-*` attributes (support/audit
// tooling, devtools inspection). This recurring leak was found and
// fixed independently in four sibling "assessment history" tables
// (RNICA/Nursing, MSW/Psychosocial, SC/Spiritual, and the chart-level
// cross-discipline history) plus the RNICA footer bar -- the same
// copy-pasted pattern kept reappearing. This is a static source scan
// (not a DOM render) so it is cheap/fast and catches the exact
// regression pattern -- a bare `{something.assessmentId}` /
// `{something.record_id}` JSX text child, or a hardcoded UUID literal
// -- before it ships, without requiring every heavyweight
// clinician-facing screen to be mounted.

const CLINICIAN_FACING_FILES = [
  "../intake/NursingAssessmentBoard.jsx",
  "../intake/PsychosocialAssessmentBoard.jsx",
  "../intake/SpiritualAssessmentBoard.jsx",
  "../charts/PatientChart.jsx",
  "../components/RNICA.jsx",
  "../components/rn-ica/RNICACommandWorkspace.jsx",
];

// Matches a JSX text child that is *only* a raw identifier expression
// immediately after a tag boundary or a literal "ID"/"Id" label, e.g.
// `>{record.assessmentId}<`, `>{assessmentId}<`, `ID: {assessmentId}`,
// `>{item.record_id}<`, `>{note.note_id}<`.
const BARE_ID_RENDER_PATTERN =
  /[>:]\s*\{[\w.?]*\b(assessmentId|visitId|patientId|documentId|recordId|clinicalNoteId|record_id|note_id|visit_id|patient_id|document_id|clinical_note_id)\b[^}]*\}\s*[<]/gi;

// Matches a literal UUID/GUID string accidentally hardcoded into JSX text
// (e.g. a placeholder or example value that was never removed).
const UUID_LITERAL_PATTERN = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

function readSource(relPath) {
  return readFileSync(fileURLToPath(new URL(relPath, import.meta.url)), "utf8");
}

describe("No internal identifiers visible in clinician-facing RNICA/Nursing Assessment UI", () => {
  for (const relPath of CLINICIAN_FACING_FILES) {
    it(`${relPath} never renders a raw id/uuid as clinician-visible text`, () => {
      const source = readSource(relPath);

      const bareIdMatches = source.match(BARE_ID_RENDER_PATTERN) || [];
      // `data-*` attributes (e.g. `data-assessment-id={assessmentId}`) are
      // the approved place for an id to reach the DOM -- it is available
      // to support staff/devtools via Inspect Element but never painted
      // on screen. Exclude those from the violation list.
      const violations = bareIdMatches.filter((match) => !/data-[\w-]*=\s*$/.test(
        source.slice(Math.max(0, source.indexOf(match) - 40), source.indexOf(match)),
      ));

      expect(
        violations,
        `Found a raw identifier rendered as visible clinician-facing text in ${relPath}: ${JSON.stringify(violations)}`,
      ).toEqual([]);

      expect(
        UUID_LITERAL_PATTERN.test(source),
        `Found a hardcoded UUID/GUID literal in ${relPath} -- internal identifiers must never appear in clinician-facing source.`,
      ).toBe(false);
    });
  }
});
