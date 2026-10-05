// ════════════════════════════════════════════════════════════════
// Performance Scale Interpretations (owner directive, 2026-10-04)
// "Never assume users remember the meaning of PPS, KPS, FAST, NYHA, or
// ECOG values." Every documented score on these five standard,
// publicly-published clinical staging scales must be shown alongside an
// automatically-derived, plain-language interpretation and a one-line
// clinical-significance note -- the clinician never has to type this
// themselves, and it is never persisted (purely presentational, derived
// live from the already-stored score). The clinician's own free-text
// justification field for each scale is completely separate and
// unaffected by this file.
//
// Source: each table reflects the standard published criteria for that
// scale (Victoria Hospice PPSv2, Karnofsky Performance Status, ECOG/WHO
// Performance Status, Reisberg FAST, NYHA Functional Classification).
// Interpretation/significance text below is written in SNS's own words,
// not copied verbatim from any single publisher.
// ════════════════════════════════════════════════════════════════

export const PPS_INTERPRETATIONS = {
  "100%": { interpretation: "Full function, no evidence of disease.", significance: "Normal activity and work; full self-care; normal intake; fully conscious." },
  "90%": { interpretation: "Full function, some evidence of disease.", significance: "Normal activity and work; full self-care; normal intake; fully conscious." },
  "80%": { interpretation: "Normal activity with effort.", significance: "Some evidence of disease present; full self-care; normal or reduced intake; fully conscious." },
  "70%": { interpretation: "Reduced ambulation; unable to do normal job or work.", significance: "Significant disease present; full self-care; normal or reduced intake; fully conscious." },
  "60%": { interpretation: "Reduced ambulation; unable to do hobbies or housework.", significance: "Significant disease present; occasional assistance needed; normal or reduced intake; full consciousness or periods of confusion." },
  "50%": { interpretation: "Mainly sits or lies down; unable to do any work.", significance: "Extensive disease present; considerable assistance required; normal or reduced intake; full consciousness or periods of confusion." },
  "40%": { interpretation: "Mainly in bed.", significance: "Extensive disease present; mainly assistance required; normal or reduced intake; full consciousness, drowsiness, or confusion." },
  "30%": { interpretation: "Totally bedbound.", significance: "Unable to perform work activities. Extensive disease; total care required; reduced intake; full consciousness, drowsiness, or confusion." },
  "20%": { interpretation: "Totally bedbound.", significance: "Unable to perform work activities. Extensive assistance required; minimal intake (sips only); full consciousness, drowsiness, or confusion." },
  "10%": { interpretation: "Totally bedbound.", significance: "Extensive disease; total care required; mouth care only; drowsy or comatose, with or without confusion." },
  "0%": { interpretation: "Death.", significance: "No remaining function." },
};

export const KPS_INTERPRETATIONS = {
  "100": { interpretation: "Normal; no complaints.", significance: "No evidence of disease." },
  "90": { interpretation: "Able to carry on normal activity.", significance: "Minor signs or symptoms of disease." },
  "80": { interpretation: "Normal activity with effort.", significance: "Some signs or symptoms of disease." },
  "70": { interpretation: "Cares for self.", significance: "Unable to carry on normal activity or active work." },
  "60": { interpretation: "Requires occasional assistance.", significance: "Able to care for most of own personal needs." },
  "50": { interpretation: "Requires considerable assistance.", significance: "Requires frequent medical care." },
  "40": { interpretation: "Disabled.", significance: "Requires special care and assistance." },
  "30": { interpretation: "Severely disabled.", significance: "Hospitalization is indicated, though death is not imminent." },
  "20": { interpretation: "Very sick.", significance: "Hospitalization necessary; active supportive treatment required." },
  "10": { interpretation: "Moribund.", significance: "Fatal processes progressing rapidly." },
  "0": { interpretation: "Dead.", significance: "No remaining function." },
};

