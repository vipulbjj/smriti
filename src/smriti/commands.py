"""
WhatsApp command system for grandparents.

Grandparents can send any of these (case-insensitive) at any time:
  MENU  / मेनू  / ਮੇਨੂ    → show available commands
  AUDIO / आवाज़ / ਆਵਾਜ਼   → receive MP3 of their last story
  VIDEO / वीडियो / ਵੀਡੀਓ  → receive video card of their last story
  STORIES / कहानियाँ       → how many stories collected + timeline link
  REPEAT / दोबारा / ਦੁਬਾਰਾ → resend this week's prompt
  HELP  / मदद  / ਮਦਦ      → support message

Commands are detected before regular story processing in the webhook.
"""

import logging
from typing import Optional

from sqlmodel import desc, select

from .config import config
from .db import Grandparent, Story, Family, open_session
from .prompts import format_whatsapp_prompt, Language
from .whatsapp import send_message, send_media_message

logger = logging.getLogger(__name__)

# Multi-language command aliases
_COMMANDS: dict[str, set[str]] = {
    "menu":    {"menu", "मेनू", "ਮੇਨੂ", "help menu", "commands"},
    "audio":   {"audio", "आवाज़", "आवाज", "ਆਵਾਜ਼", "sound", "listen"},
    "video":   {"video", "वीडियो", "ਵੀਡੀਓ", "watch"},
    "stories": {"stories", "कहानियाँ", "कहानियां", "ਕਹਾਣੀਆਂ", "count", "how many"},
    "repeat":  {"repeat", "दोबारा", "ਦੁਬਾਰਾ", "resend", "again", "फिर से"},
    "help":    {"help", "मदद", "ਮਦਦ", "?", "support"},
}

_MENU = {
    "hindi": (
        "📋 *smriti कमांड्स*\n\n"
        "• *AUDIO* — अपनी आखिरी कहानी सुनें\n"
        "• *VIDEO* — अपनी कहानी का वीडियो कार्ड पाएँ\n"
        "• *STORIES* — देखें कितनी कहानियाँ हो गई हैं\n"
        "• *REPEAT* — इस हफ़्ते का सवाल दोबारा पाएँ\n"
        "• *HELP* — मदद के लिए\n\n"
        "या बस अपना जवाब लिखें या आवाज़ में भेजें। 🙏"
    ),
    "english": (
        "📋 *smriti commands*\n\n"
        "• *AUDIO* — hear your last story read aloud\n"
        "• *VIDEO* — get a story card video\n"
        "• *STORIES* — see how many memories you've shared\n"
        "• *REPEAT* — resend this week's question\n"
        "• *HELP* — get support\n\n"
        "Or just reply to this week's question by typing or voice note. 🙏"
    ),
    "punjabi": (
        "📋 *smriti ਕਮਾਂਡਜ਼*\n\n"
        "• *AUDIO* — ਆਪਣੀ ਆਖਰੀ ਕਹਾਣੀ ਸੁਣੋ\n"
        "• *VIDEO* — ਵੀਡੀਓ ਕਾਰਡ ਪ੍ਰਾਪਤ ਕਰੋ\n"
        "• *STORIES* — ਕਿੰਨੀਆਂ ਕਹਾਣੀਆਂ ਹੋਈਆਂ ਦੇਖੋ\n"
        "• *REPEAT* — ਇਸ ਹਫ਼ਤੇ ਦਾ ਸਵਾਲ ਦੁਬਾਰਾ ਪਾਓ\n"
        "• *HELP* — ਮਦਦ ਲਈ\n\n"
        "ਜਾਂ ਬੱਸ ਆਪਣਾ ਜਵਾਬ ਲਿਖੋ ਜਾਂ ਆਵਾਜ਼ ਵਿੱਚ ਭੇਜੋ। 🙏"
    ),
}

_HELP = {
    "hindi": (
        "🙏 *smriti मदद*\n\n"
        "smriti हर सोमवार को आपकी ज़िंदगी के बारे में एक सवाल भेजता है। "
        "आपके जवाब एक किताब में बदल जाते हैं जो आपके परिवार को हमेशा याद रहेगी।\n\n"
        f"कोई परेशानी हो तो: {config.webhook_base_url}"
    ),
    "english": (
        "🙏 *smriti help*\n\n"
        "smriti sends you one question every Monday about your life and memories. "
        "Your answers become a beautiful book your family will treasure forever.\n\n"
        f"For support, visit: {config.webhook_base_url}"
    ),
    "punjabi": (
        "🙏 *smriti ਮਦਦ*\n\n"
        "smriti ਹਰ ਸੋਮਵਾਰ ਤੁਹਾਡੀ ਜ਼ਿੰਦਗੀ ਬਾਰੇ ਇੱਕ ਸਵਾਲ ਭੇਜਦਾ ਹੈ। "
        "ਤੁਹਾਡੇ ਜਵਾਬ ਇੱਕ ਸੁੰਦਰ ਕਿਤਾਬ ਬਣਦੇ ਹਨ।\n\n"
        f"ਮਦਦ ਲਈ: {config.webhook_base_url}"
    ),
}

_NO_STORIES = {
    "hindi": "अभी तक कोई कहानी नहीं है। अपना पहला जवाब भेजकर शुरुआत करें! 🙏",
    "english": "No stories yet. Reply to this week's question to get started! 🙏",
    "punjabi": "ਅਜੇ ਕੋਈ ਕਹਾਣੀ ਨਹੀਂ। ਇਸ ਹਫ਼ਤੇ ਦੇ ਸਵਾਲ ਦਾ ਜਵਾਬ ਦਿਓ! 🙏",
}

