"""Utilities for checking and masking environment secrets."""

import os
from typing import Any


# Environment variables used by the WhatsApp adapter.
SECRET_ENV_VARS = (
    "WHATSAPP_TOKEN",
    "WHATSAPP_VERIFY_TOKEN",
    "WHATSAPP_PHONE_ID",
)

OPTIONAL_ENV_VARS = (
    "WHATSAPP_PROVIDER",
)


def mask_secret(value: str | None) -> str:
    """Return a masked representation of a secret (first 4 + last 4 chars)."""
    if not value:
        return "<not set>"
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def check_secrets() -> dict[str, Any]:
    """Return masked status for all known environment variables."""
    secrets: dict[str, str] = {}
    for name in SECRET_ENV_VARS:
        secrets[name] = mask_secret(os.getenv(name))

    optional: dict[str, str] = {}
    for name in OPTIONAL_ENV_VARS:
        raw = os.getenv(name)
        optional[name] = raw if raw else "<not set>"

    all_required_set = all(os.getenv(name) for name in SECRET_ENV_VARS)

    return {
        "secrets": secrets,
        "optional": optional,
        "all_required_set": all_required_set,
    }


def log_secrets_status(prefix: str = "[SECRETS]") -> None:
    """Print masked secret status to stdout on startup."""
    status = check_secrets()
    print(f"{prefix} Environment check:", flush=True)
    for name, masked in status["secrets"].items():
        loaded = "loaded" if masked != "<not set>" else "MISSING"
        print(f"{prefix}   {name}: {masked} ({loaded})", flush=True)
    for name, value in status["optional"].items():
        print(f"{prefix}   {name}: {value}", flush=True)
    if status["all_required_set"]:
        print(f"{prefix} All required secrets are set", flush=True)
    else:
        print(f"{prefix} WARNING: One or more required secrets are missing", flush=True)
