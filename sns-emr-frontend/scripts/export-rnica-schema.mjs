#!/usr/bin/env node
/**
 * export-rnica-schema.mjs
 *
 * Groundwork for the future transcript -> RNICA field extraction pipeline.
 *
 * RNICA.jsx's SECTION_CONFIGS object is the single source of truth for every
 * structured field in the form (path, label, input type, options, HOPE/CDPH
 * flags). Rather than hand-maintaining a second copy of that list for the
 * backend/AI layer (which would drift the moment someone edits a field in
 * the UI), this script statically parses RNICA.jsx's AST and extracts
 * SECTION_CONFIGS into a plain JSON schema — no React/JSX execution, so it
 * has no runtime dependencies and can run in CI or a backend build step.
 *
 * Output: sns-emr-frontend/schemas/rnica-field-schema.json
 *
 * NOTE: `demographics` is rendered via bespoke JSX (not a SECTION_CONFIGS
 * entry) and is intentionally left out for now — flagged in the output
 * under `_notes` as a follow-up rather than silently omitted.
 *
 * Run: node scripts/export-rnica-schema.mjs
 */
import { parse } from "@babel/parser";
import traverseModule from "@babel/traverse";
const traverse = traverseModule.default || traverseModule;
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SOURCE_FILE = path.join(__dirname, "..", "src", "components", "RNICA.jsx");
const OUTPUT_FILE = path.join(__dirname, "..", "schemas", "rnica-field-schema.json");

function literalValue(node) {
  if (!node) return undefined;
  switch (node.type) {
    case "StringLiteral":
    case "NumericLiteral":
    case "BooleanLiteral":
      return node.value;
    case "NullLiteral":
      return null;
    case "ArrayExpression":
      return node.elements.map((el) => (el ? literalValue(el) : null));
    case "ObjectExpression":
      return objectExpressionToPlain(node);
    case "TemplateLiteral":
      // Best-effort: concatenate quasis, ignore interpolations (none expected here).
      return node.quasis.map((q) => q.value.cooked).join("");
    default:
      return undefined;
  }
}

function objectExpressionToPlain(objExpr) {
  const out = {};
  for (const prop of objExpr.properties) {
    if (prop.type !== "ObjectProperty") continue;
    const key = prop.key.type === "Identifier" ? prop.key.name : prop.key.value;
    out[key] = literalValue(prop.value);
  }
  return out;
}

function main() {
  const code = fs.readFileSync(SOURCE_FILE, "utf8");
  const ast = parse(code, {
    sourceType: "module",
    plugins: ["jsx"],
  });

  let sectionConfigsNode = null;

  traverse(ast, {
    VariableDeclarator(nodePath) {
      if (
        nodePath.node.id.type === "Identifier" &&
        nodePath.node.id.name === "SECTION_CONFIGS" &&
        nodePath.node.init?.type === "ObjectExpression"
      ) {
        sectionConfigsNode = nodePath.node.init;
      }
    },
  });

  if (!sectionConfigsNode) {
    console.error("Could not find SECTION_CONFIGS in RNICA.jsx — schema export aborted.");
    process.exit(1);
  }

  const sections = {};
  let fieldCount = 0;
  let skippedCustomCards = 0;

  for (const sectionProp of sectionConfigsNode.properties) {
    if (sectionProp.type !== "ObjectProperty") continue;
    const sectionKey = sectionProp.key.type === "Identifier" ? sectionProp.key.name : sectionProp.key.value;
    const sectionObj = sectionProp.value;
    if (sectionObj.type !== "ObjectExpression") continue;

    const sectionPlain = { title: undefined, subtitle: undefined, fields: [] };

    for (const sp of sectionObj.properties) {
      if (sp.type !== "ObjectProperty") continue;
      const spKey = sp.key.type === "Identifier" ? sp.key.name : sp.key.value;
      if (spKey === "title") sectionPlain.title = literalValue(sp.value);
      if (spKey === "subtitle") sectionPlain.subtitle = literalValue(sp.value);
      if (spKey === "cards" && sp.value.type === "ArrayExpression") {
        for (const cardNode of sp.value.elements) {
          if (!cardNode || cardNode.type !== "ObjectExpression") continue;
          const card = objectExpressionToPlain(cardNode);
          if (card.customRenderer) {
            // Custom cards (DeclineTracker, HopeComorbidities, weight-loss
            // auto-calc, etc.) are computed/derived UI, not raw input
            // fields for the extraction schema to target directly.
            skippedCustomCards += 1;
            continue;
          }
          if (Array.isArray(card.fields)) {
            for (const f of card.fields) {
              if (!f || !f.path) continue;
              sectionPlain.fields.push({
                path: `${sectionKey}.${f.path}`,
                label: f.label,
                type: f.type,
                options: f.options,
                hopeCode: f.hopeCode,
                sfv: f.sfv || false,
                cdphRequired: card.cms === "CDPH Required" || undefined,
              });
              fieldCount += 1;
            }
          }
        }
      }
    }

    sections[sectionKey] = sectionPlain;
  }

  const schema = {
    _generated_by: "scripts/export-rnica-schema.mjs",
    _generated_at: new Date().toISOString(),
    _source_file: "src/components/RNICA.jsx (SECTION_CONFIGS)",
    _notes: [
      "This schema covers every field rendered through renderGenericSection() " +
        "(i.e. every SECTION_CONFIGS entry). The 'demographics' section is " +
        "rendered via bespoke JSX (PCG, living situation, advance care " +
        "planning, etc.) rather than a SECTION_CONFIGS entry and is not yet " +
        "included here — a follow-up task if/when AI extraction needs to " +
        "reach those fields too.",
      "Cards with a customRenderer (decline tracker, HOPE comorbidities, " +
        "weight-loss auto-calc, constipation auto-assess, medication " +
        "orders, orders hub) are intentionally excluded: those are " +
        "computed/derived views, not raw fields for a transcript-extraction " +
        "layer to write into directly.",
      "Intended use: the future transcript-extraction service loads this " +
        "file to build its structured-output schema (e.g. an Azure OpenAI " +
        "function-calling schema), so the AI's job stays scoped to 'here is " +
        "the exact list of fields you may fill, with their exact allowed " +
        "values' rather than freeform guessing.",
    ],
    field_count: fieldCount,
    skipped_custom_render_cards: skippedCustomCards,
    sections,
  };

  fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(schema, null, 2));
  console.log(`Wrote ${fieldCount} fields across ${Object.keys(sections).length} sections to ${path.relative(process.cwd(), OUTPUT_FILE)}`);
}

main();
