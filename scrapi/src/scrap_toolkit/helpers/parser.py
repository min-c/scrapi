# src/scrap_toolkit/helpers/parsers.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


# ---------- Generic HTML helpers ----------

def safe_text(el, *, sep: str = " ", strip: bool = True) -> str:
    if not el:
        return ""
    txt = el.get_text(separator=sep)
    return txt.strip() if strip else txt


def extract_links(html: str, base_url: Optional[str] = None) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    out: List[Dict[str, str]] = []
    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        abs_url = urljoin(base_url, href) if base_url else href
        out.append({"text": safe_text(a), "href": abs_url})
    return out


def extract_titles(html: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    return [safe_text(h) for h in soup.select("h1, h2, h3")]


def normalize_url(url: str, base: Optional[str]) -> str:
    return urljoin(base, url) if base else url


# ---------- Article/body extraction ----------

def extract_article_text(html: str, base_url: Optional[str] = None, *, selector_map: Optional[Dict[str, str]] = None, max_chars: int = 4000) -> str:
    """
    간단한 기사 본문 추출.
    - selector_map이 있으면 우선 적용 (도메인별 규칙)
    - 없으면 <article> 또는 주요 컨테이너를 추정
    """
    soup = BeautifulSoup(html, "lxml")

    # 1) 도메인별/사이트별 규칙
    if selector_map:
        for css in selector_map.values():
            node = soup.select_one(css)
            if node:
                return safe_text(node)[:max_chars]

    # 2) fallback: <article> 또는 본문스러운 컨테이너
    for css in ["article", "main", "div[itemprop='articleBody']", "section.article", "div#article_body"]:
        node = soup.select_one(css)
        if node:
            return safe_text(node)[:max_chars]

    # 3) 최후: body 전체의 텍스트 (노이즈 많음)
    return safe_text(soup.body)[:max_chars] if soup.body else ""


# ---------- Pagination helpers ----------

def find_next_page(html: str, base_url: Optional[str] = None) -> Optional[str]:
    """
    '다음', 'Next', '›', rel=next 링크를 찾아 다음 페이지 URL을 반환.
    """
    soup = BeautifulSoup(html, "lxml")

    # rel=next 우선
    link = soup.find("link", rel=lambda v: v and "next" in v.lower())
    if link and link.get("href"):
        return normalize_url(link["href"], base_url)

    # 텍스트 패턴
    for a in soup.select("a[href]"):
        t = safe_text(a).lower()
        if t in {"next", "다음", "다음페이지", "다음 글", "›", "»"}:
            return normalize_url(a["href"], base_url)

    return None


# ---------- JSON helpers ----------

def jget(obj: Any, *path: str, default: Any = None) -> Any:
    """
    dict/list에서 안전하게 중첩 경로로 값을 꺼낸다.
    예: jget(data, "data", "items", "0", "title")
    """
    cur = obj
    for key in path:
        if isinstance(cur, dict):
            cur = cur.get(key, default)
        elif isinstance(cur, list):
            try:
                idx = int(key)
                cur = cur[idx]
            except Exception:
                return default
        else:
            return default
        if cur is None:
            return default
    return cur
