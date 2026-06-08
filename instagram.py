import os
import time
import requests

BASE = "https://graph.facebook.com/v19.0"


def _token():
    return os.environ["INSTAGRAM_ACCESS_TOKEN"]


def _account():
    return os.environ["INSTAGRAM_ACCOUNT_ID"]


def _get(path, params=None):
    params = params or {}
    params["access_token"] = _token()
    r = requests.get(f"{BASE}/{path}", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"]["message"])
    return data


def _post(path, data=None):
    data = data or {}
    data["access_token"] = _token()
    r = requests.post(f"{BASE}/{path}", data=data, timeout=90)
    r.raise_for_status()
    result = r.json()
    if "error" in result:
        raise RuntimeError(result["error"]["message"])
    return result


def _create_container(payload):
    return _post(f"{_account()}/media", payload)["id"]


def _publish(container_id):
    for _ in range(8):
        status = _get(container_id, {"fields": "status_code"})
        code = status.get("status_code", "")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"Erro no processamento do container: {status}")
        time.sleep(5)
    return _post(f"{_account()}/media_publish", {"creation_id": container_id})["id"]


def post_photo(image_url, caption=""):
    cid = _create_container({"image_url": image_url, "caption": caption})
    return _publish(cid)


def post_reel(video_url, caption=""):
    cid = _create_container({"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true"})
    return _publish(cid)


def post_story_image(image_url):
    cid = _create_container({"media_type": "STORIES", "image_url": image_url})
    return _publish(cid)


def get_account_insights(period="week"):
    data = _get(f"{_account()}/insights", {"metric": "impressions,reach,profile_views,follower_count", "period": period})
    result = {}
    for item in data.get("data", []):
        vals = item.get("values", [])
        result[item["name"]] = vals[-1]["value"] if vals else None
    return result


def get_recent_media(limit=10):
    data = _get(f"{_account()}/media", {"fields": "id,caption,media_type,timestamp,like_count,comments_count,permalink", "limit": limit})
    return data.get("data", [])


def get_account_info():
    return _get(_account(), {"fields": "username,name,biography,followers_count,follows_count,media_count"})
