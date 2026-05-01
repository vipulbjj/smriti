"""
Admin CLI — manage families, grandparents, and generate books.

Usage:
  python -m smriti.admin add-family
  python -m smriti.admin list
  python -m smriti.admin stories --family-id 1
  python -m smriti.admin send-prompt --grandparent-id 1
  python -m smriti.admin generate-book --family-id 1
"""

import sys
from sqlmodel import select

from .db import Family, Grandparent, Language, SubscriptionTier, get_family_stories, init_db, open_session
from .prompts import format_whatsapp_prompt, Language as PromptLanguage
from .whatsapp import send_message
from .book import generate_book


def cmd_list():
    with open_session() as session:
        families = session.exec(select(Family)).all()
        if not families:
            print("No families registered yet.")
            return
        print(f"\n{'ID':<4} {'Grandchild':<20} {'Phone':<16} {'Tier':<12}")
        print("-" * 56)
        for f in families:
            gps = session.exec(
                select(Grandparent).where(Grandparent.family_id == f.id)
            ).all()
            print(f"{f.id:<4} {f.grandchild_name:<20} {f.grandchild_phone:<16} {f.tier}")
            for gp in gps:
                status = "active" if gp.active else "done"
                print(f"     └─ {gp.name} ({gp.phone}) — week {gp.prompt_index}/52 [{status}]")


def cmd_add_family():
    print("=== Register new family ===")
    grandchild_name = input("Grandchild's name: ").strip()
    grandchild_phone = input("Grandchild's WhatsApp number (+91...): ").strip()
    grandparent_name = input("Grandparent's name: ").strip()
    grandparent_phone = input("Grandparent's WhatsApp number (+91...): ").strip()
    lang = input("Language [hindi/english/punjabi] (default: hindi): ").strip() or "hindi"
    tier = input("Tier [whatsapp/concierge/ai_vault] (default: whatsapp): ").strip() or "whatsapp"

    with open_session() as session:
        family = Family(
            grandchild_name=grandchild_name,
            grandchild_phone=grandchild_phone,
            tier=SubscriptionTier(tier),
        )
        session.add(family)
        session.commit()
        session.refresh(family)

        gp = Grandparent(
            family_id=family.id,
            name=grandparent_name,
            phone=grandparent_phone,
            language=Language(lang),
        )
        session.add(gp)
        session.commit()
        session.refresh(gp)

    print(f"\n✓ Family registered. Family ID: {family.id}, Grandparent ID: {gp.id}")
    print(f"  Send first prompt: python -m smriti.admin send-prompt --grandparent-id {gp.id}")


def cmd_stories(family_id: int):
    pairs = get_family_stories(family_id)
    if not pairs:
        print(f"No stories found for family {family_id}")
        return
    for gp, stories in pairs:
        print(f"\n=== {gp.name} — {len(stories)} stories ===")
        for s in stories:
            print(f"\n  Week {s.prompt_index + 1}: {s.prompt_text}")
            print(f"  {s.reply_text[:200]}{'...' if len(s.reply_text) > 200 else ''}")


def cmd_send_prompt(grandparent_id: int):
    with open_session() as session:
        gp = session.get(Grandparent, grandparent_id)
        if not gp:
            print(f"Grandparent {grandparent_id} not found")
            return
        msg = format_whatsapp_prompt(gp.prompt_index, PromptLanguage(gp.language), gp.name)
        sid = send_message(gp.phone, msg)
        print(f"✓ Sent prompt {gp.prompt_index + 1}/52 to {gp.name}. SID: {sid}")


def cmd_generate_book(family_id: int):
    path = generate_book(family_id)
    print(f"✓ Book generated: {path}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0]
    kwargs = {}
    i = 1
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            key = args[i][2:].replace("-", "_")
            kwargs[key] = args[i + 1]
            i += 2
        else:
            i += 1

    init_db()

    if cmd == "list":
        cmd_list()
    elif cmd == "add-family":
        cmd_add_family()
    elif cmd == "stories":
        cmd_stories(int(kwargs.get("family_id", 0)))
    elif cmd == "send-prompt":
        cmd_send_prompt(int(kwargs.get("grandparent_id", 0)))
    elif cmd == "generate-book":
        cmd_generate_book(int(kwargs.get("family_id", 0)))
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
