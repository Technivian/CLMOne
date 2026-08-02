# PayrollMinds Pilot Data Classification

**Status:** Proposed
**Purpose:** Apply purpose limitation and data minimisation to the narrow pilot without creating a new canonical classification taxonomy.

## Handling rules

This record uses the existing confidentiality, field-sensitivity, access,
retention and audit requirements. It does not create new data objects or
override an approved workspace retention policy. A classification that cannot
be applied or a data class not listed below must be treated as prohibited until
Product, Privacy and Security approve a change.

| Data category | Pilot disposition | Permitted handling | Prohibited handling |
|---|---|---|---|
| Contract document and amendments for an approved type | Allowed — confidential/restricted according to contract policy | Private quarantine; clean release; authorized human review; private storage; access-controlled search; audit. | Public links, external sharing, provider AI, unlogged export. |
| Contract metadata: parties, title, type, status, dates, owner, notice period, governing law and approved commercial terms | Allowed — minimum necessary | Human entry/verification; authorized search/filtering; reminders; audit. | AI provider context, raw query telemetry, unauthorized export. |
| Provenance, verification, reminder and content-minimized audit metadata | Allowed — protected operational evidence | Authorized administration and audit; retention under approved policy. | Document text, prompts, filenames/titles where unnecessary, credentials or secrets in logs. |
| Contact details embedded in an agreement | Conditional — incidental only | Process only when necessary to operate the agreement record and protected by object access. | Separate contact enrichment, marketing, directory creation or bulk export. |
| Raw payroll, payslips, salary/compensation, bank, tax, benefits or pension data | Prohibited | None; reject/quarantine and follow incident procedure. | Storage, OCR, search, AI, export or manual workaround. |
| Employee/worker bulk records, HRIS extracts, identity documents, credentials or authentication material | Prohibited | None; reject/quarantine and follow incident procedure. | Storage, processing, support attachment or transfer. |
| Special-category data, criminal-offence data, biometric data or data outside an agreement purpose | Prohibited | None without separately approved lawful basis, scope and controls. | Ingestion, processing, AI, export or sharing. |
| AI prompts, embeddings and provider outputs | Prohibited during this pilot | None; AI remains disabled. | Any provider call, model training, prompt logging or autonomous update. |

## Collection and use controls

- Collect only through approved manual/bulk ingestion after a clean malware and
  type-validation verdict. Do not use email forwarding.
- Re-evaluate server-side object access before document read, metadata display,
  search result, count/facet, reminder, audit view and export.
- Do not place raw document text, search terms, prompt text, credentials or
  customer identifiers in logs, monitoring, test fixtures or support tickets.
- Export is exceptional: it must be authorized, auditable, purpose-bound and
  protected from accidental disclosure.

## Retention and deletion precondition

Real data may not be accepted until the responsible owner records the approved
retention period, legal basis, legal-hold precedence, deletion method, export
method, offboarding sequence, data location and subprocessor position. This
package intentionally makes no claim that those customer terms exist.

## Incident response

Prohibited or misclassified data, a suspected leak, or a failed scanner verdict
requires immediate stop under the Pilot Charter. Preserve only the evidence
needed for security/privacy response; do not re-upload, email, copy or
manually inspect the material outside the approved incident process.
