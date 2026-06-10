from __future__ import annotations

import time
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import get_settings
from app.services.auth_state import user_is_email_verified

bearer_scheme = HTTPBearer(auto_error=False)
_ASYMMETRIC_ALGS = frozenset({"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"})
_JWKS_TTL_SECONDS = 3600
_jwks_cache: dict[str, tuple[float, PyJWKClient]] = {}


def _issuer(settings_url: str) -> str:
    return f"{settings_url.rstrip('/')}/auth/v1"


def _jwks_client(jwks_url: str) -> PyJWKClient:
    now = time.time()
    cached = _jwks_cache.get(jwks_url)
    if cached and now - cached[0] < _JWKS_TTL_SECONDS:
        return cached[1]
    client = PyJWKClient(jwks_url)
    _jwks_cache[jwks_url] = (now, client)
    return client


def payload_from_jwt(token: str) -> dict:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from None

    alg = header.get("alg")
    if alg in _ASYMMETRIC_ALGS:
        if not settings.supabase_url:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "SUPABASE_URL not configured")
        jwks_url = _issuer(settings.supabase_url) + "/.well-known/jwks.json"
        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
        try:
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                audience="authenticated",
                issuer=_issuer(settings.supabase_url),
                options={"verify_aud": True, "verify_iss": True},
            )
        except jwt.PyJWTError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from None
    elif alg == "HS256":
        if not settings.supabase_jwt_secret:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "SUPABASE_JWT_SECRET not configured")
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=_issuer(settings.supabase_url) if settings.supabase_url else None,
                options={"verify_aud": True, "verify_iss": bool(settings.supabase_url)},
            )
        except jwt.PyJWTError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from None
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return dict(payload)


def user_id_from_jwt(token: str) -> str:
    payload = payload_from_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return str(sub)


def _require_verified_email(payload: dict) -> None:
    user_id = str(payload["sub"])
    if not user_is_email_verified(user_id, payload):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email verification required")


def verify_supabase_jwt(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    payload = payload_from_jwt(creds.credentials)
    _require_verified_email(payload)
    return str(payload["sub"])


def verify_supabase_jwt_payload(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    return payload_from_jwt(creds.credentials)


def verify_supabase_jwt_payload_verified(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    payload = payload_from_jwt(creds.credentials)
    _require_verified_email(payload)
    return payload
