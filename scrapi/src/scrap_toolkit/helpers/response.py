# src/scraper_toolkit/helpers/response.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

try:
    # 선택 의존성: 자동 인코딩 감지
    from charset_normalizer import from_bytes as _cn_from_bytes  # type: ignore
except Exception:  # pragma: no cover
    _cn_from_bytes = None  # 사용 불가 시 None

JSONLike = Dict[str, Any]


@dataclass
class BodyResult:
    """
    통합 응답 컨테이너.
    - is_json: True면 data에 dict(JSON)이 들어있음
    - text: 문자열 본문(항상 채워짐; JSON이면 pretty-printed 또는 원문)
    - data: JSON dict (없으면 None)
    - encoding: 최종 사용된 인코딩(추정치 포함)
    - ctype: 응답 Content-Type 헤더(소문자)
    """
    is_json: bool
    text: str
    data: Optional[JSONLike]
    encoding: str
    ctype: str


def _infer_content_type(resp) -> str:
    return (resp.headers.get("Content-Type") or "").lower()


def _decode_text(resp, *, default_enc: str = "utf-8") -> Tuple[str, str]:
    """
    resp.content(bytes) → str로 안전하게 디코드.
    charset 헤더, requests 추정, charset-normalizer, fallback 순서로 처리.
    반환: (text, encoding)
    """
    # 1) requests가 아는 인코딩 우선
    if resp.encoding:
        try:
            return resp.text, resp.encoding
        except Exception:
            pass

    raw = resp.content

    # 2) charset-normalizer로 자동 감지 (설치되어 있으면)
    if _cn_from_bytes is not None:
        try:
            best = _cn_from_bytes(raw).best()
            if best:
                return best.output(), best.encoding or default_enc
        except Exception:
            pass

    # 3) 흔한 한국어/국제 인코딩 시도
    for enc in ("utf-8", "cp949", "euc-kr", "latin-1"):
        try:
            return raw.decode(enc), enc
        except Exception:
            continue

    # 4) 마지막으로 유니코드 치환
    return raw.decode(default_enc, errors="replace"), default_enc


def body(resp, *, pretty_json: bool = True, default_json_if_empty: bool = False) -> BodyResult:
    """
    응답을 '한 번에' 다룬다.
    - JSON이면 dict로 파싱하고, text는 (pretty_json=True면) 이쁘게 출력한 문자열로 채움
    - JSON 아니면 text로 디코드해서 채움
    - 항상 BodyResult 반환

    default_json_if_empty=True:
      Content-Type이 json인데 body가 비어있는 204/304 등에서 {}로 반환하도록 강제
    """
    ctype = _infer_content_type(resp)

    # 1) JSON 우선 처리 (헤더로 판단)
    if "json" in ctype:
        try:
            data = resp.json()
            text = json.dumps(data, ensure_ascii=False, indent=2) if pretty_json else resp.text
            enc = resp.encoding or "utf-8"
            return BodyResult(True, text, data, enc, ctype)
        except Exception:
            # 헤더는 json인데 본문 파싱 실패 → 텍스트로 폴백
            pass

    # 2) 헤더 확실치 않음 → 먼저 JSON 시도, 실패 시 텍스트
    try:
        data = resp.json()
        text = json.dumps(data, ensure_ascii=False, indent=2) if pretty_json else resp.text
        enc = resp.encoding or "utf-8"
        return BodyResult(True, text, data, enc, ctype)
    except Exception:
        if "json" in ctype and default_json_if_empty and not resp.content:
            # json 헤더인데 body가 비어있는 경우 옵션으로 {} 처리
            return BodyResult(True, "{}" if pretty_json else "{}", {}, resp.encoding or "utf-8", ctype)

    # 3) 텍스트로 안전 디코드
    text, enc = _decode_text(resp)
    return BodyResult(False, text, None, enc, ctype)


def preview(text: str, limit: int = 1500) -> str:
    """긴 본문을 로그/콘솔용으로 미리보기 자르기."""
    if text is None:
        return ""
    return text if len(text) <= limit else text[:limit] + "\n…(truncated)"


def save(path: str, content: str, *, encoding: str = "utf-8") -> None:
    """본문을 파일에 저장."""
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding=encoding) as f:
        f.write(content)