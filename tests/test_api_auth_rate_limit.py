"""Rate limiting for token-authenticated API / SCIM surfaces.

The throttle counts AUTH FAILURES per IP (HTTP 401/403) on the configured
API/SCIM path prefixes, so credential-stuffing / provisioning-abuse is blocked
while legitimate authenticated traffic is never rate-limited.
"""

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    RATELIMIT_ENABLED=True,
    API_AUTH_FAIL_LIMIT=5,
    API_AUTH_FAIL_WINDOW_SECONDS=300,
    RATELIMIT_TRUSTED_IPS=(),
)
class ApiAuthRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse('contracts:contracts_api_v1')

    def _bad_request(self):
        return self.client.get(self.url, HTTP_AUTHORIZATION='Bearer not-a-real-token')

    def test_repeated_auth_failures_are_throttled(self):
        # First API_AUTH_FAIL_LIMIT failures return 401, then the IP is blocked.
        for _ in range(5):
            self.assertEqual(self._bad_request().status_code, 401)
        blocked = self._bad_request()
        self.assertEqual(blocked.status_code, 429)
        self.assertIn('Retry-After', blocked)

    def test_scim_failures_share_the_throttle(self):
        scim_url = reverse('contracts:scim_users_api')
        for _ in range(5):
            self.client.get(scim_url, HTTP_AUTHORIZATION='Bearer bad')
        blocked = self.client.get(scim_url, HTTP_AUTHORIZATION='Bearer bad')
        self.assertEqual(blocked.status_code, 429)

    @override_settings(RATELIMIT_ENABLED=False)
    def test_disabled_flag_bypasses_throttle(self):
        for _ in range(8):
            self.assertEqual(self._bad_request().status_code, 401)

    @override_settings(RATELIMIT_TRUSTED_IPS=('127.0.0.1',))
    def test_trusted_ip_is_not_throttled(self):
        for _ in range(8):
            self.assertEqual(self._bad_request().status_code, 401)
