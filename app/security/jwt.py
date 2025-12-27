from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
import jwt
from jwt import PyJWKClient, PyJWTError
from jwt.exceptions import PyJWKClientError


#  TODO: modularize to uncouple from AWS Cognito
#  TODO: move hard-coded values to security config file


@dataclass(frozen=True)
class CognitoJwtConfig:
    region: str
    user_pool_id: str
    app_client_id: str

    @property
    def issuer(self) -> str:
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/.well-known/jwks.json"


@lru_cache(maxsize=8)
def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(
        jwks_url,
        cache_jwk_set=True,
        lifespan=300,
    )


class JwtValidationError(Exception):
    pass


def verify_cognito_access_token(token: str, cfg: CognitoJwtConfig) -> dict[str, Any]:
    try:
        jwk_client = _get_jwk_client(cfg.jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=cfg.issuer,
            options={
                "require": ["exp", "iat", "sub", "iss"],
            },
        )
    except (PyJWKClientError, PyJWTError) as e:
        raise JwtValidationError(
            f"JWT signature/standard claim validation failed: {e}"
        ) from e

    token_use = claims.get("token_use")
    if token_use != "access":
        raise JwtValidationError(
            f"Expected access token (token_use=access), got: {token_use}"
        )

    client_id = claims.get("client_id")
    if client_id != cfg.app_client_id:
        raise JwtValidationError("Token was not issued for this app client")

    return claims


def extract_scopes(claims: dict[str, Any]) -> list[str]:
    scope_str = claims.get("scope") or ""
    if isinstance(scope_str, str) and scope_str.strip():
        return scope_str.split()
    return []


def extract_groups(claims: dict[str, Any]) -> list[str]:
    groups = claims.get("cognito:groups") or []
    if isinstance(groups, list):
        return [str(g) for g in groups]
    return []
