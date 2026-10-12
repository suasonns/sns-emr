// Shared `visitMeta` (Visit Header) option lists -- single source of truth
// for both the classic RNICA.jsx "Visit Details" card and the Command
// Workspace Visit Header bar (RNICACommandWorkspace.jsx). Extracted here
// (rather than exported from RNICA.jsx) because RNICACommandWorkspace.jsx
// is imported BY RNICA.jsx -- importing back from RNICA.jsx would create a
// circular dependency. No new values are introduced; these are the exact
// option sets the classic Visit Details card already used.
export const TYPE_OF_VISIT_OPTIONS = ["In-Person", "Telephone", "Video"];
export const VISIT_KIND_OPTIONS = ["Scheduled", "Unscheduled", "Other"];
export const CARE_LEVEL_OPTIONS = ["Routine Care", "General Inpatient", "Continuous Care", "Respite Care"];
export const REASON_FOR_VISIT_OPTIONS = [
  "Initial Comprehensive Assessment",
  "Recertification",
  "Follow-up / Routine Visit",
  "Update/Revision",
  "Bereavement Support",
  "Crisis Intervention",
  "Discharge/Transfer",
  "Other",
];