export const ECOG_INTERPRETATIONS = {
  "0": { interpretation: "Fully active.", significance: "Able to carry on all pre-disease performance without restriction." },
  "1": { interpretation: "Restricted in strenuous activity.", significance: "Ambulatory and able to carry out light work." },
  "2": { interpretation: "Ambulatory, capable of self-care.", significance: "Unable to carry out any work activities; up and about more than 50% of waking hours." },
  "3": { interpretation: "Limited self-care.", significance: "Confined to bed or chair more than 50% of waking hours." },
  "4": { interpretation: "Completely disabled.", significance: "Unable to carry on any self-care; totally confined to bed or chair." },
  "5": { interpretation: "Dead.", significance: "No remaining function." },
};

export const FAST_INTERPRETATIONS = {
  "1": { interpretation: "Normal.", significance: "No functional decline; normal aging or no dementia." },
  "2": { interpretation: "Very mild cognitive decline.", significance: "Subjective forgetfulness only; no objective functional deficit." },
  "3": { interpretation: "Mild cognitive decline.", significance: "Decreased performance noted by others at work or with complex tasks." },
  "4": { interpretation: "Mild dementia.", significance: "Decreased ability to perform complex tasks (e.g., managing finances, planning a meal, handling affairs)." },
  "5": { interpretation: "Moderate dementia.", significance: "Requires assistance selecting proper clothing for the occasion or weather." },
  "6a": { interpretation: "Moderately severe dementia.", significance: "Requires assistance dressing properly; may dress incorrectly without cueing." },
  "6b": { interpretation: "Moderately severe dementia.", significance: "Requires assistance bathing properly; may develop a fear of bathing." },
  "6c": { interpretation: "Moderately severe dementia.", significance: "Requires assistance with toileting mechanics (e.g., flushing, wiping)." },
  "6d": { interpretation: "Moderately severe dementia.", significance: "Urinary incontinence." },
  "6e": { interpretation: "Moderately severe dementia.", significance: "Fecal incontinence." },
  "7a": { interpretation: "Severe dementia.", significance: "Speech limited to about a half-dozen intelligible words or fewer in an average day." },
  "7b": { interpretation: "Severe dementia.", significance: "Speech limited to a single intelligible word in an average day." },
  "7c": { interpretation: "Severe dementia.", significance: "Loss of ambulation; cannot walk without personal assistance." },
  "7d": { interpretation: "Severe dementia.", significance: "Unable to sit up independently." },
  "7e": { interpretation: "Severe dementia.", significance: "Unable to smile." },
  "7f": { interpretation: "Severe dementia.", significance: "Unable to hold head up independently." },
};

export const NYHA_INTERPRETATIONS = {
  I: { interpretation: "No limitation.", significance: "Ordinary physical activity does not cause undue fatigue, palpitations, or dyspnea." },
  II: { interpretation: "Slight limitation of physical activity.", significance: "Comfortable at rest; ordinary activity results in fatigue, palpitations, or dyspnea." },
  III: { interpretation: "Marked limitation of physical activity.", significance: "Comfortable at rest; less-than-ordinary activity causes symptoms." },
  IV: { interpretation: "Severe limitation; symptomatic at rest.", significance: "Discomfort is present even at rest and increases with any physical activity." },
};

const SCALE_INTERPRETATION_TABLES = {
  pps: PPS_INTERPRETATIONS,
  kps: KPS_INTERPRETATIONS,
  ecog: ECOG_INTERPRETATIONS,
  fast: FAST_INTERPRETATIONS,
  nyha: NYHA_INTERPRETATIONS,
};

/** Looks up the plain-language interpretation + clinical-significance pair
 * for a given scale key ("pps" | "kps" | "ecog" | "fast" | "nyha") and the
 * currently-documented score. Returns null when there is no score yet, or
 * the score doesn't match a known value (e.g. legacy/out-of-range data) --
 * callers should treat null as "nothing to show", never as an error. */
export function getScaleInterpretation(scaleKey, value) {
  if (!value) return null;
  const table = SCALE_INTERPRETATION_TABLES[scaleKey];
  if (!table) return null;
  return table[value] || null;
}
