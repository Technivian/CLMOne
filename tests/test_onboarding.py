"""Tests for self-serve onboarding service."""
import unittest
from unittest.mock import MagicMock, patch

from contracts.services.onboarding import OnboardingService, ONBOARDING_STEPS


def _make_progress(steps_completed=None, current_step='org_profile', completed=False, completed_at=None, org_id=1):
    p = MagicMock()
    p.organization_id = org_id
    p.steps_completed = steps_completed or []
    p.current_step = current_step
    p.completed = completed
    p.completed_at = completed_at
    return p


class TestOnboardingService(unittest.TestCase):
    def setUp(self):
        self.svc = OnboardingService()
        self.org = MagicMock()
        self.org.pk = 1

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_get_progress_initial(self, MockOP):
        p = _make_progress()
        MockOP.objects.get_or_create.return_value = (p, True)
        state = self.svc.get_progress(self.org)
        self.assertEqual(state.current_step, 'org_profile')
        self.assertEqual(state.steps_completed, [])
        self.assertFalse(state.completed)
        self.assertEqual(state.progress_pct, 0)

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_get_progress_halfway(self, MockOP):
        p = _make_progress(steps_completed=['org_profile', 'invite_members'])
        MockOP.objects.get_or_create.return_value = (p, False)
        state = self.svc.get_progress(self.org)
        self.assertEqual(state.progress_pct, 40)
        self.assertEqual(state.remaining_steps, ['first_contract', 'configure_policy', 'connect_integration'])

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_advance_valid_step(self, MockOP):
        p = _make_progress(steps_completed=[])
        p.save = MagicMock()
        MockOP.objects.get_or_create.return_value = (p, True)
        state = self.svc.advance_step(self.org, 'org_profile')
        self.assertIn('org_profile', p.steps_completed)

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_advance_invalid_step(self, MockOP):
        p = _make_progress()
        p.save = MagicMock()
        MockOP.objects.get_or_create.return_value = (p, True)
        with self.assertRaises(ValueError):
            self.svc.advance_step(self.org, 'nonexistent_step')

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_advance_all_steps_marks_complete(self, MockOP):
        p = _make_progress(steps_completed=list(ONBOARDING_STEPS[:-1]))
        p.save = MagicMock()
        MockOP.objects.get_or_create.return_value = (p, False)
        state = self.svc.advance_step(self.org, ONBOARDING_STEPS[-1])
        self.assertTrue(p.completed)

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_mark_complete_sets_all_steps(self, MockOP):
        p = _make_progress(steps_completed=[])
        p.save = MagicMock()
        MockOP.objects.get_or_create.return_value = (p, False)
        state = self.svc.mark_complete(self.org)
        self.assertEqual(p.steps_completed, list(ONBOARDING_STEPS))
        self.assertTrue(p.completed)
        self.assertEqual(state.progress_pct, 100)

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_reset_clears_progress(self, MockOP):
        p = _make_progress(steps_completed=['org_profile', 'invite_members'], completed=True)
        p.save = MagicMock()
        MockOP.objects.get_or_create.return_value = (p, False)
        state = self.svc.reset(self.org)
        self.assertEqual(p.steps_completed, [])
        self.assertFalse(p.completed)
        self.assertEqual(p.current_step, ONBOARDING_STEPS[0])

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_next_step_logic(self, MockOP):
        p = _make_progress(steps_completed=['org_profile'])
        MockOP.objects.get_or_create.return_value = (p, False)
        state = self.svc.get_progress(self.org)
        self.assertEqual(state.next_step, 'invite_members')

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_next_step_none_when_complete(self, MockOP):
        p = _make_progress(steps_completed=list(ONBOARDING_STEPS), completed=True)
        MockOP.objects.get_or_create.return_value = (p, False)
        state = self.svc.get_progress(self.org)
        self.assertIsNone(state.next_step)

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_duplicate_advance_not_doubled(self, MockOP):
        p = _make_progress(steps_completed=['org_profile'])
        p.save = MagicMock()
        MockOP.objects.get_or_create.return_value = (p, False)
        self.svc.advance_step(self.org, 'org_profile')
        self.assertEqual(p.steps_completed.count('org_profile'), 1)

    def test_onboarding_steps_count(self):
        self.assertEqual(len(ONBOARDING_STEPS), 5)

    @patch('contracts.services.onboarding.OnboardingProgress')
    def test_completed_at_set_on_mark_complete(self, MockOP):
        p = _make_progress(completed=False, completed_at=None)
        p.save = MagicMock()
        MockOP.objects.get_or_create.return_value = (p, False)
        self.svc.mark_complete(self.org)
        self.assertIsNotNone(p.completed_at)


if __name__ == '__main__':
    unittest.main()
