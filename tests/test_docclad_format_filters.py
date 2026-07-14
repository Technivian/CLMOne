"""Sub-block C: shared formatting helpers (contracts/templatetags/docclad_format.py)."""
from django.test import SimpleTestCase

from contracts.templatetags.docclad_format import (
    contract_risk_badge_tone,
    contract_status_badge_tone,
    dpa_approval_badge_tone,
    dpa_severity_badge_tone,
    event_label,
    humanduration,
    iso_datetime,
    money,
    object_type_label,
    risk_status_badge_tone,
    signature_status_badge_tone,
    sort_label,
    task_status_badge_tone,
)


class MoneyFilterTests(SimpleTestCase):
    def test_formats_integer_with_thousands_separator(self):
        self.assertEqual(money(125000), '$125,000.00')

    def test_formats_string_decimal(self):
        self.assertEqual(money('125000.5'), '$125,000.50')

    def test_respects_currency_code(self):
        self.assertEqual(money(50, 'EUR'), '€50.00')
        self.assertEqual(money(50, 'GBP'), '£50.00')

    def test_unknown_currency_falls_back_to_code_prefix(self):
        self.assertEqual(money(50, 'JPY'), 'JPY 50.00')

    def test_empty_value_renders_em_dash(self):
        self.assertEqual(money(None), '—')
        self.assertEqual(money(''), '—')

    def test_unparsable_value_passes_through(self):
        self.assertEqual(money('not-a-number'), 'not-a-number')


class IsoDatetimeFilterTests(SimpleTestCase):
    def test_parses_iso_string_with_microseconds_and_offset(self):
        result = iso_datetime('2026-06-01T09:15:38.135815+00:00')
        self.assertNotIn('T', result)
        self.assertNotIn('+00:00', result)
        self.assertIn('2026', result)

    def test_parses_bare_date_string(self):
        result = iso_datetime('2026-06-11', fmt='M d, Y')
        self.assertEqual(result, 'Jun 11, 2026')

    def test_empty_value_renders_empty_string(self):
        self.assertEqual(iso_datetime(''), '')
        self.assertEqual(iso_datetime(None), '')

    def test_unparsable_string_passes_through(self):
        self.assertEqual(iso_datetime('not-a-date'), 'not-a-date')


class ObjectTypeLabelFilterTests(SimpleTestCase):
    def test_known_model_names_use_curated_labels(self):
        self.assertEqual(object_type_label('OrganizationMembership'), 'team membership')
        self.assertEqual(object_type_label('ContractAI'), 'AI review')
        self.assertEqual(object_type_label('DSARRequest'), 'data subject request')

    def test_unmapped_pascal_case_falls_back_to_word_split(self):
        self.assertEqual(object_type_label('SomeFutureModel'), 'some future model')

    def test_empty_value(self):
        self.assertEqual(object_type_label(''), '')
        self.assertEqual(object_type_label(None), '')


class EventLabelFilterTests(SimpleTestCase):
    def test_snake_case_event(self):
        self.assertEqual(event_label('contract_ai_assistant_invoked'), 'Contract AI Assistant Invoked')

    def test_dot_notation_event(self):
        self.assertEqual(event_label('approval.delegated'), 'Approval Delegated')

    def test_acronyms_are_uppercased(self):
        self.assertEqual(event_label('mfa_recovery_codes_generated'), 'MFA Recovery Codes Generated')
        self.assertEqual(event_label('scim_user_provisioned'), 'SCIM User Provisioned')

    def test_empty_value(self):
        self.assertEqual(event_label(''), '')
        self.assertEqual(event_label(None), '')


class SortLabelFilterTests(SimpleTestCase):
    def test_descending_field(self):
        self.assertEqual(sort_label('-created_at'), 'Created at ↓')

    def test_ascending_field(self):
        self.assertEqual(sort_label('value'), 'Value ↑')

    def test_no_raw_dash_or_underscore_leaks_through(self):
        result = sort_label('-created_at')
        self.assertNotIn('-created_at', result)
        self.assertNotIn('_', result)

    def test_empty_value(self):
        self.assertEqual(sort_label(''), '')
        self.assertEqual(sort_label(None), '')


class HumanDurationFilterTests(SimpleTestCase):
    def test_seconds_only(self):
        self.assertEqual(humanduration(45), '45s')

    def test_minutes(self):
        self.assertEqual(humanduration(125), '2m')

    def test_hours_and_minutes(self):
        self.assertEqual(humanduration(3725), '1h 2m')

    def test_hours_exact(self):
        self.assertEqual(humanduration(7200), '2h')

    def test_days_and_hours_matches_audit_finding(self):
        # The audit found "Heartbeat: 787296s" on the operations dashboard.
        self.assertEqual(humanduration(787296), '9d 2h')

    def test_non_numeric_passes_through(self):
        self.assertEqual(humanduration('unknown'), 'unknown')


