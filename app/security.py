from __future__ import annotations

import base64
import hmac
import json
import time
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt import PyJWKClient

from app.config import Settings
from app.core.errors import ApiError


_jwks_client: PyJWKClient | None = None

def get_jwks_client(supabase_url: str) -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client

def decode_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
    except Exception as e:
        print(f"\n[JWT Header Debug Error]: {e}\n")
        alg = "HS256"

    # Support modern ES256 asymmetric signatures used by newer Supabase projects
    if alg == "ES256":
        try:
            jwks_client = get_jwks_client(settings.supabase_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                options={"verify_aud": False},
                leeway=120,
            )
        except Exception as exc:
            print(f"\n[JWT ES256 Auth Error]: {exc}\n")
            raise ApiError(
                status_code=401, code="unauthorized", message=f"Invalid bearer token (ES256): {exc}"
            ) from exc

    # Fallback to legacy HS256 symmetric signature
    secret = settings.supabase_jwt_secret
    
    # Supabase JWT secrets are base64-encoded. We attempt to base64-decode it,
    # falling back to the literal string if decoding fails or isn't needed.
    decoded_secret = None
    try:
        # Standard base64 decoding
        decoded_secret = base64.b64decode(secret)
    except Exception:
        pass

    try:
        if decoded_secret:
            try:
                return jwt.decode(
                    token,
                    decoded_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                    leeway=120,
                )
            except jwt.PyJWTError:
                # If decoded secret failed to verify signature, fall back to literal secret
                pass
                
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
            leeway=120,
        )
    except jwt.PyJWTError as exc:
        print(f"\n[JWT HS256 Auth Error]: {exc}\n")
        raise ApiError(
            status_code=401, code="unauthorized", message=f"Invalid bearer token (HS256): {exc}"
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
