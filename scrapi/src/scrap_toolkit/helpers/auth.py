# src/scrap_toolkit/helpers/auth.py
from __future__ import annotations

import json
import os
from http.cookiejar import MozillaCookieJar
from typing import Any, Dict, Iterable, Optional

from bs4 import BeautifulSoup

from ..sync_client import SyncClient


# ---------- Basic logins ----------

def login_json(
    cli: SyncClient,
    url: str,
    payload: Dict[str, Any],
    *,
    headers: Optional[Dict[str, str]] = None,
    ok_codes: Iterable[int] = (200, 204),
):
    """POST JSON으로 로그인."""
    r = cli.post(url, json=payload, headers=headers)
    if r.status_code not in ok_codes:
        raise RuntimeError(f"login_json failed: {r.status_code} {r.text[:300]}")
    return r


def login_form(
    cli: SyncClient,
    url: str,
    form: Dict[str, Any],
    *,
    headers: Optional[Dict[str, str]] = None,
    ok_codes: Iterable[int] = (200, 302),
):
    """application/x-www-form-urlencoded 폼 로그인."""
    h = {"Content-Type": "application/x-www-form-urlencoded"}
    if headers:
        h.update(headers)
    r = cli.post(url, data=form, headers=h)
    if r.status_code not in ok_codes:
        raise RuntimeError(f"login_form failed: {r.status_code} {r.text[:300]}")
    return r


# ---------- CSRF helpers ----------

def extract_csrf_from_html(html: str, *, meta_name: str = "csrf-token") -> Optional[str]:
    """
    <meta name="csrf-token" content="..."> 형태 또는
    input[name=csrfmiddlewaretoken] 등에서 토큰을 추출.
    """
    soup = BeautifulSoup(html, "lxml")
    meta = soup.find("meta", attrs={"name": meta_name})
    if meta and meta.get("content"):
        return meta["content"]

    inp = soup.find("input", attrs={"name": "csrfmiddlewaretoken"})
    if inp and inp.get("value"):
        return inp["value"]

    # 프레임워크별로 스크립트 내 전역변수에 들어있을 수도 있음 (간단 패턴 예시)
    # window.__CSRF__ = "....";
    for script in soup.find_all("script"):
        if not script.string:
            continue
        s = script.string
        if "__CSRF__" in s:
            try:
                # 매우 러프한 예시: window.__CSRF__ = "token"
                token = s.split("__CSRF__")[1].split("=")[1].split(";")[0].strip().strip('"').strip("'")
                if token:
                    return token
            except Exception:
                pass
    return None


def attach_csrf_header(cli: SyncClient, token: str, header_name: str = "X-CSRF-Token"):
    """세션 헤더에 CSRF 토큰을 심는다."""
    cli.session.headers[header_name] = token


# ---------- Bearer / Token helpers ----------

def attach_bearer_token(cli: SyncClient, token: str):
    cli.session.headers["Authorization"] = f"Bearer {token}"


def refresh_bearer_token(
    cli: SyncClient,
    url: str,
    *,
    refresh_token: str,
    field_name: str = "refresh_token",
    ok_codes: Iterable[int] = (200,),
) -> str:
    """
    리프레시 토큰으로 새 액세스 토큰을 발급받아 Authorization 헤더에 붙인다.
    서버 API 응답 스키마에 맞게 파싱 부분 수정.
    """
    r = cli.post(url, json={field_name: refresh_token})
    if r.status_code not in ok_codes:
        raise RuntimeError(f"refresh token failed: {r.status_code} {r.text[:300]}")
    data = r.json()
    access = data.get("access_token") or data.get("access") or data.get("token")
    if not access:
        raise RuntimeError("No access token in refresh response")
    attach_bearer_token(cli, access)
    return access


# ---------- Cookie persistence ----------

def save_cookies(cli: SyncClient, path: str):
    """
    쿠키를 netscape/mozilla 포맷으로 저장.
    브라우저/툴과 공유 가능(일부).
    """
    cj = MozillaCookieJar(path)
    for c in cli.session.cookies:
        cj.set_cookie(c)
    cj.save(ignore_discard=True, ignore_expires=True)


def load_cookies(cli: SyncClient, path: str):
    if not os.path.exists(path):
        return
    cj = MozillaCookieJar(path)
    cj.load(ignore_discard=True, ignore_expires=True)
    for c in cj:
        cli.session.cookies.set_cookie(c)
