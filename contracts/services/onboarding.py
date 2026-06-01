"""Guided onboarding service — tracks setup completion steps per organisation."""
from __future__ import annotations

from dataclasses import dataclass

from django.utils import timezone

from contracts.models import OnboardingProgress, Organization

ONBOARDING_STEPS = OnboardingProgress.STEPS


@dataclass
class OnboardingState:
    org_id: int
    current_step: str
    steps_completed: list[str]
    progress_pct: int
    completed: bool
    completed_at: str | None
    remaining_steps: list[str]

    @property
    def next_step(self) -> str | None:
        for step in ONBOARDING_STEPS:
            if step not in self.steps_completed:
                return step
        return None


class OnboardingService:
    def get_progress(self, org: Organization) -> OnboardingState:
        progress, _ = OnboardingProgress.objects.get_or_create(
            organization=org,
            defaults={'current_step': ONBOARDING_STEPS[0], 'steps_completed': []},
        )
        return _to_state(progress)

    def advance_step(self, org: Organization, step: str) -> OnboardingState:
        if step not in ONBOARDING_STEPS:
            raise ValueError(f'Unknown onboarding step: {step!r}. Valid: {ONBOARDING_STEPS}')
        progress, _ = OnboardingProgress.objects.get_or_create(
            organization=org,
            defaults={'current_step': ONBOARDING_STEPS[0], 'steps_completed': []},
        )
        if step not in progress.steps_completed:
            progress.steps_completed = list(progress.steps_completed) + [step]
        # Advance current_step to the next uncompleted step
        remaining = [s for s in ONBOARDING_STEPS if s not in progress.steps_completed]
        progress.current_step = remaining[0] if remaining else ONBOARDING_STEPS[-1]
        if not remaining:
            progress.completed = True
            progress.completed_at = progress.completed_at or timezone.now()
        progress.save(update_fields=['steps_completed', 'current_step', 'completed', 'completed_at', 'updated_at'])
        return _to_state(progress)

    def mark_complete(self, org: Organization) -> OnboardingState:
        progress, _ = OnboardingProgress.objects.get_or_create(
            organization=org,
            defaults={'steps_completed': list(ONBOARDING_STEPS)},
        )
        progress.steps_completed = list(ONBOARDING_STEPS)
        progress.current_step = ONBOARDING_STEPS[-1]
        progress.completed = True
        progress.completed_at = progress.completed_at or timezone.now()
        progress.save(update_fields=['steps_completed', 'current_step', 'completed', 'completed_at', 'updated_at'])
        return _to_state(progress)

    def reset(self, org: Organization) -> OnboardingState:
        progress, _ = OnboardingProgress.objects.get_or_create(organization=org)
        progress.steps_completed = []
        progress.current_step = ONBOARDING_STEPS[0]
        progress.completed = False
        progress.completed_at = None
        progress.save(update_fields=['steps_completed', 'current_step', 'completed', 'completed_at', 'updated_at'])
        return _to_state(progress)


def _to_state(p: OnboardingProgress) -> OnboardingState:
    completed_set = set(p.steps_completed or [])
    remaining = [s for s in ONBOARDING_STEPS if s not in completed_set]
    total = len(ONBOARDING_STEPS)
    pct = int(len(completed_set) / total * 100) if total else 0
    return OnboardingState(
        org_id=p.organization_id,
        current_step=p.current_step,
        steps_completed=list(p.steps_completed or []),
        progress_pct=pct,
        completed=p.completed,
        completed_at=p.completed_at.isoformat() if p.completed_at else None,
        remaining_steps=remaining,
    )


def get_onboarding_service() -> OnboardingService:
    return OnboardingService()
