"""
SQLite-based state store for tracking each grandparent's interview progress.

NOTE: HuggingFace Spaces free-tier disk is ephemeral — it resets on restart/redeploy.
This is fine for early testing but state WILL be lost if the Space sleeps and restarts.
Migrate to Supabase/Postgres before onboarding real users for anything long-running.
"""

import os
import sqlite3
import json
from contextlib import contextmanager

DB_PATH = os.path.join(os.environ.get("SMRITI_DB_DIR", "/tmp"), "smriti_state.db")


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interview_state (
                wa_id TEXT PRIMARY KEY,
                lang TEXT DEFAULT 'hi',
                current_milestone TEXT,
                current_question_index INTEGER DEFAULT 0,
                answers_json TEXT DEFAULT '{}'
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def get_state(wa_id: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT wa_id, lang, current_milestone, current_question_index, answers_json "
            "FROM interview_state WHERE wa_id = ?",
            (wa_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "wa_id": row[0],
            "lang": row[1],
            "current_milestone": row[2],
            "current_question_index": row[3],
            "answers": json.loads(row[4]),
        }


def create_state(wa_id: str, lang: str, first_milestone: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO interview_state "
            "(wa_id, lang, current_milestone, current_question_index, answers_json) "
            "VALUES (?, ?, ?, 0, '{}')",
            (wa_id, lang, first_milestone),
        )
        conn.commit()


def save_answer(wa_id: str, milestone: str, question_index: int, answer_text: str):
    state = get_state(wa_id)
    if not state:
        return
    answers = state["answers"]
    answers.setdefault(milestone, {})[str(question_index)] = answer_text
    with get_conn() as conn:
        conn.execute(
            "UPDATE interview_state SET answers_json = ? WHERE wa_id = ?",
            (json.dumps(answers), wa_id),
        )
        conn.commit()


def advance_question(wa_id: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE interview_state SET current_question_index = current_question_index + 1 "
            "WHERE wa_id = ?",
            (wa_id,),
        )
        conn.commit()


def advance_milestone(wa_id: str, next_milestone: str | None):
    with get_conn() as conn:
        conn.execute(
            "UPDATE interview_state SET current_milestone = ?, current_question_index = 0 "
            "WHERE wa_id = ?",
            (next_milestone, wa_id),
        )
        conn.commit()


def get_milestone_answers(wa_id: str, milestone: str) -> list[str]:
    """Returns ordered list of answer texts for a given milestone."""
    state = get_state(wa_id)
    if not state:
        return []
    milestone_answers = state["answers"].get(milestone, {})
    # sort by question index to preserve order
    ordered = sorted(milestone_answers.items(), key=lambda kv: int(kv[0]))
    return [text for _, text in ordered]
