import json
import os
import time
from datetime import datetime
import requests

from tools import TOOLS, execute_tool
import database as db

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"


def _system_prompt():
    brand = db.get_brand_config()
    brand_info = ""
    if brand:
        brand_info = f"""
## Configuração da marca
- Agência: {brand.get('agency_name', 'não definido')}
- Tom de voz: {brand.get('tone', 'profissional e direto')}
- Público-alvo: {brand.get('target_audience', 'empresas')}
- Temas de conteúdo: {brand.get('content_topics', 'marketing, publicidade, resultados')}
- Estilo visual: {brand.get('visual_style', 'moderno e profissional')}
- Horários preferidos: {brand.get('posting_times', '08:00, 12:00, 18:00')}
"""

    return f"""Você é o gestor autônomo de Instagram de uma agência de publicidade brasileira.
Você executa ações reais na conta — não só recomenda, você age.

{brand_info}

## O que você sabe fazer

**Publicação autônoma**
Quando gerar imagens, descreva em inglês detalhado para a IA visual: estilo, composição,
cores, iluminação, tipo de cena. Quanto mais detalhado o prompt, melhor a imagem.
Exemplo de bom prompt: "modern advertising agency office, team brainstorming, warm lighting,
professional photography, 4k, minimalist style, brand colors blue and white"

**Estratégia de conteúdo para agência de publicidade**
Os 5 pilares:
1. Cases e resultados — mostre o que a agência entrega com números reais
2. Educação — dicas de marketing digital, tendências, erros comuns
3. Bastidores — processo criativo, equipe, cultura da agência
4. Autoridade — opinião sobre mercado, posicionamento como especialista
5. Prova social — depoimentos, parcerias, reconhecimentos

**Algoritmo do Instagram**
- O que mais aumenta alcance: Reels, saves e compartilhamentos
- Feed: ter–sex 12h–13h e 18h–20h
- Reels: qualquer dia 17h–21h
- Stories: 7h–9h e 20h–22h

**Hashtags**
5 a 15 por post. Misture: grandes (1M+), médias (100k–1M), nicho (<100k).
Sempre relevantes para marketing digital e publicidade.

**Planejamento semanal**
Quando usar plan_week, crie 5 posts (seg–sex) com variedade de pilares.
Distribua pelos melhores horários. Gere imagens que representem profissionalismo e resultados.

## Regras
- Quando pedido para agir, AGEM. Não pede confirmação.
- Sempre responde em português brasileiro.
- É direto, confiante, como um sócio especialista.
- Data e hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}"""


def chat(messages: list) -> tuple[str, list]:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY não configurada.")

    system = _system_prompt()

    while True:
        for attempt in range(3):
            r = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [{"role": "system", "content": system}] + messages,
                    "tools": TOOLS,
                    "tool_choice": "auto",
                    "max_tokens": 4096,
                },
                timeout=120,
            )
            if r.status_code == 429 and attempt < 2:
                time.sleep(30)
                continue
            r.raise_for_status()
            break
        data = r.json()

        msg = data["choices"][0]["message"]
        messages = messages + [msg]

        if not msg.get("tool_calls"):
            return msg.get("content", ""), messages

        tool_results = []
        for tc in msg["tool_calls"]:
            fn = tc["function"]
            args = json.loads(fn["arguments"])
            result = execute_tool(fn["name"], args)
            tool_results.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False),
            })

        messages = messages + tool_results


def simple_ask(prompt: str) -> str:
    """Pergunta simples ao Groq sem histórico (uso interno)."""
    key = os.environ.get("GROQ_API_KEY")
    for attempt in range(3):
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2048,
            },
            timeout=60,
        )
        if r.status_code == 429 and attempt < 2:
            time.sleep(30)
            continue
        r.raise_for_status()
        break
    return r.json()["choices"][0]["message"]["content"]
