// HOPE-E2E-AUTH-001: loads the already-existing dev login credentials
// from backend/.env at runtime so Playwright can authenticate as a real
// user through the real /auth/login endpoint. backend/.env is gitignored
// (see backend/.gitignore) and already contains DEV_RN_EMAIL /
// DEV_RN_PASSWORD, provisioned by scripts/seed_login_accounts.py for
// exactly this kind of local tooling.
//
// Rules enforced here:
//  - Never hardcode a credential literal in any committed file.
//  - Never log/print a credential value (not even in an error message).
//  - Fail loudly with a clear, actionable message if a credential is
//    missing -- never silently fall back to a guessed/default value,
//    which could mask pointing tests at the wrong environment.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const BACKEND_ENV_PATH = resolve(HERE, "../../../backend/.env");

function parseEnvFile(path: string): Record<string, string> {
  let raw: string;
  try {
    raw = readFileSync(path, "utf8");
  } catch {
    throw new Error(
      `[e2e] Could not read ${path}. Playwright auth setup reads dev login ` +
        "credentials from backend/.env (gitignored, local-only) -- create it " +
        "(see backend/.env.example if present, or provision via " +
        "scripts/seed_login_accounts.py) before running e2e tests.",
    );
  }

  const values: Record<string, string> = {};
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    const value = trimmed.slice(eq + 1).trim();
    values[key] = value;
  }
  return values;
}

export type TestCredentials = {
  email: string;
  password: string;
  tenantId: string;
};

export function loadRnTestCredentials(): TestCredentials {
  const env = parseEnvFile(BACKEND_ENV_PATH);
  const email = env.DEV_RN_EMAIL;
  const password = env.DEV_RN_PASSWORD;
  const tenantId = env.DEV_TENANT_ID;

  const missing = [
    !email && "DEV_RN_EMAIL",
    !password && "DEV_RN_PASSWORD",
    !tenantId && "DEV_TENANT_ID",
  ].filter(Boolean);

  if (missing.length > 0) {
    // Deliberately does not echo any value, even the ones that ARE set.
    throw new Error(
      `[e2e] backend/.env is missing required key(s): ${missing.join(", ")}. ` +
        "Cannot authenticate the Playwright test user without these.",
    );
  }

  return { email, password, tenantId };
}
