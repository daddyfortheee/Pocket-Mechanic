"""Verified-email authentication through Supabase; secrets stay on the server."""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from threading import Lock
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, validator

router = APIRouter(prefix="/api/auth", tags=["accounts"])
ACCESS_COOKIE = "__Host-pg_access"
REFRESH_COOKIE = "__Host-pg_refresh"
_attempts: dict[str, deque] = defaultdict(deque)
_attempt_lock = Lock()


def configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_PUBLISHABLE_KEY"))


def provider(method: str, path: str, *, body=None, token: str | None = None) -> dict:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    if not url or not key:
        raise HTTPException(503, "Account setup is not complete yet. Please try again later.")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
        raise HTTPException(503, "Account service configuration needs attention.")
    headers = {"apikey": key, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with httpx.Client(timeout=20.0) as client:
            result = client.request(method, f"{url}/auth/v1/{path}", headers=headers, json=body)
    except httpx.RequestError as error:
        raise HTTPException(503, "The account service is temporarily unavailable. Try again.") from error
    if result.status_code >= 500:
        raise HTTPException(503, "The account service is temporarily unavailable. Try again.")
    if result.status_code >= 400:
        # Do not leak provider responses, credentials, or whether a particular email exists.
        try:
            error_code = result.json().get("error_code", "")
        except ValueError:
            error_code = ""
        if result.status_code == 429:
            raise HTTPException(429, "Too many attempts. Please wait before trying again.")
        if error_code == "email_not_confirmed":
            raise HTTPException(403, "Verify your email before signing in. Use Resend code on the verification screen.")
        if path == "verify":
            raise HTTPException(400, "That code is incorrect or expired. Try again or request a new code.")
        if path.startswith("token") and "password" in path:
            raise HTTPException(401, "Email or password is incorrect.")
        if path in ("signup", "resend", "recover"):
            raise HTTPException(400, "We couldn't send the email. Check your details and try again.")
        raise HTTPException(401, "Please sign in again.")
    if not result.content:
        return {}
    try:
        data = result.json()
        if not isinstance(data, dict):
            raise ValueError
        return data
    except ValueError as error:
        raise HTTPException(503, "The account service returned an unexpected response.") from error


def check_origin(request: Request) -> None:
    """Unsafe browser requests must originate from the configured app origin."""
    expected = os.getenv("APP_ORIGIN", "").rstrip("/")
    if not expected:
        expected = str(request.base_url).rstrip("/")
    if request.headers.get("origin", "").rstrip("/") != expected:
        raise HTTPException(403, "This request must come from Pocket Guru.")


def rate_limit(request: Request, email: str = "") -> None:
    now = time.monotonic()
    keys = [f"ip:{request.client.host if request.client else 'unknown'}"]
    if email:
        keys.append(f"email:{email}")
    with _attempt_lock:
        for key in list(_attempts):
            while _attempts[key] and _attempts[key][0] < now - 600:
                _attempts[key].popleft()
            if not _attempts[key]:
                del _attempts[key]
        if len(_attempts) > 10000:
            raise HTTPException(429, "Please wait before trying again.")
        if any(len(_attempts[key]) >= (20 if key.startswith("ip:") else 10) for key in keys):
            raise HTTPException(429, "Too many attempts. Please wait before trying again.")
        for key in keys:
            _attempts[key].append(now)


class EmailInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)

    @validator("email")
    def email_address(cls, value: str) -> str:
        value = value.strip().lower()
        if value.count("@") != 1 or any(c.isspace() for c in value) or not all(value.split("@")) or "." not in value.split("@")[1]:
            raise ValueError("Enter a valid email address.")
        return value


class Credentials(EmailInput):
    password: str = Field(min_length=8, max_length=128)


class CodeInput(EmailInput):
    code: str = Field(regex=r"^[0-9]{6}$")
    purpose: str = Field(default="signup", regex=r"^(signup|recovery)$")
    new_password: str | None = Field(default=None, min_length=8, max_length=128)


class ResendInput(EmailInput):
    purpose: str = Field(default="signup", regex=r"^(signup|recovery)$")


def verified_user(data: dict) -> dict:
    if not data.get("id") or not data.get("email") or not data.get("email_confirmed_at"):
        raise HTTPException(403, "Verify your email before using Pocket Guru.")
    return {"id": data["id"], "email": data["email"], "verified": True}


