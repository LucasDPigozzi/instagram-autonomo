import hashlib
import urllib.parse
import requests


def generate_image_url(prompt: str, width: int = 1080, height: int = 1080) -> str:
    encoded = urllib.parse.quote(prompt, safe="")

    attempts = [
        f"https://image.pollinations.ai/prompt/{encoded}",
        f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true",
        f"https://image.pollinations.ai/prompt/{encoded}?nologo=true",
    ]

    for url in attempts:
        try:
            r = requests.get(url, timeout=90)
            if r.status_code == 200:
                return url
        except Exception:
            continue

    # Fallback: imagem placeholder baseada no prompt
    seed = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % 1000
    return f"https://picsum.photos/seed/{seed}/1080/1080"
