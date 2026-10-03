// Referral recommendation engine shared by Psychosocial, Spiritual, and
// Bereavement (owner design correction 2026-09-25): the RN documents
// findings only; SNS derives a binary (YES/NO) referral recommendation
// from those findings. This is deterministic rule-based logic, not a real
// AI/ML call -- consistent with the codebase's other "Suggest, Never
// Commit" patterns (e.g. ConstipationAutoAssessCard). The recommendation
// is display-only and is never written into formData: RN confirms by
// acting on it (making or not making the referral), then records the
// Family Response (Accepted / Refused / Deferred) themselves.
//
// Any documented finding other than "None indicated" triggers a YES
// recommendation -- there is no manual severity/priority tier for the RN
// to select.
export function resolveReferralRecommendation(indicators) {
  const list = (indicators || []).filter((i) => i !== "None indicated");
  if (list.length === 0) {
    return { recommended: false, reason: "No referral indicators documented." };
  }
  return { recommended: true, reason: `Referral indicator(s) documented: ${list.join(", ")}.` };
}
