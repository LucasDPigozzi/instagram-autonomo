import json
from datetime import datetime

import database as db
import instagram as ig
import image_gen as img


def _tool(name, description, properties, required=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


TOOLS = [
    _tool(
        "generate_and_post_photo",
        "Gera uma imagem com IA e publica imediatamente no feed do Instagram.",
        {
            "image_prompt_en": {"type": "string", "description": "Descrição da imagem em INGLÊS para a IA gerar. Seja detalhado: estilo, cores, composição."},
            "caption": {"type": "string", "description": "Legenda em português com hashtags."},
        },
        ["image_prompt_en", "caption"],
    ),
    _tool(
        "generate_and_schedule_photo",
        "Gera uma imagem com IA e agenda para publicar numa data/hora específica.",
        {
            "image_prompt_en": {"type": "string", "description": "Descrição da imagem em INGLÊS."},
            "caption": {"type": "string", "description": "Legenda em português com hashtags."},
            "scheduled_at": {"type": "string", "description": "ISO 8601, ex: 2025-06-16T18:00:00"},
        },
        ["image_prompt_en", "caption", "scheduled_at"],
    ),
    _tool(
        "publish_photo_url",
        "Publica uma foto usando uma URL que o usuário forneceu.",
        {
            "image_url": {"type": "string"},
            "caption": {"type": "string"},
        },
        ["image_url", "caption"],
    ),
    _tool(
        "schedule_photo_url",
        "Agenda uma foto (URL fornecida pelo usuário) para data/hora específica.",
        {
            "image_url": {"type": "string"},
            "caption": {"type": "string"},
            "scheduled_at": {"type": "string"},
        },
        ["image_url", "caption", "scheduled_at"],
    ),
    _tool(
        "publish_reel",
        "Publica um Reel com vídeo de uma URL.",
        {
            "video_url": {"type": "string"},
            "caption": {"type": "string"},
        },
        ["video_url", "caption"],
    ),
    _tool(
        "plan_week",
        "Planeja e agenda automaticamente os posts da semana com base na configuração da marca. Gera imagens, cria legendas e agenda tudo.",
        {
            "theme": {"type": "string", "description": "Tema ou foco especial desta semana (opcional). Ex: lançamento de serviço, datas comemorativas."},
        },
    ),
    _tool(
        "list_scheduled_posts",
        "Lista os posts agendados.",
        {
            "status": {"type": "string", "enum": ["pending", "published", "failed", "cancelled"]},
        },
    ),
    _tool(
        "cancel_scheduled_post",
        "Cancela um post agendado.",
        {"post_id": {"type": "integer"}},
        ["post_id"],
    ),
    _tool(
        "save_brand_config",
        "Salva a configuração da marca/agência. Use quando o usuário definir identidade, tom de voz, temas ou horários preferidos.",
        {
            "agency_name":     {"type": "string", "description": "Nome da agência"},
            "tone":            {"type": "string", "description": "Tom de voz. Ex: profissional, descontraído, inspiracional"},
            "sector":          {"type": "string", "description": "Setor. Ex: agência de publicidade digital"},
            "target_audience": {"type": "string", "description": "Público-alvo. Ex: pequenas e médias empresas"},
            "content_topics":  {"type": "string", "description": "Temas de conteúdo separados por vírgula"},
            "posting_times":   {"type": "string", "description": "Horários preferidos separados por vírgula. Ex: 08:00,12:00,18:00"},
            "visual_style":    {"type": "string", "description": "Estilo visual. Ex: minimalista, vibrante, corporativo"},
        },
    ),
    _tool(
        "get_brand_config",
        "Retorna a configuração atual da marca.",
        {},
    ),
    _tool(
        "get_account_metrics",
        "Retorna métricas da conta (alcance, impressões, seguidores).",
        {
            "period": {"type": "string", "enum": ["day", "week", "days_28"]},
        },
    ),
    _tool(
        "get_recent_posts",
        "Retorna posts recentes com engajamento.",
        {"limit": {"type": "integer"}},
    ),
    _tool(
        "get_account_info",
        "Retorna informações do perfil.",
        {},
    ),
]


def execute_tool(name: str, inputs: dict) -> dict:
    try:
        if name == "generate_and_post_photo":
            url = img.generate_image_url(inputs["image_prompt_en"])
            media_id = ig.post_photo(url, inputs["caption"])
            return {"success": True, "media_id": media_id, "image_url": url}

        if name == "generate_and_schedule_photo":
            url = img.generate_image_url(inputs["image_prompt_en"])
            post_id = db.add_post("PHOTO", url, inputs["caption"], inputs["scheduled_at"], inputs["image_prompt_en"])
            return {"success": True, "post_id": post_id, "image_url": url, "scheduled_at": inputs["scheduled_at"]}

        if name == "publish_photo_url":
            media_id = ig.post_photo(inputs["image_url"], inputs["caption"])
            return {"success": True, "media_id": media_id}

        if name == "schedule_photo_url":
            post_id = db.add_post("PHOTO", inputs["image_url"], inputs["caption"], inputs["scheduled_at"])
            return {"success": True, "post_id": post_id}

        if name == "publish_reel":
            media_id = ig.post_reel(inputs["video_url"], inputs["caption"])
            return {"success": True, "media_id": media_id}

        if name == "plan_week":
            from autonomous import plan_and_schedule_week
            result = plan_and_schedule_week(theme=inputs.get("theme", ""))
            return result

        if name == "list_scheduled_posts":
            return db.list_posts(inputs.get("status"))

        if name == "cancel_scheduled_post":
            ok = db.cancel_post(inputs["post_id"])
            return {"success": ok}

        if name == "save_brand_config":
            db.set_brand_config({k: v for k, v in inputs.items() if v})
            return {"success": True}

        if name == "get_brand_config":
            return db.get_brand_config()

        if name == "get_account_metrics":
            return ig.get_account_insights(inputs.get("period", "week"))

        if name == "get_recent_posts":
            return ig.get_recent_media(inputs.get("limit", 10))

        if name == "get_account_info":
            return ig.get_account_info()

        return {"error": f"Ferramenta desconhecida: {name}"}

    except Exception as e:
        return {"error": str(e)}
