import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import worker, { backupKeyFor, parseBackupKey, runDailyDocumentBackup } from "../src/index.js";

class FakeBucket {
  constructor({ pageSize = Infinity } = {}) {
    this.pageSize = pageSize;
    this.objects = new Map();
    this.putCalls = [];
    this.deleteCalls = [];
    this.failPutFor = new Set();
  }

  async put(key, value, options = {}) {
    if (this.failPutFor.has(key)) throw new Error("intentional put failure");
    const bytes = await toBytes(value);
    const version = `version-${this.objects.size + 1}-${key}`;
    this.objects.set(key, {
      key,
      version,
      etag: `etag-${version}`,
      size: bytes.byteLength,
      uploaded: new Date("2026-08-18T02:15:00.000Z"),
      body: bytes,
      httpMetadata: options.httpMetadata || {},
      customMetadata: options.customMetadata || {},
    });
    this.putCalls.push(key);
    return this.head(key);
  }

  async get(key) {
    const object = this.objects.get(key);
    if (!object) return null;
    return {
      ...object,
      body: new ReadableStream({
        start(controller) {
          controller.enqueue(object.body);
          controller.close();
        },
      }),
    };
  }

  async head(key) {
    const object = this.objects.get(key);
    return object ? { ...object } : null;
  }

  async list({ cursor } = {}) {
    const keys = [...this.objects.keys()].sort();
    const start = cursor ? Number(cursor) : 0;
    const end = Math.min(start + this.pageSize, keys.length);
    return {
      objects: keys.slice(start, end).map((key) => ({ ...this.objects.get(key) })),
      truncated: end < keys.length,
      cursor: end < keys.length ? String(end) : undefined,
    };
  }
}

async function toBytes(value) {
  if (typeof value === "string") return new TextEncoder().encode(value);
  if (value instanceof Uint8Array) return value;
  if (value?.getReader) {
    const reader = value.getReader();
    const chunks = [];
    let size = 0;
    while (true) {
      const { done, value: chunk } = await reader.read();
      if (done) break;
      chunks.push(chunk);
      size += chunk.byteLength;
    }
    const result = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.byteLength;
    }
    return result;
  }
  throw new Error("unsupported fake R2 value");
}

function environment({ pageSize } = {}) {
  return { PRIMARY_DOCUMENTS: new FakeBucket({ pageSize }), BACKUP_DOCUMENTS: new FakeBucket() };
}

async function seed(bucket, key, content) {
  await bucket.put(key, content, { httpMetadata: { contentType: "text/plain" } });
  return bucket.head(key);
}

const fixedNow = new Date("2026-08-18T02:15:00.000Z");

test("empty primary succeeds, writes immutable evidence, and advances last-success", async () => {
  const env = environment();
  const result = await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-empty" });
  assert.equal(result.result, "SUCCESS");
  assert.equal(result.primaryObjectsExamined, 0);
  assert.ok(await env.BACKUP_DOCUMENTS.head(result.manifestKey));
  assert.ok(await env.BACKUP_DOCUMENTS.head("_backup_control/last-success.json"));
});

test("copies a new object with source metadata and size reconciliation", async () => {
  const env = environment();
  const source = await seed(env.PRIMARY_DOCUMENTS, "customer/document.pdf", "content-v1");
  const result = await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-new" });
  const key = backupKeyFor(source.key, source.version);
  const backup = await env.BACKUP_DOCUMENTS.head(key);
  assert.equal(result.objectsCopied, 1);
  assert.equal(backup.size, source.size);
  assert.equal(backup.customMetadata.backup_source_key, source.key);
  assert.equal(backup.customMetadata.backup_source_version, source.version);
  assert.equal(backup.customMetadata.backup_source_etag, source.etag);
});

test("skips an already-backed-up exact version", async () => {
  const env = environment();
  await seed(env.PRIMARY_DOCUMENTS, "customer/document.pdf", "content-v1");
  await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-first" });
  const result = await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-second" });
  assert.equal(result.objectsCopied, 0);
  assert.equal(result.objectsSkipped, 1);
});

test("changed source version receives a distinct immutable recovery key", async () => {
  const env = environment();
  const first = await seed(env.PRIMARY_DOCUMENTS, "customer/document.pdf", "content-v1");
  await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-v1" });
  const second = await seed(env.PRIMARY_DOCUMENTS, "customer/document.pdf", "content-v2");
  const result = await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-v2" });
  assert.equal(result.objectsCopied, 1);
  assert.notEqual(backupKeyFor(first.key, first.version), backupKeyFor(second.key, second.version));
  assert.ok(await env.BACKUP_DOCUMENTS.head(backupKeyFor(first.key, first.version)));
  assert.ok(await env.BACKUP_DOCUMENTS.head(backupKeyFor(second.key, second.version)));
});

