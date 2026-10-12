// Shared constant imported both by playwright.config.ts and
// e2e/auth.setup.ts. Kept in its own file (rather than exported from
// auth.setup.ts) because importing a Playwright test file from the
// config file executes its top-level `setup(...)` call outside of
// Playwright's test-loading context, which Playwright rejects with
// "did not expect test() to be called here".
export const RN_STORAGE_STATE_PATH = "e2e/.auth/rn-user.json";
