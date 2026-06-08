"""
Geração de imagens via Pollinations.ai — 100% gratuito, sem API key.
O agente descreve a imagem em inglês (melhor qualidade) e a URL é usada
diretamente pelo Instagram Graph API.
"""

import urllib.parse
import requests


def generate_image_url(prompt: str, width: int = 1080, height: int = 1080) -> str:
    """
    Gera uma imagem e retorna uma URL pública pronta para o Instagram.
    O prompt deve estar em inglês para melhores resultados.
    """
    encoded = urllib.parse.quote(prompt, safe="")
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&nologo=true&model=flux&enhance=true"
    )
    # Faz o download antecipado para garantir que a imagem está cacheada
    # antes do Instagram tentar acessar a URL
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    return url


def translate_prompt_to_english(prompt_pt: str) -> str:
    """
    Converte uma descrição em português para inglês para melhores resultados
    na geração de imagens. Usado internamente pelo agente.
    """
    # O próprio agente Gemini faz essa tradução antes de chamar generate_image_url
    return prompt_pt