def current_user(request: Request) -> dict:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(401, "Create an account or sign in to continue.")
    user = verified_user(provider("GET", "user", token=token))
    if not request.url.path.startswith("/api/auth/") and request.headers.get("x-pocket-guru-user") != user["id"]:
        raise HTTPException(401, "Your account changed. Sign in again to continue.")
    return user


def set_session(response: Response, data: dict) -> dict:
    user = verified_user(data.get("user", {}))
    access, refresh = data.get("access_token"), data.get("refresh_token")
    if not isinstance(access, str) or not isinstance(refresh, str):
        raise HTTPException(503, "Account service did not return a valid session.")
    expires = data.get("expires_in", 3600)
    expires = max(60, min(3600, expires)) if isinstance(expires, int) else 3600
    response.set_cookie(ACCESS_COOKIE, access, max_age=expires, secure=True, httponly=True, samesite="lax", path="/")
    response.set_cookie(REFRESH_COOKIE, refresh, max_age=30 * 86400, secure=True, httponly=True, samesite="lax", path="/")
    response.headers["Cache-Control"] = "no-store"
    return user


def clear_session(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(name, secure=True, httponly=True, samesite="lax", path="/")
    response.headers["Cache-Control"] = "no-store"


@router.get("/config")
def account_config(response: Response) -> dict:
    response.headers["Cache-Control"] = "no-store"
    return {"configured": configured()}


@router.post("/signup", dependencies=[Depends(check_origin)])
def signup(data: Credentials, request: Request, response: Response) -> dict:
    rate_limit(request, data.email)
    provider("POST", "signup", body={"email": data.email, "password": data.password})
    response.headers["Cache-Control"] = "no-store"
    # Signup never grants a session. Confirmation must be enabled in Supabase.
    return {"verification_required": True, "message": "Check your inbox for your six-digit verification code. If you already have an account, sign in instead."}


@router.post("/signin", dependencies=[Depends(check_origin)])
def signin(data: Credentials, request: Request, response: Response) -> dict:
    rate_limit(request, data.email)
    result = provider("POST", "token?grant_type=password", body={"email": data.email, "password": data.password})
    return {"user": set_session(response, result)}


@router.post("/verify", dependencies=[Depends(check_origin)])
def verify(data: CodeInput, request: Request, response: Response) -> dict:
    rate_limit(request, data.email)
    if data.purpose == "recovery" and not data.new_password:
        raise HTTPException(400, "Choose a new password with at least eight characters.")
    result = provider("POST", "verify", body={"email": data.email, "token": data.code, "type": data.purpose})
    verified_user(result.get("user", {}))
    if data.purpose == "recovery":
        provider("PUT", "user", token=result.get("access_token"), body={"password": data.new_password})
    return {"user": set_session(response, result)}


@router.post("/resend", dependencies=[Depends(check_origin)])
def resend(data: ResendInput, request: Request, response: Response) -> dict:
    rate_limit(request, data.email)
    if data.purpose == "recovery":
        provider("POST", "recover", body={"email": data.email})
    else:
        provider("POST", "resend", body={"email": data.email, "type": "signup"})
    response.headers["Cache-Control"] = "no-store"
    return {"message": "If this email is eligible, a new code is on its way. Check your inbox and spam folder."}


@router.post("/recover", dependencies=[Depends(check_origin)])
def recover(data: EmailInput, request: Request, response: Response) -> dict:
    rate_limit(request, data.email)
    provider("POST", "recover", body={"email": data.email})
    response.headers["Cache-Control"] = "no-store"
    return {"message": "If an account exists, we have sent a password-reset code."}


@router.post("/session", dependencies=[Depends(check_origin)])
def session(request: Request, response: Response) -> dict:
    response.headers["Cache-Control"] = "no-store"
    try:
        return {"user": current_user(request)}
    except HTTPException as error:
        if error.status_code not in (401, 403):
            raise
    refresh = request.cookies.get(REFRESH_COOKIE)
    if not refresh:
        clear_session(response)
        return {"user": None}
    try:
        result = provider("POST", "token?grant_type=refresh_token", body={"refresh_token": refresh})
        return {"user": set_session(response, result)}
    except HTTPException as error:
        if error.status_code not in (401, 403):
            raise
        clear_session(response)
        return {"user": None}


@router.post("/signout", dependencies=[Depends(check_origin)])
def signout(request: Request, response: Response) -> dict:
    token = request.cookies.get(ACCESS_COOKIE)
    if token:
        try:
            provider("POST", "logout?scope=local", token=token)
        except HTTPException:
            # Always remove this browser's cookies, including after provider outages.
            pass
    clear_session(response)
    return {"signed_out": True}
