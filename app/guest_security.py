"""Private guest sessions for beta traffic. Verified accounts are still a launch gate."""
import hashlib
import hmac
import os
import secrets
from time import time

COOKIE = 'pocket_guest'
SECRET = os.getenv('GUEST_SESSION_SECRET', '').encode() or secrets.token_bytes(32)
TTL = 24 * 60 * 60


def issue_token():
    value = f'{int(time())}.{secrets.token_urlsafe(32)}'
    return value + '.' + hmac.new(SECRET, value.encode(), hashlib.sha256).hexdigest()


def verify_token(token):
    if not isinstance(token, str) or len(token) > 200:
        return False
    try:
        timestamp, nonce, signature = token.split('.')
        age = time() - int(timestamp)
        value = timestamp + '.' + nonce
        expected = hmac.new(SECRET, value.encode(), hashlib.sha256).hexdigest()
        return 0 <= age < TTL and len(nonce) >= 32 and hmac.compare_digest(expected, signature)
    except (ValueError, TypeError):
        return False

# Per-process protection while durable accounts and usage billing are prepared.
from collections import deque
from threading import Lock
from time import monotonic

RATE_BUCKETS = {}
RATE_LOCK = Lock()


def allow_request(owner, group, limit, window):
    now = monotonic()
    with RATE_LOCK:
        key = (owner, group)
        if key not in RATE_BUCKETS and len(RATE_BUCKETS) >= 2000:
            expired = [k for k, (_, last) in RATE_BUCKETS.items() if now - last >= 3600]
            for k in expired:
                RATE_BUCKETS.pop(k, None)
            if len(RATE_BUCKETS) >= 2000:
                return False
        bucket, _ = RATE_BUCKETS.setdefault(key, (deque(), now))
        while bucket and now - bucket[0] >= window:
            bucket.popleft()
        RATE_BUCKETS[key] = (bucket, now)
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True
