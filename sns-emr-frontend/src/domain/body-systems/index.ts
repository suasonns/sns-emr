/**
 * SNS Body Systems — domain layer public barrel.
 *
 * Re-exports the public surface of the Body Systems domain foundation:
 * types (section 4), ownership registry (section 5), visit-mode
 * configuration (section 6), the assessment state machine (section 7),
 * validation/exception rules (section 8), and the legacy RNICA
 * compatibility adapter. Nothing outside this folder should import from
 * individual module files directly except where that is the existing
 * project convention — prefer importing from this barrel.
 */
export * from "./types";
export * from "./ownership";
export * from "./visitMode";
export * from "./stateMachine";
export * from "./exceptionRules";
export * from "./legacyRNICAAdapter";
