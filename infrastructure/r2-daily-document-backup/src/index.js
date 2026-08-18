const BACKUP_VERSION_PREFIX = "_backup_versions/v1/";
const RUN_EVIDENCE_PREFIX = "_backup_runs/";
const CONTROL_PREFIX = "_backup_control/";
const LAST_SUCCESS_KEY = `${CONTROL_PREFIX}last-success.json`;
const RESERVED_PRIMARY_PREFIXES = [
  BACKUP_VERSION_PREFIX,
  RUN_EVIDENCE_PREFIX,
  CONTROL_PREFIX,
];
const MAX_ATTEMPTS = 2;

function base64UrlEncode(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function base64UrlDecode(value) {
  const padded = value.replaceAll("-", "+").replaceAll("_", "/") + "=".repeat((4 - (value.length % 4)) % 4);
  const binary = atob(padded);
  return new TextDecoder().decode(Uint8Array.from(binary, (character) => character.charCodeAt(0)));
}

export function backupKeyFor(sourceKey, sourceVersion) {
  return `${BACKUP_VERSION_PREFIX}${base64UrlEncode(sourceKey)}/${base64UrlEncode(sourceVersion)}`;
}

export function parseBackupKey(backupKey) {
  if (!backupKey.startsWith(BACKUP_VERSION_PREFIX)) return null;
  const encodedParts = backupKey.slice(BACKUP_VERSION_PREFIX.length).split("/");
  if (encodedParts.length !== 2 || !encodedParts[0] || !encodedParts[1]) return null;
  return {
    sourceKey: base64UrlDecode(encodedParts[0]),
    sourceVersion: base64UrlDecode(encodedParts[1]),
  };
}

function isReservedSourceKey(key) {
  return RESERVED_PRIMARY_PREFIXES.some((prefix) => key.startsWith(prefix));
}

function sourceVersionFor(source) {
  const version = typeof source.version === "string" ? source.version.trim() : "";
  if (version) return version;
  const etag = typeof source.etag === "string" ? source.etag.trim() : "";
  if (etag) return `etag:${etag}`;
  throw new Error(`R2 object ${source.key} has neither a source version nor an ETag`);
}

function iso(value) {
  return value instanceof Date ? value.toISOString() : new Date(value).toISOString();
}

async function sha256Identifier(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return `sha256:${Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("").slice(0, 24)}`;
}

function safeFailure(error) {
  return error instanceof Error && error.name ? `${error.name}: backup operation failed` : "backup operation failed";
}

async function retry(operation) {
  let lastError;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      if (attempt === MAX_ATTEMPTS) throw error;
    }
  }
  throw lastError;
}

function backupMetadata(source, sourceVersion, backedUpAt) {
  return {
    backup_source_key: source.key,
    backup_source_version: sourceVersion,
    backup_source_etag: source.etag || "",
    backup_source_size: String(source.size),
    backup_source_uploaded_at: source.uploaded ? iso(source.uploaded) : "",
    backup_copied_at: backedUpAt,
  };
}

function metadataMatches(backedUpObject, source, sourceVersion) {
  const metadata = backedUpObject?.customMetadata || {};
  return backedUpObject?.size === source.size
    && metadata.backup_source_key === source.key
    && metadata.backup_source_version === sourceVersion
    && metadata.backup_source_etag === (source.etag || "")
    && metadata.backup_source_size === String(source.size);
}

async function copySourceObject(env, source, startedAt) {
  const sourceVersion = sourceVersionFor(source);
  const key = backupKeyFor(source.key, sourceVersion);
  const existing = await retry(() => env.BACKUP_DOCUMENTS.head(key));
  if (existing) {
    if (!metadataMatches(existing, source, sourceVersion)) {
      throw new Error("immutable backup metadata mismatch");
    }
    return { outcome: "skipped", bytes: 0, backupKey: key };
  }

  const primaryBody = await retry(() => env.PRIMARY_DOCUMENTS.get(source.key));
  if (!primaryBody?.body) throw new Error("primary object unavailable during backup");
  if (sourceVersionFor(primaryBody) !== sourceVersion || primaryBody.etag !== source.etag) {
    throw new Error("primary object changed while the backup copy was being read");
  }

  const copiedAt = iso(startedAt);
  await retry(() => env.BACKUP_DOCUMENTS.put(key, primaryBody.body, {
    httpMetadata: primaryBody.httpMetadata,
    customMetadata: backupMetadata(source, sourceVersion, copiedAt),
  }));

  const backedUpObject = await retry(() => env.BACKUP_DOCUMENTS.head(key));
  if (!metadataMatches(backedUpObject, source, sourceVersion)) {
    throw new Error("backup metadata or size reconciliation failed");
  }
  return { outcome: "copied", bytes: source.size, backupKey: key };
}

async function putJson(bucket, key, value) {
  await retry(() => bucket.put(key, JSON.stringify(value), {
    httpMetadata: { contentType: "application/json; charset=utf-8" },
  }));
}

export async function runDailyDocumentBackup(env, { now = new Date(), runId = crypto.randomUUID() } = {}) {
  const startedAt = iso(now);
  const summary = {
    runId,
    scheduledAt: startedAt,
    startedAt,
    finishedAt: null,
    primaryObjectsExamined: 0,
    objectsCopied: 0,
    objectsSkipped: 0,
    bytesCopied: 0,
    failures: [],
    result: "FAILED",
  };

  let cursor;
  let listingFailed = false;
  do {
    let page;
    try {
      page = await retry(() => env.PRIMARY_DOCUMENTS.list({ cursor }));
    } catch (error) {
      summary.failures.push({
        object: "primary-listing",
        stage: "list",
        error: safeFailure(error),
      });
      listingFailed = true;
      break;
    }
    for (const source of page.objects) {
      if (isReservedSourceKey(source.key)) continue;
      summary.primaryObjectsExamined += 1;
      try {
        const copy = await copySourceObject(env, source, now);
        if (copy.outcome === "copied") {
          summary.objectsCopied += 1;
          summary.bytesCopied += copy.bytes;
        } else {
          summary.objectsSkipped += 1;
        }
      } catch (error) {
        summary.failures.push({
          object: await sha256Identifier(source.key),
          stage: "copy-or-reconcile",
          error: safeFailure(error),
        });
      }
    }
    cursor = page.truncated ? page.cursor : undefined;
  } while (cursor && !listingFailed);

  summary.finishedAt = iso(new Date());
  summary.result = summary.failures.length === 0 ? "SUCCESS" : "FAILED";
  const manifestKey = `${RUN_EVIDENCE_PREFIX}${summary.finishedAt.replaceAll(":", "-")}-${runId}.json`;
  summary.manifestKey = manifestKey;
  await putJson(env.BACKUP_DOCUMENTS, manifestKey, summary);

  if (summary.result === "SUCCESS") {
    await putJson(env.BACKUP_DOCUMENTS, LAST_SUCCESS_KEY, {
      runId: summary.runId,
      completedAt: summary.finishedAt,
      manifestKey,
      primaryObjectsExamined: summary.primaryObjectsExamined,
      objectsCopied: summary.objectsCopied,
      objectsSkipped: summary.objectsSkipped,
      bytesCopied: summary.bytesCopied,
    });
  }
  return summary;
}

export default {
  async scheduled(controller, env) {
    await runDailyDocumentBackup(env, { now: new Date(controller.scheduledTime) });
  },
};