class DPABadgeToneFilterTests(SimpleTestCase):
    """Direct coverage for the design-system Phase 4 tone filters added
    alongside the DPA Reviews migration — every persisted enum value must
    map to a real tone, since an unmapped value silently rendering neutral
    is a defect (see DESIGN_CONSTITUTION.md's badge-mapping rule), not an
    acceptable fallback."""

    def test_every_dpa_review_pack_approval_status_maps_to_a_tone(self):
        from contracts.models import DPAReviewPack

        expected = {
            'DRAFT': 'neutral',
            'UNDER_REVIEW': 'progress',
            'ESCALATED': 'special',
            'APPROVED': 'success',
            'REJECTED': 'danger',
        }
        choices = {value for value, _ in DPAReviewPack.ApprovalStatus.choices}
        self.assertEqual(choices, set(expected.keys()))
        for status, tone in expected.items():
            self.assertEqual(dpa_approval_badge_tone(status), tone)

    def test_every_dpa_risk_item_severity_maps_to_a_tone(self):
        from contracts.models import DPARiskItem

        expected = {
            'CRITICAL': 'danger',
            'HIGH': 'danger',
            'MEDIUM': 'attention',
            'LOW': 'success',
        }
        choices = {value for value, _ in DPARiskItem.Severity.choices}
        self.assertEqual(choices, set(expected.keys()))
        for severity, tone in expected.items():
            self.assertEqual(dpa_severity_badge_tone(severity), tone)

    def test_unknown_value_falls_back_to_neutral_not_a_crash(self):
        self.assertEqual(dpa_approval_badge_tone('NOT_A_REAL_STATUS'), 'neutral')
        self.assertEqual(dpa_severity_badge_tone('NOT_A_REAL_SEVERITY'), 'neutral')


class ContractDetailBadgeToneFilterTests(SimpleTestCase):
    """Direct coverage for the tone filters added alongside the Contract
    Detail migration — every persisted enum value must map to a real tone,
    mirroring DPABadgeToneFilterTests above (DESIGN_CONSTITUTION.md's
    badge-mapping rule: an unmapped value silently rendering neutral is a
    defect, not an acceptable fallback)."""

    def test_every_contract_status_maps_to_a_tone(self):
        from contracts.models import Contract

        expected = {
            'DRAFT': 'neutral',
            'PENDING': 'attention',
            'IN_REVIEW': 'progress',
            'APPROVED': 'progress',
            'ACTIVE': 'success',
            'COMPLETED': 'success',
            'EXPIRED': 'danger',
            'TERMINATED': 'danger',
            'CANCELLED': 'neutral',
        }
        choices = {value for value, _ in Contract.Status.choices}
        self.assertEqual(choices, set(expected.keys()))
        for status, tone in expected.items():
            self.assertEqual(contract_status_badge_tone(status), tone)

    def test_every_contract_risk_level_maps_to_a_tone(self):
        from contracts.models import Contract, RiskLog

        expected = {
            'LOW': 'success',
            'MEDIUM': 'attention',
            'HIGH': 'danger',
            'CRITICAL': 'danger',
        }
        contract_choices = {value for value, _ in Contract.RiskLevel.choices}
        risk_log_choices = {value for value, _ in RiskLog.RiskLevel.choices}
        self.assertEqual(contract_choices, set(expected.keys()))
        self.assertEqual(risk_log_choices, set(expected.keys()))
        for risk_level, tone in expected.items():
            self.assertEqual(contract_risk_badge_tone(risk_level), tone)

    def test_every_legal_task_status_maps_to_a_tone(self):
        from contracts.models import LegalTask

        expected = {
            'PENDING': 'attention',
            'IN_PROGRESS': 'progress',
            'COMPLETED': 'success',
            'CANCELLED': 'neutral',
        }
        choices = {value for value, _ in LegalTask.Status.choices}
        self.assertEqual(choices, set(expected.keys()))
        for status, tone in expected.items():
            self.assertEqual(task_status_badge_tone(status), tone)

    def test_every_signature_request_status_maps_to_a_tone(self):
        from contracts.models import SignatureRequest

        expected = {
            'PENDING': 'neutral',
            'SENT': 'attention',
            'VIEWED': 'progress',
            'SIGNED': 'success',
            'DECLINED': 'danger',
            'EXPIRED': 'danger',
            'CANCELLED': 'neutral',
        }
        choices = {value for value, _ in SignatureRequest.Status.choices}
        self.assertEqual(choices, set(expected.keys()))
        for status, tone in expected.items():
            self.assertEqual(signature_status_badge_tone(status), tone)

    def test_every_risk_log_status_maps_to_a_tone(self):
        from contracts.models import RiskLog

        expected = {
            'OPEN': 'attention',
            'IN_PROGRESS': 'progress',
            'RESOLVED': 'success',
        }
        choices = {value for value, _ in RiskLog.Status.choices}
        self.assertEqual(choices, set(expected.keys()))
        for status, tone in expected.items():
            self.assertEqual(risk_status_badge_tone(status), tone)

    def test_unknown_value_falls_back_to_neutral_not_a_crash(self):
        self.assertEqual(contract_status_badge_tone('NOT_A_REAL_STATUS'), 'neutral')
        self.assertEqual(contract_risk_badge_tone('NOT_A_REAL_RISK_LEVEL'), 'neutral')
        self.assertEqual(task_status_badge_tone('NOT_A_REAL_STATUS'), 'neutral')
        self.assertEqual(signature_status_badge_tone('NOT_A_REAL_STATUS'), 'neutral')
        self.assertEqual(risk_status_badge_tone('NOT_A_REAL_STATUS'), 'neutral')
