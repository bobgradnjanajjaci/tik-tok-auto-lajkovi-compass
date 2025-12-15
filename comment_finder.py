import re
import requests
from typing import List, Optional

# 🧠 SIGNATURE TOKENS — skoro nemoguće da ih ima tuđi komentar zajedno
SIGNATURE_TOKENS = [
    "money",
    "forbidden",
    "compass",
    "damian",
    "rothwell",
]

# 🥈 FRAZE KOje se stalno ponavljaju u tvojim komentarima
POWER_PHRASES = [
    "changed my life",
    "it changed my life",
    "change your life",
    "you need this book",
    "must read",
    "game changer",
    "another level",
    "read the book",
]

# 🥉 FALLBACK FRAZE
FALLBACK_PHRASES = [
    "money forbidden compass",
    "damian rothwell",
]

STATIC_BUFFER = 5
PERCENT_BUFFER = 0.20

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


def fetch_comments(video_id: str, count=50, pages=5) -> List[dict]:
    comments = []
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
            batch = data.get("comments") or []
            comments.extend(batch)

            if not data.get("has_more"):
                break

            cursor = int(data.get("cursor") or 0)
        except Exception:
            break

    return comments


def apply_buffer(likes: int) -> int:
    return likes + max(STATIC_BUFFER, int(likes * PERCENT_BUFFER))


def score_comment(text_norm: str) -> int:
    """
    Vraća score koliko je vjerovatno da je komentar tvoj.
    """
    score = 0

    # PRIORITET 1 — signature tokens
    token_hits = sum(1 for t in SIGNATURE_TOKENS if t in text_norm)
    if token_hits >= 4:
        score += 100 + token_hits * 10

    # PRIORITET 2 — power phrases
    for p in POWER_PHRASES:
        if p in text_norm:
            score += 20

    # PRIORITET 3 — fallback
    for f in FALLBACK_PHRASES:
        if f in text_norm:
            score += 10

    return score


def find_target_comment(video_url: str) -> dict:
    video_url = expand_tiktok_url(video_url)
    video_id = extract_video_id(video_url)

    if not video_id:
        return {"found": False, "error": "Video ID nije pronađen"}

    comments = fetch_comments(video_id)
    if not comments:
        return {"found": False, "error": "Nema komentara"}

    top_likes = 0
    best = None
    best_score = 0

    for c in comments:
        likes = int(c.get("digg_count") or 0)
        text_raw = c.get("text") or ""
        text_norm = normalize(text_raw)

        top_likes = max(top_likes, likes)
        score = score_comment(text_norm)

        if score > 0:
            user = c.get("user") or {}
            candidate = {
                "cid": c.get("cid"),
                "likes": likes,
                "username": user.get("unique_id"),
                "text": text_raw,
                "score": score,
            }

            # biramo najjači score, a ako je isti score → više lajkova
            if (
                best is None
                or candidate["score"] > best_score
                or (
                    candidate["score"] == best_score
                    and candidate["likes"] > best["likes"]
                )
            ):
                best = candidate
                best_score = candidate["score"]

    if not best:
        return {"found": False, "error": "Compass komentar nije pronađen"}

    return {
        "found": True,
        "video_id": video_id,
        "my_cid": best["cid"],
        "my_likes": apply_buffer(best["likes"]),
        "top_likes": top_likes,
        "username": best["username"],
        "matched_text": best["text"],
        "confidence_score": best_score,
    }
