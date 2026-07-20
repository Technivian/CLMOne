#!/usr/bin/env python3
"""Prove login rate limiting shares a Redis counter across logical workers.

Usage (requires Redis):
  REDIS_URL=redis://127.0.0.1:6379/15 \\
  DJANGO_SETTINGS_MODULE=config.settings_development \\
  .venv/bin/python scripts/verify_redis_login_rate_limit.py

Exit 0 on success; non-zero on failure. Never logs credentials.
"""
from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_development')
os.environ.setdefault('DJANGO_DEBUG', 'false')

redis_url = os.environ.get('REDIS_URL', '').strip()
if not redis_url:
    print('FAIL: REDIS_URL is required for multi-worker rate-limit verification')
    sys.exit(2)

import django

django.setup()

from django.conf import settings
from django.core.cache import cache
from django.test import Client

from django.contrib.auth import get_user_model

User = get_user_model()

LIMIT = 3
WINDOW = 60
IP_A = '198.51.100.10'
IP_B = '198.51.100.20'


def _backend_ok() -> bool:
    backend = settings.CACHES['default']['BACKEND']
    if 'redis' not in backend.lower():
        print(f'FAIL: expected Redis cache backend, got {backend}')
        return False
    cache.set('pilot-rl-probe', '1', timeout=5)
    if cache.get('pilot-rl-probe') != '1':
        print('FAIL: Redis cache set/get failed')
        return False
    return True


def _clear_keys():
    for path, ip in (('/login/', IP_A), ('/login/', IP_B)):
        cache.delete(f'auth-rl:{path}:{ip}')
        cache.delete(f'auth-rl-reset:{path}:{ip}')


def _post_login(ip: str, username: str, password: str) -> int:
    client = Client()
    response = client.post(
        '/login/',
        {'username': username, 'password': password},
        REMOTE_ADDR=ip,
    )
    return response.status_code


def main() -> int:
    print(f'Using cache backend: {settings.CACHES["default"]["BACKEND"]}')
    print('REDIS_URL present: yes (value redacted)')
    if not _backend_ok():
        return 2

    from django.test.utils import override_settings

    with override_settings(
        RATELIMIT_ENABLED=True,
        LOGIN_RATE_LIMIT_REQUESTS=LIMIT,
        LOGIN_RATE_LIMIT_WINDOW_SECONDS=WINDOW,
        RATELIMIT_TRUSTED_IPS=(),
        DEBUG=False,
        ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'],
    ):
        user, _ = User.objects.get_or_create(username='rl_pilot_user', defaults={'email': 'rl_pilot@example.com'})
        user.set_password('CorrectPass123!')
        user.save()

        _clear_keys()

        # Simulate multiple application workers by using distinct Django test
        # clients that all hit the same Redis-backed counter (sequential posts
        # avoid SQLite audit-write lock noise; shared-cache correctness is the gate).
        statuses = []
        for _ in range(LIMIT):
            statuses.append(_post_login(IP_A, 'rl_pilot_user', 'wrong-password'))
        if any(code != 200 for code in statuses):
            print(f'FAIL: expected {LIMIT} failed logins to return 200, got {statuses}')
            return 1

        blocked = _post_login(IP_A, 'rl_pilot_user', 'wrong-password')
        if blocked != 429:
            print(f'FAIL: expected 429 after shared threshold, got {blocked}')
            return 1
        print('PASS: shared Redis counter blocked after sequential multi-client failures')

        # Concurrent workers must share the atomic Redis counter.
        _clear_keys()
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [
                pool.submit(_post_login, IP_A, 'rl_pilot_user', 'wrong-password')
                for _ in range(LIMIT + 3)
            ]
            concurrent_statuses = [future.result() for future in as_completed(futures)]
        if 429 not in concurrent_statuses:
            print(f'FAIL: expected at least one 429 under concurrent shared Redis posts, got {concurrent_statuses}')
            return 1
        print(f'PASS: concurrent multi-client posts observed statuses {sorted(concurrent_statuses)}')

        # Unrelated IP is not blocked.
        other = _post_login(IP_B, 'rl_pilot_user', 'wrong-password')
        if other != 200:
            print(f'FAIL: unrelated IP incorrectly blocked ({other})')
            return 1
        print('PASS: unrelated IP remains unblocked')

        _clear_keys()
        success = _post_login(IP_A, 'rl_pilot_user', 'CorrectPass123!')
        if success != 302:
            print(f'FAIL: successful login expected 302, got {success}')
            return 1
        print('PASS: successful login returns 302')

        cache.set('pilot-rl-probe-end', 'ok', timeout=5)
        if cache.get('pilot-rl-probe-end') != 'ok':
            print('FAIL: Redis unhealthy after verification')
            return 1
        print('PASS: Redis remains healthy')
        print('ALL REDIS RATE-LIMIT CHECKS PASSED')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
