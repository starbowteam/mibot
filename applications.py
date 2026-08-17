import re
from typing import Any

import discord


def trim_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def build_answer_block(label: str, value: str) -> str:
    cleaned = trim_text((value or "—").strip(), limit=850)
    quoted = "\n".join(f"> {line}" for line in cleaned.splitlines() if line.strip()) or "> —"
    return f"**{label}**\n{quoted}"


def sanitize_channel_name_component(value: str, fallback: str = "user", limit: int = 24) -> str:
    cleaned = re.sub(r"[^a-z0-9а-яё_-]+", "-", (value or "").strip().lower(), flags=re.IGNORECASE)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned[:limit] or fallback


def extract_nickname_and_static(raw_value: str) -> tuple[str, str]:
    cleaned = " ".join((raw_value or "").strip().split())
    if not cleaned:
        return "Ник", "Статик"

    static_match = re.search(r"(\d{1,8})\s*$", cleaned)
    static_value = static_match.group(1) if static_match else "Статик"
    nickname_part = cleaned[: static_match.start()].strip(" |-") if static_match else cleaned
    nickname_tokens = nickname_part.split()
    nickname = nickname_tokens[0] if nickname_tokens else nickname_part or "Ник"
    return nickname[:24], static_value[:16]


def extract_legacy_irl_name(raw_value: str) -> str:
    cleaned = " ".join((raw_value or "").strip().split())
    if not cleaned:
        return ""
    cleaned = re.sub(r"\b\d{1,2}\b.*$", "", cleaned).strip(" ,|-/")
    return cleaned[:20]


def extract_static_id(raw_value: str) -> str:
    _nickname, static_value = extract_nickname_and_static(raw_value)
    return static_value


def build_asx_member_nickname(application: dict[str, Any]) -> str:
    irl_name = (application.get("irlName") or extract_legacy_irl_name(application.get("nameAge", "")) or "Имя").strip()
    static_value = extract_static_id(application.get("nameStatic", "")) or "Static-ID"
    suffix = f" | {static_value}"
    max_name_length = max(1, 32 - len("ASX | ") - len(suffix))
    return f"ASX | {irl_name[:max_name_length]}{suffix}"[:32]


# --- Новая функция для построения эмбеда заявки с полями (широкий вид) ---
def build_application_embed(application: dict[str, Any], applicant_tag: str, color: int = 0x090D14) -> discord.Embed:
    """
    Создаёт эмбед заявки в широком формате (поля, без цитирования).
    """
    embed = discord.Embed(
        title=f"Заявка #{application['id']}",
        color=color,
        timestamp=parse_iso(application.get("submittedAt")),
    )
    embed.set_author(name=applicant_tag)
    embed.set_footer(text=f"ID заявителя: {application['applicantId']}")

    # Основные поля
    embed.add_field(name="Заявитель", value=f"<@{application['applicantId']}>", inline=False)
    embed.add_field(name="Сервер", value=get_server_plain_label(application.get("server", "")), inline=False)

    # Поля анкеты
    fields_map = {
        "01. Имя IRL": application.get("irlName") or extract_legacy_irl_name(application.get("nameAge", "")) or "—",
        "02. Возраст IRL": application.get("ageIrl") or application.get("nameAge") or "—",
        "03. Левел, онлайн и часовой пояс": application.get("levelOnline") or "—",
        "04. Фракция": application.get("fraction") or "—",
        "05. Ник и Static-ID": application.get("nameStatic") or "—",
    }
    for label, value in fields_map.items():
        embed.add_field(name=label, value=value, inline=False)

    # Если заявка закреплена за рекрутером
    if application.get("claimedBy"):
        embed.add_field(name="Закреплена за", value=f"<@{application['claimedBy']}>", inline=False)

    return embed


# Вспомогательная функция (нужна для парсинга даты)
def parse_iso(value: str | None):
    from datetime import datetime, timezone
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now(timezone.utc)


# Вспомогательная функция для получения названия сервера (копия из index, чтобы не импортировать)
def get_server_plain_label(server: str) -> str:
    from config import (
        FAMQ_SERVER_FRIEND_VERIFICATION,
        FEDRU_APPLICATION_SERVER,
        FAMQ_SERVER_DENVER,
        FAMQ_SERVER_ORLANDO,
        FAMQ_SERVER_SF,
    )
    if server == FAMQ_SERVER_FRIEND_VERIFICATION:
        return "Верификация для друзей"
    if server == FEDRU_APPLICATION_SERVER:
        return "ASIXEZ RU"
    if server == FAMQ_SERVER_DENVER:
        return "Denver"
    if server == FAMQ_SERVER_ORLANDO:
        return "Orlando"
    return "San Francisco" if server == FAMQ_SERVER_SF else "Detroit"
