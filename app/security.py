from __future__ import annotations

import base64
import hmac
import json
import time
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

import jwt

from app.config import Settings
from app.core.errors import ApiError


def decode_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise ApiError(
            status_code=401, code="unauthorized", message="Invalid bearer token"
        ) from exc


def parse_uuid_claim(value: Any, claim_name: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ApiError(
            status_code=401,
            code="unauthorized",
            message=f"Invalid JWT {claim_name} claim",
        ) from exc


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def sign_state(payload: dict[str, Any], secret: str, ttl_seconds: int = 600) -> str:
    state_payload = {
        **payload,
        "nonce": str(uuid4()),
        "exp": int(time.time()) + ttl_seconds,
    }
    encoded = _b64url(json.dumps(state_payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), sha256).digest()
    return f"{encoded}.{_b64url(signature)}"


def verify_state(state: str, secret: str) -> dict[str, Any]:
    try:
        encoded, signature = state.split(".", 1)
    except ValueError as exc:
        raise ApiError(
            status_code=400, code="invalid_state", message="Invalid OAuth state"
        ) from exc

    expected = _b64url(hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), sha256).digest())
    if not hmac.compare_digest(signature, expected):
        raise ApiError(status_code=400, code="invalid_state", message="Invalid OAuth state")

    payload = json.loads(_b64url_decode(encoded))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ApiError(status_code=400, code="invalid_state", message="Expired OAuth state")
    return payload


def verify_hmac_hex(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode("utf-8"), body, sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def verify_stripe_signature(body: bytes, signature_header: str, secret: str) -> bool:
    signatures = [
        part.removeprefix("v1=") for part in signature_header.split(",") if part.startswith("v1=")
    ]
    if not signatures:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, sha256).hexdigest()
    return any(hmac.compare_digest(signature, expected) for signature in signatures)
