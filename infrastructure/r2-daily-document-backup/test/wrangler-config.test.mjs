import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const configPath = new URL("../wrangler.toml", import.meta.url);
const workerPath = new URL("../src/index.js", import.meta.url);

test("production R2 bindings target the exact EU-jurisdiction buckets", async () => {
  const config = await readFile(configPath, "utf8");

  assert.match(config, /workers_dev\s*=\s*false/);
  assert.match(config, /\[triggers\]\s*\ncrons\s*=\s*\["15 2 \* \* \*"\]/);
  assert.match(
    config,
    /\[\[r2_buckets\]\]\s*\nbinding\s*=\s*"PRIMARY_DOCUMENTS"\s*\nbucket_name\s*=\s*"clmone-documents"\s*\njurisdiction\s*=\s*"eu"/,
  );
  assert.match(
    config,
    /\[\[r2_buckets\]\]\s*\nbinding\s*=\s*"BACKUP_DOCUMENTS"\s*\nbucket_name\s*=\s*"clmone-documents-backup"\s*\njurisdiction\s*=\s*"eu"/,
  );
  assert.doesNotMatch(config, /^(?:route|routes)\s*=/m);
});

test("worker remains scheduled-only and preserves immutable, no-delete semantics", async () => {
  const source = await readFile(workerPath, "utf8");

  assert.doesNotMatch(source, /\bfetch\s*\(/);
  assert.equal(source.includes(".delete("), false);
  assert.equal(source.includes("deleteAll"), false);
  assert.match(source, /_backup_versions\/v1\//);
  assert.match(source, /last-success\.json/);
});
