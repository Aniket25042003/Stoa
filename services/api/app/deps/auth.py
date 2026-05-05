from __future__ import annotations

from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)

# Supabase asymmetric signing keys (see https://supabase.com/docs/guides/auth/jwts)
_ASYMMETRIC_ALGS = frozenset({"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"})


@lru_cache(maxsize=2)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _issuer(settings_url: str) -> str:
    return f"{settings_url.rstrip('/')}/auth/v1"


def user_id_from_jwt(token: str) -> str:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}") from e

    alg = header.get("alg")
    if alg in _ASYMMETRIC_ALGS:
        if not settings.supabase_url:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "SUPABASE_URL not configured (required for asymmetric JWT verification)",
            )
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
            try:
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=[alg],
                    issuer=_issuer(settings.supabase_url),
                    options={"verify_aud": False, "verify_iss": True},
                )
            except jwt.PyJWTError as e:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}") from e
    elif alg == "HS256":
        if not settings.supabase_jwt_secret:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "SUPABASE_JWT_SECRET not configured")
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_aud": True},
            )
        except jwt.PyJWTError:
            try:
                payload = jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
            except jwt.PyJWTError as e:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}") from e
    else:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            f"Unsupported JWT algorithm: {alg!r}",
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token missing sub")
    return str(sub)


def verify_supabase_jwt(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    return user_id_from_jwt(creds.credentials)
