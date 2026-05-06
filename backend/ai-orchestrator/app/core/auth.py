"""Firebase ID token verification — duplicated from core-api.

Both services run independently and need their own token verification.
Spec §5.1.
"""

import hashlib
from typing import Annotated

import firebase_admin
from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth as fb_auth
from firebase_admin import credentials

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

_app: firebase_admin.App | None = None


def _firebase_app() -> firebase_admin.App:
    global _app
    if _app is not None:
        return _app
    settings = get_settings()
    if settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        _app = firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
    else:
        _app = firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
    return _app


class AuthContext:
    def __init__(self, firebase_uid: str, claims: dict[str, object]) -> None:
        self.firebase_uid = firebase_uid
        self.claims = claims

    def __repr__(self) -> str:
        return f"AuthContext(uid={self.firebase_uid!r})"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def require_auth(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="empty bearer token")

    try:
        claims = fb_auth.verify_id_token(token, app=_firebase_app(), check_revoked=False)
    except Exception as exc:
        log.warning("firebase_token_invalid", token_hash=_hash_token(token), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        ) from exc

    uid = claims.get("uid") or claims.get("sub")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token missing uid")

    return AuthContext(firebase_uid=str(uid), claims=claims)


CurrentUser = Annotated[AuthContext, Depends(require_auth)]
