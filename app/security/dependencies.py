from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import get_settings
from app.security.jwt import (
    CognitoJwtConfig,
    JwtValidationError,
    verify_cognito_access_token,
    extract_groups,
    extract_scopes,
)
from app.security.principal import Principal

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Principal:
    auth_settings = get_settings().auth

    #  dev-only bypass mode
    if getattr(auth_settings, "auth_mode", None) == "disabled":
        return Principal(
            sub="local_dev",
            username="local_dev",
            groups=["admin"],
            scopes=["*"],
            claims={},
        )

    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = creds.credentials

    try:
        cfg = CognitoJwtConfig(
            region=auth_settings.cognito_region,
            user_pool_id=auth_settings.cognito_user_pool_id,
            app_client_id=auth_settings.cognito_app_client_id,
        )
        claims = verify_cognito_access_token(token, cfg)
    except JwtValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    return Principal(
        sub=str(claims.get("sub")),
        username=claims.get("username") or claims.get("cognito:username"),
        groups=extract_groups(claims),
        scopes=extract_scopes(claims),
        claims=claims,
    )


def require_group(group: str, *, admin_group: str = "admin"):
    def _checker(principal: Principal = Depends(get_current_principal)) -> None:
        if admin_group in principal.groups:
            return
        if group not in principal.groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required group: {group}",
            )

    return _checker
