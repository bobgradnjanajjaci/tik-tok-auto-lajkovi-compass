import re
import requests
from typing import List, Optional

# ✅ Default keywords za Money Forbidden Compass (možeš mijenjati u UI)
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

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def normalize_text(s: str) -> str:
    """
    Normalizuje tekst (lowercase, ukloni višak razmaka, zadrži slova/brojeve).
    Pomaže kad TikTok ubaci emoji, čudne razmake, itd.
    """
    s = (s or "").lower()
    # zamijeni sve što nije slovo/broj u razmak
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def phrase_match(text_norm: str, phrase: str) -> bool:
    """
    Fuzzy match: fraza se razbije u tokene i svi tokeni moraju postojati u tekstu.
    Npr "damian rothwell" matcha i kad je "damian...rothwell" sa emoji između.
    """
    p = normalize_text(phrase)
    if not p:
        return False
    tokens = p.split()
    return all(t in text_norm for t in tokens)


def expand_tiktok_url(url: str) -> str:
    """
    Pretvara short TikTok link (tiktok.com/t/...) u puni link (.../@user/video/ID).
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=15)
        return r.url
    except Exception:
        return url


def extract_video_id(video_url: str) -> Optional[str]:
    match = re.search(r"/video/(\d+)", video_url)
    return match.group(1) if match else None


def fetch_comments_paged(video_id: str, count: int = 50, max_pages: int = 5) -> List[dict]:
    """
    Povuče više stranica komentara (cursor paging).
    Ovo dramatično povećava šansu da nađe tvoj komentar.
    """
    all_comments: List[dict] = []
    cursor = 0

    for _ in range(max_pages):
        url = "https://www.tiktok.com/api/comment/list/"
        params = {
            "aid": 1988,
            "count": count,
            "cursor": cursor,
            "aweme_id": video_id,
        }

        try:
            r = requests.get(url, headers=BASE_HEADERS, params=params, timeout=15)
            if r.status_code != 200:
                break

            data = r.json()
            comments = data.get("comments") or []
            all_comments.extend(comments)

            has_more = bool(data.get("has_more"))
            cursor = int(data.get("cursor") or 0)

            if not has_more:
                break
        except Exception:
            break

    return all_comments


def apply_buffer(likes: int) -> int:
    dynamic = int(likes * PERCENT_BUFFER)
    return likes + max(STATIC_BUFFER, dynamic)


def find_target_comment(video_url: str, keywords: Optional[List[str]] = None) -> dict:
    """
    1) expand short link
    2) extract video_id
    3) fetch comments (više stranica)
    4) nađi komentar koji matcha keyworde (uzima NAJLAJKANIJI match)
    """
    video_url = expand_tiktok_url(video_url)
    video_id = extract_video_id(video_url)

    if not video_id:
        return {"found": False, "error": "Video ID nije pronađen (provjeri link)", "expanded_url": video_url}

    kw = keywords if keywords and len(keywords) > 0 else DEFAULT_KEYWORDS
    kw = [k.strip() for k in kw if k and k.strip()]

    comments = fetch_comments_paged(video_id, count=50, max_pages=5)  # 250 komentara max
    if not comments:
        return {"found": False, "error": "Nema komentara ili fetch nije uspio", "expanded_url": video_url}

    top_likes = 0
    best_match = None

    for c in comments:
        likes = int(c.get("digg_count") or 0)
        text_raw = c.get("text") or ""
        text_norm = normalize_text(text_raw)

        if likes > top_likes:
            top_likes = likes

        # Match na bilo koji keyword (fuzzy token match)
        if any(phrase_match(text_norm, k) for k in kw):
            user = c.get("user") or {}
            candidate = {
                "cid": c.get("cid"),
                "likes": likes,
                "username": user.get("unique_id"),
                "text": text_raw,
            }
            # uzmi match koji ima najviše lajkova (najvjerovatnije pravi)
            if (best_match is None) or (candidate["likes"] > best_match["likes"]):
                best_match = candidate

    if not best_match or not best_match.get("cid") or not best_match.get("username"):
        return {"found": False, "error": "Keyword komentar nije pronađen", "expanded_url": video_url}

    return {
        "found": True,
        "video_id": video_id,
        "my_cid": best_match["cid"],
        "my_likes": apply_buffer(best_match["likes"]),
        "top_likes": top_likes,
        "username": best_match["username"],
        "matched_text": best_match["text"],
        "expanded_url": video_url,
    }
