import React from "react";
import { Languages, Fingerprint, Home, Users2, ShieldCheck, Building2, LogIn, HeartHandshake, MessageCircleHeart } from "lucide-react";
import { Card, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../../ui/select";
import DemographicMultiSelect from "./DemographicMultiSelect";
import "../design-system/RnicaTailwind.css";
import "./HopeAdministrativeReview.css";

// HOPE Section A -- Administrative Information. A distinct RNICA screen,
// separate from Evidence & Intake and from Psychosocial, per owner
// direction (2026-09-25 architecture correction). This is NOT a
// demographics data-entry form and NOT a duplicate Face Sheet: it is the
// HOPE assessment's own point-in-time collection/confirmation of seven CMS
// items grouped by workflow concept (2026-09-25 density redesign):
//   Communication        -- A1110 Language, A1110 Interpreter
//   Living Environment    -- A0215 Site of Service, A1805 Admitted From,
//                            A1905 Living Arrangement, A1910 Availability
//                            of Assistance
//   Demographic Reporting -- A1005 Ethnicity, A1010 Race
// Every response set below is the complete CMS list -- never collapsed.
//
// Repository trace (2026-09-25): backend/app/models/patient_facesheet.py
// has unrestricted free-text race/ethnicity/language columns (not
// currently exposed by the frontend Face Sheet client) and has NO
// interpreter/living_arrangement/availability_of_assistance columns at
// all. There is currently no Face Sheet-authoritative value to reconcile
// these HOPE responses against. This is source-code documentation only --
// nothing in this comment block is ever rendered to a clinician.

// A0215 Site of Service at Admission -- official CMS codes (single source
// of truth, mirrors hopeReportMapper.js's SITE_OF_SERVICE_LABELS).
export const SITE_OF_SERVICE_LABELS = {
  "01": "Patient's Home/Residence",
  "02": "Assisted Living Facility",
  "03": "Nursing Long Term Care (LTC) or Non-Skilled Nursing Facility (NF)",
  "04": "Skilled Nursing Facility (SNF)",
  "05": "Inpatient Hospital",
  "06": "Inpatient Hospice Facility (General Inpatient (GIP))",
  "07": "Long Term Care Hospital (LTCH)",
  "08": "Inpatient Psychiatric Facility",
  "09": "Hospice Home Care (Routine Home Care (RHC)) Provided in a Hospice Facility",
  "99": "Not listed",
};

// A1805 Admitted From -- official CMS codes (mirrors hopeReportMapper.js's
// ADMITTED_FROM_LABELS).
export const ADMITTED_FROM_LABELS = {
  "01": "Home/Community (private home/apt., board/care, assisted living, group home, etc.)",
  "02": "Nursing Home (long-term care facility)",
  "03": "Skilled Nursing Facility (SNF, swing beds)",
  "04": "Short-Term General Hospital (acute hospital, IPPS)",
  "05": "Long-Term Care Hospital (LTCH)",
  "06": "Inpatient Rehabilitation Facility (IRF)",
  "07": "Inpatient Psychiatric Facility",
  "08": "Intermediate Care Facility (ID/DD facility)",
  "10": "Hospice (institutional facility)",
  "11": "Critical Access Hospital (CAH)",
  "99": "Not Listed",
};

// A1905 Living Arrangement codes -> display labels (single source of truth
// -- matches hopeReportMapper.js's LIVING_ARRANGEMENT_LABELS exactly).
export const LIVING_ARRANGEMENT_LABELS = {
  "1": "Alone (no other residents in the home)",
  "2": "With others in the home (e.g., family, friends, or paid caregiver)",
  "3": "Congregate home (e.g., assisted living or residential care home)",
  "4": "Inpatient facility (e.g., SNF, nursing home, inpatient hospice, hospital)",
  "5": "Does not have a permanent home",
};

// A1910 Availability of Assistance -- complete HOPE response set (matches
// hopeReportMapper.js's ASSISTANCE_MAP keys exactly).
export const AVAILABILITY_OPTIONS = ["24/7 available", "Daytime only", "Nighttime only", "Limited", "None"];

// A1005 Ethnicity -- complete HOPE response set (7 options).
export const ETHNICITY_OPTIONS = [
  "No, not of Hispanic, Latino/a, or Spanish origin",
  "Yes, Mexican, Mexican American, Chicano/a",
  "Yes, Puerto Rican",
  "Yes, Cuban",
  "Yes, Another Hispanic, Latino, or Spanish origin",
  "Patient unable to respond",
  "Patient declines to respond",
];

// A1010 Race -- complete HOPE response set (16 options). Never collapsed
// into "Asian" / "Pacific Islander" -- each is its own reportable option.
export const RACE_OPTIONS = [
  "White",
  "Black or African American",
  "American Indian or Alaska Native",
  "Asian Indian",
  "Chinese",
  "Filipino",
  "Japanese",
  "Korean",
  "Vietnamese",
  "Other Asian",
  "Native Hawaiian",
  "Guamanian or Chamorro",
  "Samoan",
  "Other Pacific Islander",
  "Patient unable to respond",
  "Patient declines to respond",
  "None of the above",
];

// A1110 Preferred Language -- controlled list (transcribed from the real
// reference implementation's dropdown, not invented/ISO-639-1).
export const LANGUAGE_OPTIONS = [
  "English", "Spanish", "Chinese", "Hindi", "French", "Arabic", "Bengali", "Russian", "Portuguese", "Indonesian",
  "Urdu", "Japanese", "German", "Punjabi", "Javanese", "Telugu", "Turkish", "Korean", "Marathi", "Vietnamese",
  "Afrikaans", "Albanian", "Armenian", "Basque", "Bulgarian", "Catalan", "Cambodian", "Croatian", "Czech", "Danish",
  "Dutch", "Estonian", "Fiji", "Finnish", "Georgian", "Greek", "Gujarati", "Hebrew", "Hmong", "Hungarian",
  "Icelandic", "Irish", "Italian", "Latin", "Latvian", "Lithuanian", "Macedonian", "Malay", "Malayalam", "Maltese",
  "Maori", "Mongolian", "Nepali", "Norwegian", "Persian", "Polish", "Quechua", "Romanian", "Samoan", "Serbian",
  "Slovak", "Slovenian", "Swahili", "Swedish", "Tamil", "Tatar", "Thai", "Tibetan", "Tonga", "Ukrainian",
  "Uzbek", "Welsh", "Xhosa", "Tagalog",
  "- No Information",
];

// A1110 Interpreter Needed -- three-state HOPE response (not boolean).
export const INTERPRETER_NEEDED_OPTIONS = [
  { value: "no", label: "No" },
  { value: "yes", label: "Yes" },
  { value: "unable", label: "Unable to determine" },
];

// Operational (non-CMS) follow-up fields present in the reference
// HospiceMD "Communications & Other Factors" section. Not HOPE-required --
// F2000/F2100/F2200 (the other HospiceMD items in that same section) are
// intentionally NOT duplicated here; they are already fully implemented on
// the separate Advanced Care Planning screen (RNICA.jsx `advancedCarePlanning`).
// Cross-checked 2026-09-25 against real HospiceMD screenshots of this exact
// section ("If Yes, offer of interpreter" dropdown) -- richer response set
// than HospiceMD's, per owner direction to exceed (not just match) parity.
export const INTERPRETER_OFFERED_OPTIONS = [
  { value: "n/a", label: "N/A" },
  { value: "offered_accepted", label: "Offered and accepted" },
  { value: "offered_declined", label: "Offered and declined" },
  { value: "needed_unavailable", label: "Needed but unavailable" },
  { value: "pending", label: "Pending arrangement" },
  { value: "unable", label: "Unable to determine" },
];
export const UNDERSTANDS_PARTICIPATES_OPTIONS = [
  { value: "yes", label: "Yes" },
  { value: "partially", label: "Partially" },
  { value: "no", label: "No" },
  { value: "unable", label: "Unable to assess" },
];
// "Any special event/desire for patient before dying?" -- matches
// HospiceMD's own field 1:1; the documented wish itself, an optional
// follow-up discipline, and a review status are SNS operational additions
// shown only when a wish is actually documented (progressive disclosure).
export const SPECIAL_WISH_STATUS_OPTIONS = [
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
  { value: "unable", label: "Unable to assess" },
];
export const SPECIAL_WISH_FOLLOWUP_DISCIPLINE_OPTIONS = [
  "RN", "MSW", "Chaplain/Spiritual Counselor", "Physician", "IDG Team", "Other",
];
export const SPECIAL_WISH_REVIEW_STATUS_OPTIONS = [
  "Documented", "Reviewed by IDG", "Action Planned", "Fulfilled", "No Longer Applicable",
];


// Every field here is currently sourced ONLY from this HOPE assessment's
// own point-in-time response (`formData.demographics` /
// `formData.livingSituation`) -- there is no Face Sheet-authoritative
// value to reconcile against yet (see file header comment / repository
// trace). This state is surfaced honestly rather than labeled "Verified"
// or "Confirmed", which would imply a reconciliation that hasn't happened.
function ReviewSection({ icon: Icon, title, itemCode, fullWidth, children }) {
  return (
    <div className={"rnica-hope-section" + (fullWidth ? " rnica-hope-section--full" : "")}>
      <div className="rnica-hope-section__heading">
        <Icon className="h-3.5 w-3.5" />
        <span>{title}</span>
        <Badge variant="neutral">{itemCode ? `HOPE ${itemCode}` : "Operational"}</Badge>
      </div>
      {children}
    </div>
  );
}

// Groups related HOPE Section A fields under one compact label so a nurse
// can scan by workflow concept (Communication / Living Environment /
// Demographic Reporting) instead of one field per card. Purely a visual
// grouping -- no change to persistence or field ownership.
function ReviewGroup({ title, columns, children }) {
  return (
    <div className="rnica-hope-group">
      <div className="rnica-hope-group__title">{title}</div>
      <div className={`rnica-hope-group__fields rnica-hope-group__fields--${columns}`}>
        {children}
      </div>
    </div>
  );
}

export default function HopeAdministrativeReview({ value, onUpdateField, locked }) {
  const demographics = value || {};
  const interpreterValue =
    demographics.needsInterpreter === true ? "yes" : demographics.needsInterpreter === false ? "no" : "unable";

  const missingCount = [
    (demographics.ethnicity || []).length === 0,
    (demographics.race || []).length === 0,
    !demographics.preferredLanguage,
    !demographics.siteOfService,
    !demographics.admittedFrom,
    !demographics.livingArrangement,
    !demographics.availabilityOfAssistance,
  ].filter(Boolean).length;

  return (
    <div className="rnica-hope-admin">
      <Card className="rnica-ds-card rnica-hope-admin__summary">
        <CardContent className="rnica-hope-admin__summary-row">
          <span className="rnica-hope-admin__title"><ShieldCheck className="h-4 w-4" /> HOPE Administrative Review</span>
          <span className="rnica-hope-admin__note">
            CMS Section A items collected at this HOPE timepoint &mdash; not a duplicate Face Sheet.
            Corrections to the patient&rsquo;s operational record must be made through Face Sheet.
          </span>
          <Badge variant={missingCount === 0 ? "success" : "warning"}>
            {missingCount === 0 ? "All items collected" : `${missingCount} not yet collected`}
          </Badge>
          {locked && <Badge variant="neutral">Locked</Badge>}
        </CardContent>
      </Card>

      <Card className="rnica-ds-card rnica-hope-admin__body">
        <CardContent className="rnica-hope-admin__grid">
          <ReviewGroup title="Communication" columns="3">
            <ReviewSection icon={Languages} title="Preferred Language" itemCode="A1110">
              <Select
                value={demographics.preferredLanguage || undefined}
                disabled={locked}
                onValueChange={(v) => onUpdateField?.("demographics", "preferredLanguage", v)}
              >
                <SelectTrigger><SelectValue placeholder="Select&hellip;" /></SelectTrigger>
                <SelectContent>
                  {LANGUAGE_OPTIONS.map((opt) => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                </SelectContent>
              </Select>
            </ReviewSection>

            <ReviewSection icon={Languages} title="Interpreter Needed or Wanted" itemCode="A1110">
              <Select
                value={interpreterValue}
                disabled={locked}
                onValueChange={(v) => onUpdateField?.("demographics", "needsInterpreter", v === "yes" ? true : v === "no" ? false : null)}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {INTERPRETER_NEEDED_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </ReviewSection>

            {/* Progressive disclosure: stays visible+discoverable but only
                editable once an interpreter has been needed, wanted, or is
                clinically under consideration (not a flat "No"). */}
            <ReviewSection icon={Languages} title="Interpreter Offered">
              <Select
                value={demographics.interpreterOffered || "n/a"}
                disabled={locked || interpreterValue === "no"}
                onValueChange={(v) => onUpdateField?.("demographics", "interpreterOffered", v)}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {INTERPRETER_OFFERED_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
                </SelectContent>
              </Select>
              {demographics.interpreterOffered === "needed_unavailable" && (
                <Badge variant="warning" className="rnica-hope-followup-badge">Follow-up needed</Badge>
              )}
            </ReviewSection>

            <ReviewSection icon={HeartHandshake} title="Understands &amp; Participates in Own Care">
              <Select
                value={demographics.understandsParticipatesInCare || undefined}
                disabled={locked}
                onValueChange={(v) => onUpdateField?.("demographics", "understandsParticipatesInCare", v)}
              >
                <SelectTrigger><SelectValue placeholder="Select&hellip;" /></SelectTrigger>
                <SelectContent>
                  {UNDERSTANDS_PARTICIPATES_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </ReviewSection>

            <ReviewSection icon={MessageCircleHeart} title="Special Event/Desire Before Dying">
              <Select
                value={demographics.specialWishStatus || undefined}
                disabled={locked}
                onValueChange={(v) => onUpdateField?.("demographics", "specialWishStatus", v)}
              >
                <SelectTrigger><SelectValue placeholder="Select&hellip;" /></SelectTrigger>
                <SelectContent>
                  {SPECIAL_WISH_STATUS_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </ReviewSection>

            {/* Full-width narrative only opens conditionally, when a wish has
                actually been documented -- per progressive-disclosure rule. */}
            {demographics.specialWishStatus === "yes" && (
              <ReviewSection icon={MessageCircleHeart} title="Documented Wish" fullWidth>
                <textarea
                  className="rnica-hope-textarea"
                  rows={2}
                  disabled={locked}
                  placeholder="e.g. attend granddaughter's wedding"
                  value={demographics.specialEventDesire || ""}
                  onChange={(e) => onUpdateField?.("demographics", "specialEventDesire", e.target.value)}
                />
                <div className="rnica-hope-group__fields--2" style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(200px, 1fr))", gap: 16, marginTop: 8 }}>
                  <Select
                    value={demographics.specialWishFollowUpDiscipline || undefined}
                    disabled={locked}
                    onValueChange={(v) => onUpdateField?.("demographics", "specialWishFollowUpDiscipline", v)}
                  >
                    <SelectTrigger><SelectValue placeholder="Follow-up owner/discipline (optional)" /></SelectTrigger>
                    <SelectContent>
                      {SPECIAL_WISH_FOLLOWUP_DISCIPLINE_OPTIONS.map((opt) => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                    </SelectContent>
                  </Select>
                  <Select
                    value={demographics.specialWishReviewStatus || undefined}
                    disabled={locked}
                    onValueChange={(v) => onUpdateField?.("demographics", "specialWishReviewStatus", v)}
                  >
                    <SelectTrigger><SelectValue placeholder="Review status" /></SelectTrigger>
                    <SelectContent>
                      {SPECIAL_WISH_REVIEW_STATUS_OPTIONS.map((opt) => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </ReviewSection>
            )}
          </ReviewGroup>

          <ReviewGroup title="Living Environment" columns="4">
            <ReviewSection icon={Building2} title="Site of Service at Admission" itemCode="A0215">
              <Select
                value={demographics.siteOfService || undefined}
                disabled={locked}
                onValueChange={(v) => onUpdateField?.("livingSituation", "siteOfService", v)}
              >
                <SelectTrigger><SelectValue placeholder="Select&hellip;" /></SelectTrigger>
                <SelectContent>
                  {Object.entries(SITE_OF_SERVICE_LABELS).map(([code, label]) => (
                    <SelectItem key={code} value={code}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </ReviewSection>

            <ReviewSection icon={LogIn} title="Admitted From" itemCode="A1805">
              <Select
                value={demographics.admittedFrom || undefined}
                disabled={locked}
                onValueChange={(v) => onUpdateField?.("livingSituation", "admittedFrom", v)}
              >
                <SelectTrigger><SelectValue placeholder="Select&hellip;" /></SelectTrigger>
                <SelectContent>
                  {Object.entries(ADMITTED_FROM_LABELS).map(([code, label]) => (
                    <SelectItem key={code} value={code}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </ReviewSection>

            <ReviewSection icon={Home} title="Living Arrangement" itemCode="A1905">
              <Select
                value={demographics.livingArrangement || undefined}
                disabled={locked}
                onValueChange={(v) => onUpdateField?.("livingSituation", "livingArrangement", v)}
              >
                <SelectTrigger><SelectValue placeholder="Select&hellip;" /></SelectTrigger>
                <SelectContent>
                  {Object.entries(LIVING_ARRANGEMENT_LABELS).map(([code, label]) => (
                    <SelectItem key={code} value={code}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </ReviewSection>

            <ReviewSection icon={Users2} title="Availability of Assistance" itemCode="A1910">
              <Select
                value={demographics.availabilityOfAssistance || undefined}
                disabled={locked}
                onValueChange={(v) => onUpdateField?.("livingSituation", "availabilityOfAssistance", v)}
              >
                <SelectTrigger><SelectValue placeholder="Select&hellip;" /></SelectTrigger>
                <SelectContent>
                  {AVAILABILITY_OPTIONS.map((opt) => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                </SelectContent>
              </Select>
            </ReviewSection>
          </ReviewGroup>

          <ReviewGroup title="Demographic Reporting" columns="2">
            <ReviewSection icon={Fingerprint} title="Ethnicity" itemCode="A1005">
              <DemographicMultiSelect
                title="Ethnicity"
                itemCode="A1005"
                options={ETHNICITY_OPTIONS}
                value={demographics.ethnicity || []}
                onChange={(next) => onUpdateField?.("demographics", "ethnicity", next)}
                disabled={locked}
                informationSource={demographics.ethnicityInformationSource}
                informationSourceOther={demographics.ethnicityInformationSourceOther}
                onInformationSourceChange={(v) => onUpdateField?.("demographics", "ethnicityInformationSource", v)}
                onInformationSourceOtherChange={(v) => onUpdateField?.("demographics", "ethnicityInformationSourceOther", v)}
              />
            </ReviewSection>

            <ReviewSection icon={Fingerprint} title="Race" itemCode="A1010">
              <DemographicMultiSelect
                title="Race"
                itemCode="A1010"
                options={RACE_OPTIONS}
                value={demographics.race || []}
                onChange={(next) => onUpdateField?.("demographics", "race", next)}
                disabled={locked}
                informationSource={demographics.raceInformationSource}
                informationSourceOther={demographics.raceInformationSourceOther}
                onInformationSourceChange={(v) => onUpdateField?.("demographics", "raceInformationSource", v)}
                onInformationSourceOtherChange={(v) => onUpdateField?.("demographics", "raceInformationSourceOther", v)}
              />
            </ReviewSection>
          </ReviewGroup>
        </CardContent>
      </Card>
    </div>
  );
}
