import re
import requests
from typing import List, Optional

DEFAULT_KEYWORDS = [
    "money forbidden compass",
    "forbidden compass",
    "damian rothwell",
    "money compass",
    "forbidden money",
    "mfc",
]

STATIC_BUFFER = 5
PERCENT_BUFFER = 0.20

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def normalize_text(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def phrase_match(text_norm: str, phrase: str) -> bool:
    p = normalize_text(phrase)
    if not p:
        return False
    return all(tok in text_norm for tok in p.split())


def expand_tiktok_url(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                         allow_redirects=True, timeout=15)
        return r.url
    except Exception:
        return url


def extract_video_id(url: str) -> Optional[str]:
    m = re.search(r"/video/(\d+)", url)
    return m.group(1) if m else None


def fetch_comments_paged(video_id: str, count: int = 50, pages: int = 5) -> List[dict]:
    all_comments = []
    cursor = 0

    for _ in range(pages):
        params = {
            "aid": 1988,
            "count": count,
            "cursor": cursor,
            "aweme_id": video_id,
        }
        try:
            r = requests.get(
                "https://www.tiktok.com/api/comment/list/",
                headers=HEADERS,
                params=params,
                timeout=15
            )
            if r.status_code != 200:
                break

            data = r.json()
            comments = data.get("comments") or []
            all_comments.extend(comments)

            if not data.get("has_more"):
                break

            cursor = int(data.get("cursor") or 0)
        except Exception:
            break

    return all_comments


def apply_buffer(likes: int) -> int:
    return likes + max(STATIC_BUFFER, int(likes * PERCENT_BUFFER))


def find_target_comment(video_url: str, keywords: List[str] | None = None) -> dict:
    video_url = expand_tiktok_url(video_url)
    video_id = extract_video_id(video_url)

    if not video_id:
        return {"found": False, "error": "Video ID nije pronađen"}

    kw = keywords if keywords else DEFAULT_KEYWORDS
    kw = [k.strip() for k in kw if k.strip()]

    comments = fetch_comments_paged(video_id)
    if not comments:
        return {"found": False, "error": "Nema komentara"}

    top_likes = 0
    best = None

    for c in comments:
        likes = int(c.get("digg_count") or 0)
        text_raw = c.get("text") or ""
        text_norm = normalize_text(text_raw)

        top_likes = max(top_likes, likes)

        if any(phrase_match(text_norm, k) for k in kw):
            user = c.get("user") or {}
            candidate = {
                "cid": c.get("cid"),
                "likes": likes,
                "username": user.get("unique_id"),
                "text": text_raw,
            }
            if best is None or candidate["likes"] > best["likes"]:
                best = candidate

    if not best:
        return {"found": False, "error": "Keyword komentar nije pronađen"}

    return {
        "found": True,
        "video_id": video_id,
        "my_cid": best["cid"],
        "my_likes": apply_buffer(best["likes"]),
        "top_likes": top_likes,
        "username": best["username"],
        "matched_text": best["text"],
    }
