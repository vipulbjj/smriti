"""
Per-phone rate limiting for the inbound webhook.

Twilio signature validation only stops non-Twilio senders; a genuine sender who
knows a grandparent's number could still flood the webhook. This is a simple
in-memory token bucket keyed by phone.

Caveat: in-memory state does not persist across Vercel serverless cold starts,
so this is a best-effort layer there rather than a hard guarantee. On a
long-lived (non-serverless) deployment it works as intended. Swap the store for
Redis if a hard limit is needed across instances.
"""

import os
import time
from collections import defaultdict
from threading import Lock

_MAX = int(os.environ.get("WEBHOOK_RATE_MAX", "10"))      # messages
_WINDOW = int(os.environ.get("WEBHOOK_RATE_WINDOW", "3600"))  # seconds

_hits: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def allow(phone: str, now: float | None = None) -> bool:
    """Return True if `phone` may send another message, False if over the limit.

    Sliding window: keeps timestamps within the last _WINDOW seconds and allows
    up to _MAX per window.
    """
    now = time.time() if now is None else now
    cutoff = now - _WINDOW
    with _lock:
        times = [t for t in _hits[phone] if t > cutoff]
        if len(times) >= _MAX:
            _hits[phone] = times
            return False
        times.append(now)
        _hits[phone] = times
        return True


def reset(phone: str | None = None) -> None:
    """Clear rate-limit state (for tests / admin). None clears everything."""
    with _lock:
        if phone is None:
            _hits.clear()
        else:
            _hits.pop(phone, None)