_VIDEO_PROCESSING = {
    "hindi": "⏳ वीडियो अभी बन रहा है। थोड़ी देर में मिलेगा! आज शाम तक आ जाएगा।",
    "english": "⏳ Your story video is still rendering. Check back this evening!",
    "punjabi": "⏳ ਵੀਡੀਓ ਅਜੇ ਤਿਆਰ ਹੋ ਰਿਹਾ ਹੈ। ਥੋੜੀ ਦੇਰ ਵਿੱਚ ਮਿਲੇਗਾ!",
}

_STORIES_COUNT = {
    "hindi": "📖 *{name} जी की यादें*\n\n{count}/52 कहानियाँ\n{bar}\n\nटाइमलाइन देखें: {url}",
    "english": "📖 *{name}'s memories*\n\n{count}/52 stories collected\n{bar}\n\nView timeline: {url}",
    "punjabi": "📖 *{name} ਜੀ ਦੀਆਂ ਯਾਦਾਂ*\n\n{count}/52 ਕਹਾਣੀਆਂ\n{bar}\n\nਟਾਈਮਲਾਈਨ ਦੇਖੋ: {url}",
}


def _progress_bar(count: int, total: int = 52) -> str:
    filled = int((count / total) * 10)
    return "▓" * filled + "░" * (10 - filled) + f" {count}/{total}"


def detect_command(body: str) -> Optional[str]:
    """Return command key if body matches a known command, else None."""
    normalized = body.strip().lower()
    for cmd, aliases in _COMMANDS.items():
        if normalized in aliases:
            return cmd
    return None


def handle_command(cmd: str, gp: Grandparent) -> None:
    """Dispatch and respond to a WhatsApp command."""
    lang = gp.language
    phone = gp.phone

    if cmd == "menu":
        send_message(phone, _MENU.get(lang, _MENU["english"]))

    elif cmd == "help":
        send_message(phone, _HELP.get(lang, _HELP["english"]))

    elif cmd == "repeat":
        msg = format_whatsapp_prompt(gp.prompt_index, Language(lang), gp.name)
        send_message(phone, msg)

    elif cmd == "stories":
        with open_session() as session:
            count = len(session.exec(
                select(Story).where(Story.grandparent_id == gp.id)
            ).all())
            family = session.get(Family, gp.family_id)
        token = family.timeline_token if family else ""
        url = f"{config.webhook_base_url}/family/{token}" if token else config.webhook_base_url
        bar = _progress_bar(count)
        send_message(phone, _STORIES_COUNT.get(lang, _STORIES_COUNT["english"]).format(
            name=gp.name, count=count, bar=bar, url=url
        ))

    elif cmd == "audio":
        _send_audio_command(gp)

    elif cmd == "video":
        _send_video_command(gp)


def _get_latest_story(gp: Grandparent) -> Optional[Story]:
    with open_session() as session:
        return session.exec(
            select(Story)
            .where(Story.grandparent_id == gp.id)
            .order_by(desc(Story.received_at))
        ).first()


def _send_audio_command(gp: Grandparent) -> None:
    story = _get_latest_story(gp)
    if not story:
        send_message(gp.phone, _NO_STORIES.get(gp.language, _NO_STORIES["english"]))
        return
    try:
        audio_url = f"{config.webhook_base_url}/media/audio/{story.id}"
        caption = {
            "hindi": f"🎙️ आपकी कहानी — हफ़्ता {story.prompt_index + 1}/52",
            "english": f"🎙️ Your story — Week {story.prompt_index + 1}/52",
            "punjabi": f"🎙️ ਤੁਹਾਡੀ ਕਹਾਣੀ — ਹਫ਼ਤਾ {story.prompt_index + 1}/52",
        }.get(gp.language, f"Week {story.prompt_index + 1}/52")
        send_media_message(gp.phone, caption, audio_url)
        logger.info("Audio sent to %s for story %d", gp.name, story.id)
    except Exception:
        logger.exception("Failed to send audio to %s", gp.name)
        send_message(gp.phone, _NO_STORIES.get(gp.language, _NO_STORIES["english"]))


def _send_video_command(gp: Grandparent) -> None:
    story = _get_latest_story(gp)
    if not story:
        send_message(gp.phone, _NO_STORIES.get(gp.language, _NO_STORIES["english"]))
        return
    if story.video_url:
        caption = {
            "hindi": f"🎬 आपकी कहानी का वीडियो — हफ़्ता {story.prompt_index + 1}/52",
            "english": f"🎬 Your story video — Week {story.prompt_index + 1}/52",
            "punjabi": f"🎬 ਤੁਹਾਡੀ ਕਹਾਣੀ ਦਾ ਵੀਡੀਓ — ਹਫ਼ਤਾ {story.prompt_index + 1}/52",
        }.get(gp.language, f"Week {story.prompt_index + 1}/52")
        try:
            send_media_message(gp.phone, caption, story.video_url)
        except Exception:
            logger.exception("Failed to send video to %s", gp.name)
            send_message(gp.phone, story.video_url)
    else:
        send_message(gp.phone, _VIDEO_PROCESSING.get(gp.language, _VIDEO_PROCESSING["english"]))
