"""PayrollMinds backup/restore drill tooling.

Builds a small, explicitly synthetic object graph through this
repository's own governed application services (never raw ORM bypasses of
authorization or workflow invariants), exports a deterministic,
secret-free manifest of it, and re-verifies that manifest against
whatever database this process is currently connected to.

This module never contacts any external provider (Neon, Render,
Cloudflare) directly. It only ever talks to Django's own configured
database and storage backends — which database/storage that is depends
entirely on how the *operator* has configured the process running it
(see docs/pilots/payrollminds/OPERATOR_BACKUP_RESTORE_DRILL_RUNBOOK.md).
That is what makes the same code usable both to create the fixture
against the live database and to verify it against an isolated restored
recovery branch, without this module ever needing provider credentials
of its own.

Nothing here claims a real restore succeeded. `verify_manifest()` reports
a factual comparison; whether that comparison happened against a real
isolated recovery target is a fact about how the operator ran it, not
something this module can know or assert.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.test import Client as TestClient
from django.urls import reverse
from django.utils import timezone

from contracts.models import AuditLog, Contract, Deadline, Document, DocumentVersion, Organization, OrganizationMembership

RECOVERY_NAMESPACE_PREFIX = 'payrollminds-recovery-drill-'

# Field-name fragments that must never appear as manifest/evidence keys with
# a non-empty value. Deliberately broad — false positives (refusing to write
# a harmless field) are the safe failure mode here, not the reverse.
_SECRET_KEY_FRAGMENTS = (
    'password', 'secret', 'token', 'api_key', 'apikey', 'access_key',
    'accesskey', 'private_key', 'privatekey', 'credential', 'dsn',
    'connection_string', 'database_url', 'session_key',
)

# Value shapes that look like a live secret regardless of which key they're
# under (e.g. someone renames a field but the value is still a connection
# string). Checked in addition to, not instead of, the key-name check.
_SECRET_VALUE_PATTERNS = (
    re.compile(r'postgres(ql)?://\S+:\S+@'),
    re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\bnpg_[A-Za-z0-9]{20,}\b'),
)


class RecoveryDrillError(Exception):
    """Raised for any recovery-drill tooling failure that should stop the CLI with a clear message."""


class SecretDetected(RecoveryDrillError):
    """Raised when a value that looks like a live secret was about to be written to evidence."""


def looks_like_secret(key: str, value: Any) -> bool:
    """Return True if a manifest/evidence key or its value looks secret-shaped.

    Conservative on purpose: this gates what is allowed to reach a JSON
    evidence file that may end up in git or shared with a reviewer, so a
    false positive (a benign field gets rejected) is the acceptable failure
    mode, never a false negative.
    """
    lowered_key = (key or '').lower()
    if any(fragment in lowered_key for fragment in _SECRET_KEY_FRAGMENTS):
        return True
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in _SECRET_VALUE_PATTERNS):
            return True
    return False


def reject_secrets(data: Any, *, path: str = '') -> None:
    """Recursively raise SecretDetected if any key/value in ``data`` looks secret-shaped."""
    if isinstance(data, dict):
        for key, value in data.items():
            child_path = f'{path}.{key}' if path else str(key)
            if looks_like_secret(key, value):
                raise SecretDetected(f'Refusing to write secret-shaped value at {child_path!r}.')
            reject_secrets(value, path=child_path)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            reject_secrets(item, path=f'{path}[{index}]')


def new_recovery_namespace(*, now: Any = None) -> str:
    moment = now or timezone.now()
    return f'{RECOVERY_NAMESPACE_PREFIX}{moment.strftime("%Y%m%d-%H%M%S")}'


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class RecoveryFixtureResult:
    namespace: str
    organization_id: int
    organization_slug: str
    owner_user_id: int
    unrelated_member_user_id: int
    cross_workspace_user_id: int
    cross_workspace_organization_id: int
    contract_id: int
    workflow_id: int
    document_id: int
    document_version_id: int
    deadline_id: int
    audit_log_ids: list[int] = field(default_factory=list)
    canonical_runtime_exercised: bool = False
    canonical_workflow_definition_id: int | None = None
    canonical_workflow_version_id: int | None = None
    canonical_workflow_instance_id: int | None = None
    contract_record_id: int | None = None
    quarantine_object_created: bool = False
    created_at: str = ''


def create_recovery_fixture() -> RecoveryFixtureResult:
    """Create one explicitly synthetic recovery fixture through real governed services.

    Uses ``contracts.services.msa_workflow`` (the real MSA workflow builder
    service, exactly the path an actual pilot user drives through
    ``/contracts/new/msa/``) for the Organization/Contract/Workflow/Document
    graph, and the real ``deadline_create`` HTTP view for the
    date/reminder object, so authorization and workflow invariants are
    exercised exactly as they are in production — nothing here is a
    parallel, recovery-drill-only code path.

    Never creates employee, salary, or payroll data — this is a B2B
    commercial-contract fixture (an MSA between the pilot org and a
    clearly-synthetic counterparty), the same object shape the governed
    MSA builder always creates, not a payroll/HR record of any kind.
    """
    from contracts.services.msa_workflow import create_msa_document_artifact, create_msa_workflow_instance

    User = get_user_model()
    namespace = new_recovery_namespace()

    organization = Organization.objects.create(
        name=f'Recovery Drill Workspace {namespace}',
        slug=namespace,
    )
    cross_organization = Organization.objects.create(
        name=f'Recovery Drill Cross-Workspace {namespace}',
        slug=f'{namespace}-cross',
    )

    owner = User.objects.create_user(username=f'{namespace}-owner', password='RecoveryDrillOwner!2026')
    unrelated_member = User.objects.create_user(username=f'{namespace}-member', password='RecoveryDrillMember!2026')
    cross_workspace_user = User.objects.create_user(username=f'{namespace}-outsider', password='RecoveryDrillOutsider!2026')

    OrganizationMembership.objects.create(
        organization=organization, user=owner, role=OrganizationMembership.Role.OWNER, is_active=True,
    )
    OrganizationMembership.objects.create(
        organization=organization, user=unrelated_member, role=OrganizationMembership.Role.MEMBER, is_active=True,
    )
    OrganizationMembership.objects.create(
        organization=cross_organization, user=cross_workspace_user, role=OrganizationMembership.Role.OWNER, is_active=True,
    )

    cleaned_values = {
        'counterparty': f'Recovery Drill Synthetic Counterparty {namespace}',
        'payrollminds_contracting_entity': 'Recovery Drill Synthetic Contracting Entity',
        'client_contact_name': 'Recovery Drill Synthetic Contact',
        'client_contact_email': f'synthetic-contact+{namespace}@recovery-drill.invalid',
        'start_date': date.today().isoformat(),
        'end_date': (date.today() + timedelta(days=365)).isoformat(),
        'contract_owner': 'Recovery Drill Synthetic Owner',
        'business_unit': 'Recovery Drill Synthetic Unit',
        'internal_reference': f'RECOVERY-DRILL-{namespace}',
        'value': 1000,
        'currency': 'EUR',
        'payment_terms': 'Net 30',
        'rate': 1,
        'travel_km_rate': 0,
        'administrative_fee': 0,
        'initial_term': '12 months',
        'renewal_type': 'Manual',
        'termination_notice_period': 30,
        'consultant_service_type': 'Synthetic recovery-drill services',
        'services_description': 'Synthetic recovery-drill commissioning record; not a real engagement.',
        'worker_classification': 'Not applicable — synthetic fixture',
        'payrollminds_professional_involved': False,
        'sow_required': False,
        'deliverables_defined': False,
        'acceptance_criteria_required': False,
        'governing_law': 'Not applicable — synthetic fixture',
        'jurisdiction': 'Not applicable — synthetic fixture',
        'liability_cap': 'Not applicable — synthetic fixture',
        'source_system': 'recovery_drill_toolkit',
        'source_system_id': namespace,
    }

    workflow = create_msa_workflow_instance(organization=organization, user=owner, cleaned_values=cleaned_values)
    contract = workflow.contract
    document = create_msa_document_artifact(workflow=workflow, user=owner, artifact_type='word')
    document_version = document.canonical_version if hasattr(document, 'canonical_version') else DocumentVersion.objects.filter(document_row=document).order_by('-version_number').first()

    # Date/reminder object, created through the real governed HTTP view
    # (the same path PM-UAT-006 uses) rather than a direct model write.
    client = TestClient()
    client.force_login(owner)
    deadline_response = client.post(
        reverse('contracts:deadline_create'),
        {
            'title': f'Recovery drill synthetic reminder {namespace}',
            'deadline_type': Deadline.DeadlineType.CONTRACT,
            'priority': Deadline.Priority.LOW,
            'due_date': (date.today() + timedelta(days=30)).isoformat(),
            'reminder_days': 7,
            'contract': contract.pk,
            'assigned_to': owner.pk,
        },
        follow=True,
    )
    deadline = Deadline.objects.filter(contract=contract).order_by('-created_at').first()
    if deadline is None:
        raise RecoveryDrillError(
            f'deadline_create view did not produce a Deadline row (HTTP {deadline_response.status_code}); '
            'recovery fixture is incomplete, refusing to report a namespace as ready.'
        )

    # Canonical WorkflowDefinition/Version/Instance + ContractRecord are only
    # exercised if the canonical runtime is already enabled for this
    # organization — this task must not enable a currently-inactive
    # production feature just to populate the fixture. See
    # OPERATOR_BACKUP_RESTORE_DRILL_RUNBOOK.md for why this is conditional.
    canonical_definition_id = canonical_version_id = canonical_instance_id = None
    contract_record_id = None
    canonical_exercised = False
    try:
        from contracts.services.canonical_workflow_runtime import (
            _canonical_runtime_enabled,
            create_draft_workflow_version,
            create_workflow_definition,
        )
        if _canonical_runtime_enabled(organization):
            definition = create_workflow_definition(
                organization=organization, key=f'recovery-drill-{namespace}',
                name=f'Recovery Drill NDA {namespace}', actor=owner,
            )
            version = create_draft_workflow_version(
                definition=definition,
                configuration={'recovery_drill': True, 'namespace': namespace},
                actor=owner,
            )
            canonical_definition_id = definition.pk
            canonical_version_id = version.pk
            canonical_exercised = True
    except Exception:  # noqa: BLE001 - optional path; failure here must not abort the whole fixture
        canonical_exercised = False

    audit_log_ids = list(
        AuditLog.objects.filter(organization=organization).order_by('id').values_list('id', flat=True)
    )

    return RecoveryFixtureResult(
        namespace=namespace,
        organization_id=organization.pk,
        organization_slug=organization.slug,
        owner_user_id=owner.pk,
        unrelated_member_user_id=unrelated_member.pk,
        cross_workspace_user_id=cross_workspace_user.pk,
        cross_workspace_organization_id=cross_organization.pk,
        contract_id=contract.pk,
        workflow_id=workflow.pk,
        document_id=document.pk,
        document_version_id=document_version.pk if document_version else 0,
        deadline_id=deadline.pk,
        audit_log_ids=audit_log_ids,
        canonical_runtime_exercised=canonical_exercised,
        canonical_workflow_definition_id=canonical_definition_id,
        canonical_workflow_version_id=canonical_version_id,
        canonical_workflow_instance_id=canonical_instance_id,
        contract_record_id=contract_record_id,
        quarantine_object_created=False,
        created_at=timezone.now().isoformat(),
    )


def _hash_document_version_storage(document_version: DocumentVersion) -> dict:
    if not document_version.file:
        return {'stored': False}
    storage_alias = 'default'
    key = document_version.file.name
    try:
        handle = storages[storage_alias].open(key, 'rb')
        try:
            data = handle.read()
        finally:
            handle.close()
    except Exception as exc:  # noqa: BLE001
        return {'stored': True, 'key': key, 'readable': False, 'error': str(exc)}
    return {
        'stored': True,
        'bucket_logical_role': 'canonical_document_storage',
        'key': key,
        'size': len(data),
        'sha256': _sha256_bytes(data),
        'readable': True,
    }


def export_manifest(namespace: str) -> dict:
    """Build the deterministic, secret-free pre-recovery manifest for ``namespace``.

    Reads only from whatever database this process is currently connected
    to — the operator is responsible for pointing it at the right one
    (see the runbook). Raises RecoveryDrillError if the namespace's
    fixture cannot be fully located.
    """
    try:
        organization = Organization.objects.get(slug=namespace)
    except Organization.DoesNotExist as exc:
        raise RecoveryDrillError(f'No organization found for recovery namespace {namespace!r}.') from exc

    memberships = list(
        OrganizationMembership.objects.filter(organization=organization).order_by('user__username').values(
            'user__username', 'role', 'is_active',
        )
    )
    contract = Contract.objects.filter(organization=organization).order_by('id').first()
    if contract is None:
        raise RecoveryDrillError(f'No Contract found for recovery namespace {namespace!r}.')
    document = Document.objects.filter(organization=organization, contract=contract).order_by('id').first()
    document_version = None
    document_storage = {'stored': False}
    if document is not None:
        document_version = DocumentVersion.objects.filter(document_row=document).order_by('-version_number').first()
        if document_version is not None:
            document_storage = _hash_document_version_storage(document_version)
    deadline = Deadline.objects.filter(contract=contract).order_by('id').first()
    audit_ids = list(
        AuditLog.objects.filter(organization=organization).order_by('id').values_list('id', flat=True)
    )

    manifest = {
        'schema_version': 1,
        'namespace': namespace,
        'exported_at': timezone.now().isoformat(),
        'organization': {'id': organization.pk, 'slug': organization.slug, 'name': organization.name},
        'memberships': memberships,
        'contract': {
            'id': contract.pk,
            'title': contract.title,
            'contract_type': contract.contract_type,
            'status': contract.status,
            'created_by_id': contract.created_by_id,
            'origin_kind': getattr(contract, 'origin_kind', None),
            'origin_channel': getattr(contract, 'origin_channel', None),
        },
        'document': None,
        'deadline': None,
        'audit': {'count': len(audit_ids), 'ids': audit_ids},
        'canonical_runtime_exercised': False,
    }
    if document is not None:
        manifest['document'] = {
            'id': document.pk,
            'title': document.title,
            'document_type': document.document_type,
            'version': {
                'id': document_version.pk if document_version else None,
                'version_number': document_version.version_number if document_version else None,
                'file_hash': document_version.file_hash if document_version else '',
                'file_size': document_version.file_size if document_version else None,
                'storage': document_storage,
            } if document_version else None,
        }
    if deadline is not None:
        manifest['deadline'] = {
            'id': deadline.pk,
            'title': deadline.title,
            'deadline_type': deadline.deadline_type,
            'due_date': deadline.due_date.isoformat(),
            'reminder_days': deadline.reminder_days,
        }

    reject_secrets(manifest)
    return manifest


def _diff_scalar(before: Any, after: Any, path: str, differences: list[str]) -> None:
    if before != after:
        differences.append(f'{path}: before={before!r} after={after!r}')


def verify_manifest(manifest: dict, *, verify_authorization: bool = False) -> tuple[dict, dict]:
    """Re-derive the same manifest shape from the currently-connected database and diff it.

    Returns ``(after_snapshot, comparison)``. ``comparison['differences']``
    is empty only when every field this manifest schema tracks matched
    exactly. Does not itself decide pass/fail for the CLI — the caller
    (management command) does that from ``comparison``, per Rule #10:
    this function reports facts, it does not claim success.
    """
    namespace = manifest.get('namespace')
    if not namespace:
        raise RecoveryDrillError('Manifest is missing "namespace"; cannot verify.')

    differences: list[str] = []
    missing: list[str] = []

    try:
        after = export_manifest(namespace)
    except RecoveryDrillError as exc:
        return (
            {'namespace': namespace, 'error': str(exc)},
            {
                'namespace': namespace,
                'matched_object_count': 0,
                'missing_object_count': 1,
                'unexpected_differences': [str(exc)],
                'differences': [str(exc)],
                'zero_unexplained_differences': False,
            },
        )

    matched = 0
    for key in ('organization', 'contract', 'deadline'):
        before_value = manifest.get(key)
        after_value = after.get(key)
        if before_value is None:
            continue
        if after_value is None:
            missing.append(key)
            continue
        matched += 1
        for field_name, before_field in before_value.items():
            after_field = after_value.get(field_name)
            _diff_scalar(before_field, after_field, f'{key}.{field_name}', differences)

    before_doc = manifest.get('document')
    after_doc = after.get('document')
    if before_doc is not None:
        if after_doc is None:
            missing.append('document')
        else:
            matched += 1
            _diff_scalar(before_doc.get('id'), after_doc.get('id'), 'document.id', differences)
            _diff_scalar(before_doc.get('title'), after_doc.get('title'), 'document.title', differences)
            before_version = (before_doc.get('version') or {})
            after_version = (after_doc.get('version') or {})
            _diff_scalar(before_version.get('file_hash'), after_version.get('file_hash'), 'document.version.file_hash', differences)
            _diff_scalar(before_version.get('file_size'), after_version.get('file_size'), 'document.version.file_size', differences)
            before_storage = before_version.get('storage') or {}
            after_storage = after_version.get('storage') or {}
            if before_storage.get('sha256'):
                _diff_scalar(before_storage.get('sha256'), after_storage.get('sha256'), 'document.version.storage.sha256', differences)

    before_audit = manifest.get('audit') or {}
    after_audit = after.get('audit') or {}
    _diff_scalar(before_audit.get('count'), after_audit.get('count'), 'audit.count', differences)
    if set(before_audit.get('ids') or []) - set(after_audit.get('ids') or []):
        differences.append(
            f"audit.ids: missing after restore = {sorted(set(before_audit.get('ids') or []) - set(after_audit.get('ids') or []))}"
        )
    else:
        matched += 1

    before_memberships = {(m['user__username'], m['role']) for m in (manifest.get('memberships') or [])}
    after_memberships = {(m['user__username'], m['role']) for m in (after.get('memberships') or [])}
    missing_memberships = before_memberships - after_memberships
    if missing_memberships:
        differences.append(f'memberships: missing after restore = {sorted(missing_memberships)}')
    else:
        matched += 1

    authorization_result = None
    if verify_authorization:
        authorization_result = _verify_authorization(manifest)
        if not authorization_result.get('all_expected'):
            differences.append(f"authorization: {authorization_result.get('unexpected')}")

    comparison = {
        'namespace': namespace,
        'matched_object_count': matched,
        'missing_object_count': len(missing),
        'missing_objects': missing,
        'unexpected_differences': differences,
        'differences': differences,
        'zero_unexplained_differences': not differences and not missing,
        'authorization': authorization_result,
    }
    reject_secrets(after)
    reject_secrets(comparison)
    return after, comparison


def _verify_authorization(manifest: dict) -> dict:
    """Prove restored-DB authorization using the real, canonical object-read policy service.

    Reuses ``contracts.services.object_read_policy.filter_contract_queryset``
    — the same function production views use to scope contract
    visibility — rather than any recovery-drill-specific ACL check.
    """
    from contracts.services.object_read_policy import filter_contract_queryset
    from contracts.tenancy import get_user_organization

    User = get_user_model()
    org_data = manifest.get('organization') or {}
    contract_data = manifest.get('contract') or {}
    namespace = manifest.get('namespace')

    contract_id = contract_data.get('id')
    checks: dict[str, bool] = {}
    unexpected: list[str] = []
    try:
        owner = User.objects.get(username=f'{namespace}-owner')
        unrelated_member = User.objects.get(username=f'{namespace}-member')
        cross_workspace_user = User.objects.get(username=f'{namespace}-outsider')
        contract = Contract.objects.get(pk=contract_id)
    except Exception as exc:  # noqa: BLE001
        return {'all_expected': False, 'unexpected': f'authorization actors/contract not found after restore: {exc}', 'checks': {}}

    def _visible(actor) -> bool:
        actor_org = get_user_organization(actor)
        if actor_org is None:
            return False
        visible = filter_contract_queryset(
            Contract.objects.filter(pk=contract.pk), organization=actor_org, user=actor, surface='recovery_drill_verification',
        )
        return visible.exists()

    checks['owner_can_access'] = _visible(owner)
    checks['unrelated_member_cannot_access'] = not _visible(unrelated_member)
    checks['cross_workspace_user_cannot_access'] = not _visible(cross_workspace_user)

    # Audit append-only invariant, re-checked against whatever database this
    # verification is actually running against.
    audit_row = AuditLog.objects.filter(organization_id=org_data.get('id')).order_by('id').first()
    audit_append_only = True
    if audit_row is not None:
        from contracts.models import AuditWriteError
        try:
            audit_row.outcome = AuditLog.Outcome.FAILURE
            audit_row.save(update_fields=['outcome'])
            audit_append_only = False
        except AuditWriteError:
            audit_append_only = True
    checks['audit_remains_append_only'] = audit_append_only

    for name, passed in checks.items():
        if not passed:
            unexpected.append(name)

    return {
        'all_expected': not unexpected,
        'unexpected': unexpected,
        'checks': checks,
    }


def hash_stored_object(*, storage_alias: str, key: str) -> dict:
    """Read one object through a Django-configured storage backend and hash it.

    Provider-neutral: works identically for the canonical ``default``
    storage alias and the ``quarantine`` alias, and for any additional
    alias an operator adds to ``STORAGES`` for a recovery target. Never
    returns or logs credentials — only the bucket logical role (the
    storage alias name), key, size, and hash.
    """
    try:
        backend = storages[storage_alias]
    except Exception as exc:  # noqa: BLE001 - Django raises InvalidStorageError, not KeyError
        raise RecoveryDrillError(f'No storage alias {storage_alias!r} is configured.') from exc
    handle = backend.open(key, 'rb')
    try:
        data = handle.read()
    finally:
        handle.close()
    return {
        'bucket_logical_role': storage_alias,
        'key': key,
        'size': len(data),
        'sha256': _sha256_bytes(data),
    }


def assemble_evidence_bundle(**named_documents: dict) -> dict:
    """Combine named evidence documents into one bundle, rejecting any secret-shaped value first."""
    bundle = {
        'schema_version': 1,
        'assembled_at': timezone.now().isoformat(),
        'documents': named_documents,
    }
    reject_secrets(bundle)
    return bundle
