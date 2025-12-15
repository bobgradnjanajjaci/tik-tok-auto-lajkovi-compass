import time
import requests
from comment_finder import find_target_comment
from like_rules import calculate_target_likes

LIKE_APP_URL = "https://lajkovi-crtica-lajkovi.up.railway.app/"  # ⬅️ tvoj URL


def process_video(video_url: str, keywords: list[str] | None = None) -> dict:
    # 🔁 1. pokušaj
    result = find_target_comment(video_url, keywords)

    # 🔁 2. pokušaj ako prvi ne uspije
    if not result.get("found"):
        time.sleep(2)
        result = find_target_comment(video_url, keywords)

    if not result.get("found"):
        return {
            "status": "error",
            "message": "Komentar nije pronađen ni nakon 2 pokušaja"
        }

    top_likes = result["top_likes"]
    my_likes = result["my_likes"]
    username = result["username"]

    target = calculate_target_likes(top_likes)
    if target == 0:
        return {"status": "skip", "message": "Top komentar prevelik"}

    to_send = max(0, target - my_likes)
    if to_send <= 0:
        return {"status": "ok", "message": "Već ima dovoljno lajkova"}

    payload = {
        "orders": f"{video_url} {username} {to_send}"
    }

    r = requests.post(LIKE_APP_URL, data=payload, timeout=25)

    return {
        "status": "sent",
        "likes_sent": to_send,
        "username": username,
        "top_likes": top_likes,
        "my_likes_buffered": my_likes,
        "matched_text": result["matched_text"][:120],
        "response": r.text[:200]
    }
