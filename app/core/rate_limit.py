"""
Simple rate limiter for auth endpoints.
Uses slowapi (in-memory storage) — no external dependencies needed.
Appropriate for on-premise single-server deployments.

For multi-worker (Gunicorn) deployments, configure a Redis backend:
  limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# key_func=get_remote_address: rate limits by client IP
# default_limits=[]: no global limit — limits applied per-route only
limiter = Limiter(key_func=get_remote_address, default_limits=[])
