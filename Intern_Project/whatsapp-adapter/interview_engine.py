"""
Interview engine: drives the Capture -> Structure flow over WhatsApp.
Call `handle_incoming_voice_answer` from your webhook's audio message handler.
Call `start_interview` when a new user messages you for the first time.
"""

import logging
import httpx

from question_bank import get_question, get_question_count, get_next_milestone, MILESTONES
from state_store import (
    get_state, create_state, save_answer, advance_question,
    advance_milestone, get_milestone_answers,
)
from whatsapp_meta import send_message, download_media

logger = logging.getLogger("interview_engine")

WHISPER_URL = "https://bajajlakshit-whisper.hf.space/transcribe"

# TODO: replace with your actual LLM call (Groq/OpenAI) for chapter structuring.
STRUCTURE_ENDPOINT = None  # e.g. "https://api.groq.com/openai/v1/chat/completions"


async def start_interview(wa_id: str, lang: str = "hi"):
    """Call this when a user first messages the bot (no existing state)."""
    first_milestone = MILESTONES[0]
    create_state(wa_id, lang, first_milestone)
    question = get_question(first_milestone, 0, lang)
    await send_message(wa_id, question)
    logger.info(f"Started interview for {wa_id}, milestone={first_milestone}")


async def handle_incoming_voice_answer(wa_id: str, media_id: str):
    """Call this from your webhook when an audio message arrives."""
    state = get_state(wa_id)
    if not state:
        # No interview in progress — treat as a fresh start
        await start_interview(wa_id)
        return

    # 1. Download and transcribe the answer
    try:
        audio_bytes, mime_type = await download_media(media_id)
    except Exception as e:
        logger.error(f"Audio download failed for {wa_id}: {e}")
        await send_message(wa_id, "Sorry, I couldn't download your voice note. Please try again.")
        return

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            files = {"file": ("answer.ogg", audio_bytes, mime_type or "audio/ogg")}
            resp = await client.post(WHISPER_URL, files=files)
            resp.raise_for_status()
            result = resp.json()
            transcription = result.get("text") or result.get("transcription", "")
    except Exception as e:
        logger.error(f"Whisper call failed for {wa_id}: {e}")
        await send_message(wa_id, "Sorry, I had trouble understanding that. Could you send it again?")
        return

    # 2. Save the answer against the current milestone/question
    milestone = state["current_milestone"]
    q_index = state["current_question_index"]
    save_answer(wa_id, milestone, q_index, transcription)
    logger.info(f"Saved answer for {wa_id}, milestone={milestone}, q={q_index}")

    # 3. Move to next question, or wrap up the milestone
    advance_question(wa_id)
    next_q_index = q_index + 1
    lang = state["lang"]
    next_question = get_question(milestone, next_q_index, lang)

    if next_question:
        await send_message(wa_id, next_question)
    else:
        # Milestone complete — trigger structuring, then move to next milestone
        await send_message(wa_id, "Thank you for sharing that! Let me note it all down... 📝")
        await structure_milestone(wa_id, milestone)

        next_milestone = get_next_milestone(milestone)
        advance_milestone(wa_id, next_milestone)

        if next_milestone:
            first_q = get_question(next_milestone, 0, lang)
            await send_message(wa_id, first_q)
        else:
            await send_message(wa_id, "That's everything for now — thank you for sharing your memories with me! 💛")


async def structure_milestone(wa_id: str, milestone: str):
    """
    Takes raw answers for a milestone and turns them into a cohesive chapter.
    Placeholder for now — wire up your LLM call here (Groq/OpenAI).
    """
    raw_answers = get_milestone_answers(wa_id, milestone)
    combined_text = "\n\n".join(raw_answers)

    if not STRUCTURE_ENDPOINT:
        logger.info(f"[STRUCTURE STUB] {wa_id} / {milestone}:\n{combined_text}")
        # TODO: replace this stub with an actual LLM call once STRUCTURE_ENDPOINT is set,
        # and persist the resulting chapter text (e.g. to the same SQLite DB or Supabase).
        return

    # Example shape for a real call — adjust to your chosen LLM provider:
    # async with httpx.AsyncClient(timeout=60) as client:
    #     resp = await client.post(STRUCTURE_ENDPOINT, json={...})
    #     chapter_text = resp.json()[...]
    #     save_chapter(wa_id, milestone, chapter_text)
