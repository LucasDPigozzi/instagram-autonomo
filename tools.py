import json
from datetime import datetime

import database as db
import instagram as ig
import image_gen as img

TOOLS = [
    {
        "name": "generate_and_post_photo",
        "description": "Gera uma imagem com IA e publica imediatamente no feed do Instagram.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_prompt_en": {"type": "string", "description": "Descrição da imagem em INGLÊS para a IA gerar. Seja detalhado: estilo, cores, composição."},
                "caption": {"type": "string", "description": "Legenda em português com hashtags."},
            },
            "required": ["image_prompt_en", "caption"],
        },
    },
    {
        "name": "generate_and_schedule_photo",
        "description": "Gera uma imagem com IA e agenda para publicar numa data/hora específica.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_prompt_en": {"type": "string", "description": "Descrição da imagem em INGLÊS."},
                "caption": {"type": "string", "description": "Legenda em português com hashtags."},
                "scheduled_at": {"type": "string", "description": "ISO 8601, ex: 2025-06-16T18:00:00"},
            },
            "required": ["image_prompt_en", "caption", "scheduled_at"],
        },
    },
    {
        "name": "publish_photo_url",
        "description": "Publica uma foto usando uma URL que o usuário forneceu.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_url": {"type": "string"},
                "caption": {"type": "string"},
            },
            "required": ["image_url", "caption"],
        },
    },
    {
        "name": "schedule_photo_url",
        "description": "Agenda uma foto (URL fornecida pelo usuário) para data/hora específica.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_url": {"type": "string"},
                "caption": {"type": "string"},
                "scheduled_at": {"type": "string"},
            },
            "required": ["image_url", "caption", "scheduled_at"],
        },
    },
    {
        "name": "publish_reel",
        "description": "Publica um Reel com vídeo de uma URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_url": {"type": "string"},
                "caption": {"type": "string"},
            },
            "required": ["video_url", "caption"],
        },
    },
    {
        "name": "plan_week",
        "description": "Planeja e agenda automaticamente os posts da semana com base na configuração da marca. Gera imagens, cria legendas e agenda tudo.",
        "parameters": {
            "type": "object",
            "properties": {
                "theme": {"type": "string", "description": "Tema ou foco especial desta semana (opcional). Ex: lançamento de serviço, datas comemorativas."},
            },
            "required": [],
        },
    },
    {
        "name": "list_scheduled_posts",
        "description": "Lista os posts agendados.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pending", "published", "failed", "cancelled"]},
            },
        },
    },
    {
        "name": "cancel_scheduled_post",
        "description": "Cancela um post agendado.",
        "parameters": {
            "type": "object",
            "properties": {"post_id": {"type": "integer"}},
            "required": ["post_id"],
        },
    },
    {
        "name": "save_brand_config",
        "description": "Salva a configuração da marca/agência. Use quando o usuário definir identidade, tom de voz, temas ou horários preferidos.",
        "parameters": {
            "type": "object",
            "properties": {
                "agency_name":      {"type": "string", "description": "Nome da agência"},
                "tone":             {"type": "string", "description": "Tom de voz. Ex: profissional, descontraído, inspiracional"},
                "sector":           {"type": "string", "description": "Setor. Ex: agência de publicidade digital"},
                "target_audience":  {"type": "string", "description": "Público-alvo. Ex: pequenas e médias empresas"},
                "content_topics":   {"type": "string", "description": "Temas de conteúdo separados por vírgula"},
                "posting_times":    {"type": "string", "description": "Horários preferidos separados por vírgula. Ex: 08:00,12:00,18:00"},
                "visual_style":     {"type": "string", "description": "Estilo visual. Ex: minimalista, vibrante, corporativo"},
            },
            "required": [],
        },
    },
    {
        "name": "get_brand_config",
        "description": "Retorna a configuração atual da marca.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_account_metrics",
        "description": "Retorna métricas da conta (alcance, impressões, seguidores).",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["day", "week", "days_28"]},
            },
        },
    },
    {
        "name": "get_recent_posts",
        "description": "Retorna posts recentes com engajamento.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
        },
    },
    {
        "name": "get_account_info",
        "description": "Retorna informações do perfil.",
        "parameters": {"type": "object", "properties": {}},
    },
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
            # This triggers the autonomous weekly planner
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
