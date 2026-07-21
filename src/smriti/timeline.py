"""
Shareable family memory timeline.
GET /family/{token}  — renders all stories as a beautiful web page.
"""

import html
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

from .db import get_family_by_token, get_family_stories
from .program import SPRINT_LENGTH

router = APIRouter()


def _story_card(day: int, prompt: str, reply: str, enhanced: str, photo_url: str,
                audio_url: str, video_url: str, story_id: int) -> str:
    text = enhanced or reply
    safe_text = html.escape(text) if text else "<em>No reply yet.</em>"
    safe_prompt = html.escape(prompt)

    media_html = ""
    if photo_url:
        media_html += f'<img class="story-photo" src="{html.escape(photo_url)}" alt="photo" loading="lazy">'
    if audio_url:
        media_html += (
            f'<audio controls class="story-audio" preload="none">'
            f'<source src="{html.escape(audio_url)}" type="audio/mpeg"></audio>'
        )
    if video_url:
        media_html += (
            f'<video controls class="story-video" preload="none">'
            f'<source src="{html.escape(video_url)}" type="video/mp4"></video>'
        )

    return f"""
    <article class="card">
      <header class="card-header">
        <span class="week-badge">Day {day}</span>
      </header>
      <p class="card-prompt">{safe_prompt}</p>
      <div class="card-body">{safe_text}</div>
      {media_html}
    </article>
    """


def _render_page(family_name: str, grandchild: str, pairs: list) -> str:
    all_cards = ""
    total = 0
    for gp, stories in pairs:
        if len(pairs) > 1:
            all_cards += f'<h2 class="gp-heading">{html.escape(gp.name)}</h2>'
        for story in stories:
            total += 1
            audio_url = f"/media/audio/{story.id}"
            all_cards += _story_card(
                day=story.prompt_index + 1,
                prompt=story.prompt_text,
                reply=story.reply_text,
                enhanced=story.enhanced_text,
                photo_url=story.photo_url,
                audio_url=audio_url,
                video_url=story.video_url,
                story_id=story.id,
            )

    progress = min(100, int((total / SPRINT_LENGTH) * 100))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>smriti · {html.escape(family_name)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--cream:#FBF5EC;--ink:#1C1917;--muted:#78716C;--gold:#B45309;--border:#E7DDD0;--card:#fff}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--cream);color:var(--ink);padding:0 0 4rem}}
.top{{background:var(--ink);color:#fff;padding:1.5rem 2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.75rem}}
.top-logo{{font-family:'Lora',serif;font-size:1.2rem;color:#fff;opacity:.9}}
.top-meta{{font-size:.82rem;opacity:.6}}
.hero{{text-align:center;padding:3.5rem 1.5rem 2rem}}
.hero h1{{font-family:'Lora',serif;font-size:clamp(1.75rem,4vw,2.5rem);font-weight:600;margin-bottom:.75rem}}
.hero h1 em{{font-style:italic;color:var(--gold)}}
.hero p{{color:var(--muted);font-size:.95rem;max-width:480px;margin:0 auto 1.5rem;line-height:1.6}}
.progress-wrap{{max-width:360px;margin:0 auto}}
.progress-bar{{height:6px;background:var(--border);border-radius:99px;overflow:hidden}}
.progress-fill{{height:100%;background:var(--gold);border-radius:99px;transition:width .5s ease}}
.progress-label{{font-size:.75rem;color:var(--muted);margin-top:.4rem;text-align:right}}
.feed{{max-width:680px;margin:0 auto;padding:0 1rem;display:flex;flex-direction:column;gap:1.5rem}}
.gp-heading{{font-family:'Lora',serif;font-size:1.35rem;padding:1.5rem 0 .25rem;border-top:2px solid var(--gold);color:var(--ink)}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:1.5rem;overflow:hidden}}
.card-header{{margin-bottom:.75rem}}
.week-badge{{display:inline-block;background:var(--gold);color:#fff;font-size:.72rem;font-weight:500;padding:.2rem .65rem;border-radius:99px;letter-spacing:.04em}}
.card-prompt{{font-family:'Lora',serif;font-style:italic;color:var(--muted);font-size:.9rem;margin-bottom:1rem;line-height:1.5;padding-left:.75rem;border-left:3px solid var(--border)}}
.card-body{{font-size:.95rem;line-height:1.7;color:var(--ink);white-space:pre-wrap;word-break:break-word}}
.story-photo{{width:100%;max-height:320px;object-fit:cover;border-radius:10px;margin-top:1rem}}
.story-audio{{width:100%;margin-top:1rem;accent-color:var(--gold)}}
.story-video{{width:100%;margin-top:1rem;border-radius:10px}}
footer{{text-align:center;padding:2.5rem 1rem 0;font-size:.78rem;color:var(--muted)}}
@media(max-width:600px){{.card{{padding:1.1rem}}}}
</style>
</head>
<body>
<div class="top">
  <span class="top-logo">smriti</span>
  <span class="top-meta">A gift from {html.escape(grandchild)}</span>
</div>
<section class="hero">
  <h1>The memories of<br><em>{html.escape(family_name)}</em></h1>
  <p>{total} of {SPRINT_LENGTH} stories collected</p>
  <div class="progress-wrap">
    <div class="progress-bar"><div class="progress-fill" style="width:{progress}%"></div></div>
    <div class="progress-label">{progress}%</div>
  </div>
</section>
<div class="feed">
{all_cards}
</div>
<footer>smriti &middot; स्मृति &middot; memory &middot; made with love</footer>
</body>
</html>"""


@router.get("/family/{token}", response_class=HTMLResponse, include_in_schema=False)
def family_timeline(token: str):
    family = get_family_by_token(token)
    if not family:
        return Response(status_code=404, content="Timeline not found.")
    pairs = get_family_stories(family.id)
    if not pairs:
        return HTMLResponse("<h2>No stories yet.</h2>", status_code=200)
    gp_names = " & ".join(gp.name for gp, _ in pairs)
    return _render_page(gp_names, family.grandchild_name, pairs)
