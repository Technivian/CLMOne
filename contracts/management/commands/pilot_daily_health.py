from django.core.management.base import BaseCommand

from contracts.models import Organization
from contracts.services.pilot_monitoring import build_pilot_daily_health, format_pilot_daily_health


class Command(BaseCommand):
    help = 'Print the controlled-pilot daily health summary (no contract content).'

    def add_arguments(self, parser):
        parser.add_argument('--org-slug', default='controlled-pilot-org')
        parser.add_argument('--output', default='', help='Optional file path for JSON output.')

    def handle(self, *args, **options):
        org = Organization.objects.filter(slug=options['org_slug']).first()
        summary = build_pilot_daily_health(organization=org)
        text = format_pilot_daily_health(summary)
        self.stdout.write(text)
        output = options['output']
        if output:
            with open(output, 'w', encoding='utf-8') as handle:
                handle.write(text + '\n')
            self.stdout.write(self.style.SUCCESS(f'wrote {output}'))
