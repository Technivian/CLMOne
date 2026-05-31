const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command:
          "cd .. && export DJANGO_E2E=1; PY=.venv/bin/python; if [ ! -x \"$PY\" ]; then PY=python; fi; $PY manage.py shell -c \"from django.contrib.auth import get_user_model; U=get_user_model(); u,_=U.objects.get_or_create(username='e2e_owner', defaults={'email':'e2e_owner@example.com'}); u.is_staff=True; u.is_superuser=True; u.set_password('e2e_pass_123'); u.save()\" && $PY manage.py runserver 127.0.0.1:8010",
        url: 'http://127.0.0.1:8010/login/',
        reuseExistingServer: true,
        timeout: 120000,
      },
  use: {
    headless: true,
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:8010',
  },
  reporter: 'list',
});
