import json
import urllib.error
import urllib.request

from fastapi import Header, HTTPException

from .state import AppState


def _verify_supabase_token(token: str) -> dict | None:
    url = f"{AppState.supabase_url.rstrip('/')}/auth/v1/user"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": AppState.supabase_anon_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError:
        return None
    except Exception:
        return None


def require_user(authorization: str | None = Header(None, alias="Authorization")):
    if not AppState.auth_enabled:
        return None

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, {"error": "Unauthorized"})

    user = _verify_supabase_token(authorization[7:])
    if not user:
        raise HTTPException(401, {"error": "Invalid or expired token"})
    return user