test("deleting a primary object never deletes its backup", async () => {
  const env = environment();
  const source = await seed(env.PRIMARY_DOCUMENTS, "customer/document.pdf", "content-v1");
  await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-copy" });
  env.PRIMARY_DOCUMENTS.objects.delete(source.key);
  await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-after-source-delete" });
  assert.ok(await env.BACKUP_DOCUMENTS.head(backupKeyFor(source.key, source.version)));
  assert.deepEqual(env.BACKUP_DOCUMENTS.deleteCalls, []);
});

test("processes every R2 list page", async () => {
  const env = environment({ pageSize: 1 });
  await seed(env.PRIMARY_DOCUMENTS, "one.pdf", "1");
  await seed(env.PRIMARY_DOCUMENTS, "two.pdf", "2");
  await seed(env.PRIMARY_DOCUMENTS, "three.pdf", "3");
  const result = await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-pages" });
  assert.equal(result.primaryObjectsExamined, 3);
  assert.equal(result.objectsCopied, 3);
});

test("partial copy failure records FAILED evidence and does not advance last-success", async () => {
  const env = environment();
  await seed(env.PRIMARY_DOCUMENTS, "ok.pdf", "ok");
  await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-prior-success" });
  const priorLastSuccess = await env.BACKUP_DOCUMENTS.get("_backup_control/last-success.json");
  const priorLastSuccessBytes = await toBytes(priorLastSuccess.body);
  const failing = await seed(env.PRIMARY_DOCUMENTS, "failing.pdf", "fail");
  env.BACKUP_DOCUMENTS.failPutFor.add(backupKeyFor(failing.key, failing.version));
  const result = await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-failure" });
  assert.equal(result.result, "FAILED");
  assert.equal(result.failures.length, 1);
  assert.ok(await env.BACKUP_DOCUMENTS.head(result.manifestKey));
  const currentLastSuccess = await env.BACKUP_DOCUMENTS.get("_backup_control/last-success.json");
  assert.deepEqual(await toBytes(currentLastSuccess.body), priorLastSuccessBytes);
  assert.deepEqual(env.PRIMARY_DOCUMENTS.deleteCalls, []);
});

test("a source change during the read is rejected instead of writing it under the stale version", async () => {
  const env = environment();
  const source = await seed(env.PRIMARY_DOCUMENTS, "changed-during-read.pdf", "v1");
  const originalGet = env.PRIMARY_DOCUMENTS.get.bind(env.PRIMARY_DOCUMENTS);
  env.PRIMARY_DOCUMENTS.get = async (key) => {
    const object = await originalGet(key);
    return { ...object, version: `${source.version}-new`, etag: `${source.etag}-new` };
  };
  const result = await runDailyDocumentBackup(env, { now: fixedNow, runId: "run-source-change" });
  assert.equal(result.result, "FAILED");
  assert.equal(await env.BACKUP_DOCUMENTS.head(backupKeyFor(source.key, source.version)), null);
  assert.equal(await env.BACKUP_DOCUMENTS.head("_backup_control/last-success.json"), null);
});

test("backup keys are reversible to the original source key and version", () => {
  const key = backupKeyFor("customer folder/report 2026.pdf", "source-version/with:characters");
  assert.deepEqual(parseBackupKey(key), {
    sourceKey: "customer folder/report 2026.pdf",
    sourceVersion: "source-version/with:characters",
  });
});

test("scheduled handler invokes the backup service against its two isolated bindings", async () => {
  const env = environment();
  await seed(env.PRIMARY_DOCUMENTS, "scheduled.pdf", "scheduled-content");
  await worker.scheduled({ scheduledTime: fixedNow.getTime() }, env);
  const manifests = [...env.BACKUP_DOCUMENTS.objects.keys()].filter((key) => key.startsWith("_backup_runs/"));
  assert.equal(manifests.length, 1);
  assert.ok(await env.BACKUP_DOCUMENTS.head("_backup_control/last-success.json"));
});

test("worker source contains no R2 delete operation or wildcard deletion", async () => {
  const source = await readFile(new URL("../src/index.js", import.meta.url), "utf8");
  assert.equal(source.includes(".delete("), false);
  assert.equal(source.includes("deleteAll"), false);
  assert.equal(source.includes(".arrayBuffer("), false);
  assert.equal(source.includes(".text("), false);
  assert.equal(source.includes(".blob("), false);
});
