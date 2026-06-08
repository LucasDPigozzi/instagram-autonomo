"""
Lógica autônoma: planejamento semanal, postagem diária e relatórios.
Chamado pelo scheduler sem intervenção humana.
"""

import json
import logging
from datetime import datetime, timedelta

import agent
import database as db
import image_gen as img
import instagram as ig

logger = logging.getLogger(__name__)

WEEKDAYS_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]


def plan_and_schedule_week(theme: str = "") -> dict:
    """
    Gera e agenda o conteúdo da semana inteira automaticamente.
    Chamado toda segunda-feira às 8h ou quando o usuário pede.
    """
    brand = db.get_brand_config()
    agency = brand.get("agency_name", "agência de publicidade")
    tone = brand.get("tone", "profissional e direto")
    topics = brand.get("content_topics", "marketing digital, publicidade, cases, tendências")
    style = brand.get("visual_style", "moderno, minimalista, profissional")
    times = [t.strip() for t in brand.get("posting_times", "12:00,18:00").split(",")]

    theme_line = f"Tema especial desta semana: {theme}." if theme else ""

    prompt = f"""Você é um estrategista de conteúdo para Instagram de uma agência de publicidade chamada "{agency}".

{theme_line}

Tom de voz: {tone}
Temas disponíveis: {topics}
Estilo visual: {style}

Crie um plano de 5 posts para esta semana (segunda a sexta).
Para cada post, retorne um objeto JSON com exatamente estes campos:
- "day_offset": número de dias a partir de hoje (0=hoje, 1=amanhã, etc.)
- "hour": hora de publicação no formato "HH:MM" (use horários: {', '.join(times)})
- "pillar": pilar de conteúdo (cases, educação, bastidores, autoridade, prova_social)
- "caption_pt": legenda completa em português com hashtags (máx 2200 caracteres)
- "image_prompt_en": descrição detalhada da imagem em INGLÊS para IA gerar (seja visual e específico, mencione estilo fotográfico, cores, composição)

Responda APENAS com um array JSON válido, sem markdown, sem explicações."""

    try:
        raw = agent.simple_ask(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        plan = json.loads(raw.strip())
    except Exception as e:
        logger.error("Erro ao parsear plano semanal: %s", e)
        return {"error": f"Não foi possível gerar o plano: {e}"}

    scheduled = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for item in plan:
        try:
            day_offset = int(item.get("day_offset", 0))
            post_date = today + timedelta(days=day_offset)
            hour, minute = item["hour"].split(":")
            post_dt = post_date.replace(hour=int(hour), minute=int(minute))
            scheduled_at = post_dt.strftime("%Y-%m-%dT%H:%M:%S")

            # Generate image
            image_url = img.generate_image_url(item["image_prompt_en"])

            post_id = db.add_post(
                "PHOTO",
                image_url,
                item["caption_pt"],
                scheduled_at,
                item["image_prompt_en"],
            )
            scheduled.append({
                "post_id": post_id,
                "scheduled_at": scheduled_at,
                "pillar": item.get("pillar"),
            })
            logger.info("Post %d agendado para %s", post_id, scheduled_at)

        except Exception as e:
            logger.error("Erro ao agendar item do plano: %s — %s", item, e)

    return {
        "success": True,
        "posts_scheduled": len(scheduled),
        "schedule": scheduled,
    }


def publish_pending_posts():
    """Publica todos os posts pendentes cujo horário já chegou. Roda a cada minuto."""
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    posts = db.get_pending_posts(before=now)

    for post in posts:
        try:
            if post["media_type"] == "PHOTO":
                ig.post_photo(post["media_url"], post["caption"] or "")
            elif post["media_type"] == "REEL":
                ig.post_reel(post["media_url"], post["caption"] or "")
            elif post["media_type"] == "STORY_IMAGE":
                ig.post_story_image(post["media_url"])

            db.update_post_status(
                post["id"],
                "published",
                published_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            )
            logger.info("Post %d publicado com sucesso.", post["id"])

        except Exception as e:
            logger.error("Erro ao publicar post %d: %s", post["id"], e)
            db.update_post_status(post["id"], "failed", error=str(e))


def generate_weekly_report() -> str:
    """Gera relatório de métricas da semana. Roda todo domingo às 18h."""
    try:
        metrics = ig.get_account_insights("week")
        recent = ig.get_recent_media(7)
        brand = db.get_brand_config()

        prompt = f"""Analise as métricas da semana do Instagram da agência "{brand.get('agency_name', 'agência')}":

Métricas da conta:
{json.dumps(metrics, indent=2)}

Posts recentes (últimos 7):
{json.dumps(recent, indent=2)}

Escreva um relatório executivo em português com:
1. Resumo do desempenho (2-3 linhas)
2. O que funcionou bem
3. O que precisa melhorar
4. 3 recomendações para a próxima semana

Seja direto e baseado nos dados."""

        report = agent.simple_ask(prompt)
        logger.info("Relatório semanal gerado com sucesso.")
        return report

    except Exception as e:
        logger.error("Erro ao gerar relatório: %s", e)
        return f"Erro ao gerar relatório: {e}"
