from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from contracts.models import OrganizationMembership, UserProfile


User = get_user_model()


@override_settings(
    AUTHENTICATION_BACKENDS=[
        'django.contrib.auth.backends.ModelBackend',
        'django.contrib.auth.backends.AllowAllUsersModelBackend',
    ]
)
class RegistrationFlowTests(TestCase):
    def test_register_get_sets_csrf_cookie(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.CSRF_COOKIE_NAME, response.cookies)

    def test_register_succeeds_with_multiple_auth_backends(self):
        response = self.client.post(
            reverse('register'),
            data={
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'SafePass123!',
                'password2': 'SafePass123!',
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dashboard'))

        user = User.objects.get(username='newuser')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertEqual(int(self.client.session.get('_auth_user_id')), user.id)

        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertTrue(OrganizationMembership.objects.filter(user=user, is_active=True).exists())


class LoginPagePasswordRecoveryTests(TestCase):
    """Sub-block C4: the login page must link to password recovery, and the
    complete flow (link -> request -> generic confirmation) must work without
    revealing whether the submitted account exists."""

    def test_login_page_links_to_password_reset(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('password_reset'))
        self.assertContains(response, 'Forgot password?')

    def test_full_flow_for_existing_account(self):
        User.objects.create_user(username='hasaccount', email='hasaccount@example.com', password='OldPass123!')

        login_response = self.client.get(reverse('login'))
        self.assertContains(login_response, reverse('password_reset'))

        reset_page = self.client.get(reverse('password_reset'))
        self.assertEqual(reset_page.status_code, 200)

        submit_response = self.client.post(reverse('password_reset'), {'email': 'hasaccount@example.com'}, follow=True)
        self.assertRedirects(submit_response, reverse('password_reset_done'))
        self.assertContains(submit_response, 'If an account exists for that address')

    def test_full_flow_for_nonexistent_account_gives_identical_response(self):
        submit_response = self.client.post(reverse('password_reset'), {'email': 'nobody-here@example.com'}, follow=True)
        self.assertRedirects(submit_response, reverse('password_reset_done'))
        self.assertContains(submit_response, 'If an account exists for that address')
        # The confirmation page must not say anything different for a real
        # vs. fake email — verified by both flows landing on the identical URL
        # with the identical generic copy above.
