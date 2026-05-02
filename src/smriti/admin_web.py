"""
Admin web dashboard — GET /admin?key={ADMIN_KEY}
Shows all families, progress, stories, and quick actions.
"""

import html
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .config import config
from .db import Family, Grandparent, Story, get_family_stories, open_session
from .scheduler import send_weekly_prompts
from sqlmodel import select, func

logger = logging.getLogger(__name__)
router = APIRouter()


def _auth(request: Request) -> bool:
    key = request.query_params.get("key", "") or request.headers.get("X-Admin-Key", "")
    return bool(config.admin_key) and key == config.admin_key


def _family_card(family: Family, gps: list, stories_by_gp: dict) -> str:
    total_stories = sum(len(stories_by_gp.get(gp.id, [])) for gp in gps)
    gp_html = ""
    for gp in gps:
        stories = stories_by_gp.get(gp.id, [])
        count = len(stories)
        pct = int((count / 52) * 100)
        last = stories[-1].received_at.strftime("%b %d") if stories else "—"
        status_color = "#22C55E" if gp.active else "#94A3B8"
        status_label = "active" if gp.active else "complete"
        gp_html += f"""
        <div class="gp-row">
          <div class="gp-info">
            <div class="gp-avatar" style="background:{status_color}">{html.escape(gp.name[0])}</div>
            <div>
              <div class="gp-name">{html.escape(gp.name)}</div>
              <div class="gp-meta">{gp.language} · {status_label} · last: {last}</div>
            </div>
          </div>
          <div class="gp-right">
            <div class="prog-wrap">
              <div class="prog-bar"><div class="prog-fill" style="width:{pct}%"></div></div>
              <span class="prog-label">{count}/52</span>
            </div>
            <div class="gp-actions">
              <button class="btn-sm btn-ghost" onclick="sendPrompt({gp.id},'{html.escape(gp.name)}',this)">Send prompt</button>
              <button class="btn-sm btn-ghost" onclick="showStories({gp.id},'{html.escape(gp.name)}')">Stories</button>
            </div>
          </div>
        </div>"""

    token = family.timeline_token
    base = config.webhook_base_url
    return f"""
    <div class="card" id="family-{family.id}">
      <div class="card-header">
        <div>
          <div class="card-title">
            <span class="tier-badge">{family.tier}</span>
            {html.escape(family.grandchild_name)}'s family
          </div>
          <div class="card-sub">{family.grandchild_phone} · {total_stories} stories</div>
        </div>
        <div class="card-links">
          <a href="{base}/family/{token}" target="_blank" class="btn-sm btn-primary">Timeline ↗</a>
          <button class="btn-sm btn-ghost" onclick="genBook({family.id},this)">Gen PDF</button>
        </div>
      </div>
      {gp_html}
    </div>"""


def _render_dashboard(families_data: list) -> str:
    total_fam = len(families_data)
    total_gp = sum(len(gps) for _, gps, _ in families_data)
    total_stories = sum(
        sum(len(s) for s in sd.values())
        for _, _, sd in families_data
    )
    active_gp = sum(
        sum(1 for gp in gps if gp.active)
        for _, gps, _ in families_data
    )

    cards = "".join(
        _family_card(fam, gps, sd)
        for fam, gps, sd in families_data
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>smriti admin</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0F172A;--surface:#1E293B;--border:#334155;--text:#F1F5F9;
  --muted:#94A3B8;--gold:#F59E0B;--green:#22C55E;--blue:#3B82F6;--red:#EF4444;
  --card:#1E293B;
}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}
/* NAV */
nav{{display:flex;align-items:center;justify-content:space-between;padding:1rem 2rem;border-bottom:1px solid var(--border);background:var(--surface)}}
.logo{{font-weight:600;font-size:1.1rem;color:var(--gold)}}
.nav-right{{font-size:.8rem;color:var(--muted)}}
/* STATS */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1rem;padding:1.5rem 2rem}}
.stat{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.1rem 1.25rem}}
.stat-val{{font-size:1.75rem;font-weight:600;color:var(--text)}}
.stat-label{{font-size:.75rem;color:var(--muted);margin-top:.2rem;letter-spacing:.04em;text-transform:uppercase}}
/* TOOLBAR */
.toolbar{{padding:.75rem 2rem;display:flex;gap:.75rem;align-items:center;border-bottom:1px solid var(--border)}}
.search{{background:var(--surface);border:1px solid var(--border);color:var(--text);padding:.45rem .85rem;border-radius:8px;font-size:.85rem;width:240px;outline:none}}
.search:focus{{border-color:var(--blue)}}
/* CARDS */
.cards{{padding:1.5rem 2rem;display:flex;flex-direction:column;gap:1.25rem}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:1.25rem 1.5rem;overflow:hidden}}
.card-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;flex-wrap:wrap;gap:.75rem}}
.card-title{{font-weight:600;font-size:1rem;display:flex;align-items:center;gap:.5rem}}
.card-sub{{font-size:.78rem;color:var(--muted);margin-top:.2rem}}
.card-links{{display:flex;gap:.5rem}}
.tier-badge{{font-size:.65rem;background:rgba(245,158,11,.15);color:var(--gold);border:1px solid rgba(245,158,11,.3);padding:.15rem .5rem;border-radius:99px;font-weight:500;text-transform:uppercase;letter-spacing:.04em}}
/* GP ROW */
.gp-row{{display:flex;align-items:center;justify-content:space-between;padding:.75rem 0;border-top:1px solid var(--border);gap:1rem;flex-wrap:wrap}}
.gp-info{{display:flex;align-items:center;gap:.75rem}}
.gp-avatar{{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:.9rem;color:#fff;flex-shrink:0}}
.gp-name{{font-weight:500;font-size:.9rem}}
.gp-meta{{font-size:.75rem;color:var(--muted);margin-top:.1rem}}
.gp-right{{display:flex;align-items:center;gap:1rem;flex-wrap:wrap}}
.gp-actions{{display:flex;gap:.4rem}}
/* PROGRESS */
.prog-wrap{{display:flex;align-items:center;gap:.6rem;min-width:140px}}
.prog-bar{{flex:1;height:6px;background:var(--border);border-radius:99px;overflow:hidden}}
.prog-fill{{height:100%;background:var(--green);border-radius:99px;transition:width .4s}}
.prog-label{{font-size:.75rem;color:var(--muted);white-space:nowrap}}
/* BUTTONS */
.btn-sm{{padding:.3rem .75rem;border-radius:8px;font-size:.78rem;font-weight:500;cursor:pointer;border:none;transition:all .15s}}
.btn-primary{{background:var(--blue);color:#fff}}
.btn-primary:hover{{background:#2563EB}}
.btn-ghost{{background:transparent;color:var(--muted);border:1px solid var(--border)}}
.btn-ghost:hover{{background:var(--border);color:var(--text)}}
.btn-danger{{background:transparent;color:var(--red);border:1px solid rgba(239,68,68,.3)}}
/* MODAL */
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:100;align-items:center;justify-content:center;padding:1rem}}
.modal-overlay.open{{display:flex}}
.modal{{background:var(--surface);border:1px solid var(--border);border-radius:20px;width:100%;max-width:680px;max-height:80vh;overflow:hidden;display:flex;flex-direction:column}}
.modal-header{{padding:1.25rem 1.5rem;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}}
.modal-title{{font-weight:600}}
.modal-close{{background:none;border:none;color:var(--muted);cursor:pointer;font-size:1.25rem;line-height:1}}
.modal-body{{overflow-y:auto;padding:1.25rem 1.5rem;flex:1}}
/* STORY ITEM */
.story-item{{padding:.9rem;border:1px solid var(--border);border-radius:12px;margin-bottom:.75rem}}
.story-week{{font-size:.72rem;color:var(--gold);font-weight:500;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.35rem}}
.story-prompt{{font-size:.82rem;color:var(--muted);font-style:italic;margin-bottom:.5rem;padding-left:.6rem;border-left:2px solid var(--border)}}
.story-text{{font-size:.88rem;line-height:1.6;white-space:pre-wrap}}
.story-enhanced{{font-size:.8rem;color:var(--muted);margin-top:.4rem;font-style:italic}}
/* TOAST */
.toast{{position:fixed;bottom:1.5rem;right:1.5rem;background:var(--green);color:#fff;padding:.65rem 1.1rem;border-radius:10px;font-size:.85rem;font-weight:500;opacity:0;transform:translateY(8px);transition:all .2s;pointer-events:none;z-index:200}}
.toast.show{{opacity:1;transform:translateY(0)}}
.toast.error{{background:var(--red)}}
/* EMPTY */
.empty{{text-align:center;padding:4rem 2rem;color:var(--muted)}}
</style>
</head>
<body>

<nav>
  <span class="logo">smriti admin</span>
  <span class="nav-right">v0.3.0 · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</span>
</nav>

<div class="stats">
  <div class="stat"><div class="stat-val">{total_fam}</div><div class="stat-label">Families</div></div>
  <div class="stat"><div class="stat-val">{total_gp}</div><div class="stat-label">Grandparents</div></div>
  <div class="stat"><div class="stat-val">{active_gp}</div><div class="stat-label">Active</div></div>
  <div class="stat"><div class="stat-val">{total_stories}</div><div class="stat-label">Stories</div></div>
  <div class="stat"><div class="stat-val">{int(total_stories/max(total_gp*52,1)*100)}%</div><div class="stat-label">Completion</div></div>
</div>

<div class="toolbar">
  <input class="search" type="text" placeholder="Search families…" oninput="filterCards(this.value)">
  <button class="btn-sm btn-ghost" onclick="sendAllPrompts(this)">Send all prompts now</button>
</div>

<div class="cards" id="cards">
{"<div class='empty'>No families registered yet.</div>" if not families_data else cards}
</div>

<!-- Story modal -->
<div class="modal-overlay" id="modal">
  <div class="modal">
    <div class="modal-header">
      <span class="modal-title" id="modal-title">Stories</span>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const KEY = new URLSearchParams(location.search).get('key') || '';

function toast(msg, err=false) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (err?' error':'');
  setTimeout(() => t.className = 'toast', 2800);
}}

async function apiFetch(url, opts={{}}) {{
  const res = await fetch(url + '?key=' + encodeURIComponent(KEY), opts);
  return res;
}}

function filterCards(q) {{
  document.querySelectorAll('.card').forEach(c => {{
    c.style.display = c.textContent.toLowerCase().includes(q.toLowerCase()) ? '' : 'none';
  }});
}}

async function sendPrompt(gpId, name, btn) {{
  btn.disabled = true; btn.textContent = '…';
  const res = await apiFetch(`/admin/api/send-prompt/${{gpId}}`, {{method:'POST'}});
  const d = await res.json();
  if (res.ok) {{ toast(`Prompt sent to ${{name}}!`); btn.textContent = 'Sent ✓'; }}
  else {{ toast(d.detail || 'Failed', true); btn.disabled = false; btn.textContent = 'Send prompt'; }}
}}

async function genBook(familyId, btn) {{
  btn.disabled = true; btn.textContent = '…';
  const res = await apiFetch(`/admin/api/gen-book/${{familyId}}`, {{method:'POST'}});
  const d = await res.json();
  if (res.ok) {{ toast('Book generated! ' + (d.path||'')); btn.textContent = 'Done ✓'; }}
  else {{ toast(d.detail || 'Failed', true); btn.disabled = false; btn.textContent = 'Gen PDF'; }}
}}

async function showStories(gpId, name) {{
  document.getElementById('modal-title').textContent = name + ''s stories';
  document.getElementById('modal-body').innerHTML = '<p style="color:var(--muted)">Loading…</p>';
  document.getElementById('modal').classList.add('open');
  const res = await apiFetch(`/admin/api/stories/${{gpId}}`);
  const stories = await res.json();
  if (!stories.length) {{
    document.getElementById('modal-body').innerHTML = '<p style="color:var(--muted)">No stories yet.</p>';
    return;
  }}
  document.getElementById('modal-body').innerHTML = stories.map(s => `
    <div class="story-item">
      <div class="story-week">Week ${{s.week}} — ${{s.date}}</div>
      <div class="story-prompt">${{escHtml(s.prompt)}}</div>
      <div class="story-text">${{escHtml(s.reply)}}</div>
      ${{s.enhanced ? '<div class="story-enhanced">✨ ' + escHtml(s.enhanced) + '</div>' : ''}}
    </div>
  `).join('');
}}

function escHtml(s) {{
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

async function sendAllPrompts(btn) {{
  if (!confirm('Send prompts to ALL active grandparents now?')) return;
  btn.disabled = true; btn.textContent = '…';
  const res = await apiFetch('/admin/api/send-all-prompts', {{method:'POST'}});
  const d = await res.json();
  if (res.ok) {{ toast(`Sent ${{d.sent}} prompts!`); }}
  else {{ toast('Failed', true); }}
  btn.disabled = false; btn.textContent = 'Send all prompts now';
}}

function closeModal() {{
  document.getElementById('modal').classList.remove('open');
}}
document.getElementById('modal').addEventListener('click', e => {{
  if (e.target === e.currentTarget) closeModal();
}});
</script>
</body>
</html>"""


@router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard(request: Request):
    if not _auth(request):
        return Response(status_code=401, content="Unauthorized. Add ?key=YOUR_ADMIN_KEY")

    with open_session() as session:
        families = session.exec(select(Family)).all()
        families_data = []
        for fam in families:
            gps = session.exec(
                select(Grandparent).where(Grandparent.family_id == fam.id)
            ).all()
            stories_by_gp = {}
            for gp in gps:
                stories = session.exec(
                    select(Story)
                    .where(Story.grandparent_id == gp.id)
                    .order_by(Story.prompt_index)
                ).all()
                stories_by_gp[gp.id] = list(stories)
            families_data.append((fam, list(gps), stories_by_gp))

    return _render_dashboard(families_data)


@router.post("/admin/api/send-prompt/{gp_id}", include_in_schema=False)
def api_send_prompt(gp_id: int, request: Request):
    if not _auth(request):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    from .db import Grandparent, mark_prompted
    from .prompts import format_whatsapp_prompt
    from .whatsapp import send_message
    with open_session() as session:
        gp = session.get(Grandparent, gp_id)
        if not gp:
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        gp_data = (gp.id, gp.name, gp.phone, gp.prompt_index, gp.language)
    gp_id, name, phone, idx, lang = gp_data
    try:
        msg = format_whatsapp_prompt(idx, Language(lang), name)
        send_message(phone, msg)
        mark_prompted(gp_id)
        return {"sent": True, "name": name}
    except Exception as e:
        logger.exception("Admin send-prompt failed for %d", gp_id)
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.post("/admin/api/gen-book/{family_id}", include_in_schema=False)
def api_gen_book(family_id: int, request: Request):
    if not _auth(request):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    try:
        from .book import generate_book
        path = generate_book(family_id)
        return {"path": path}
    except Exception as e:
        logger.exception("Admin gen-book failed for family %d", family_id)
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.get("/admin/api/stories/{gp_id}", include_in_schema=False)
def api_get_stories(gp_id: int, request: Request):
    if not _auth(request):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    with open_session() as session:
        stories = session.exec(
            select(Story)
            .where(Story.grandparent_id == gp_id)
            .order_by(Story.prompt_index)
        ).all()
        return [
            {
                "week": s.prompt_index + 1,
                "date": s.received_at.strftime("%b %d, %Y"),
                "prompt": s.prompt_text,
                "reply": s.reply_text,
                "enhanced": s.enhanced_text,
                "audio_url": f"/media/audio/{s.id}",
                "video_url": s.video_url,
            }
            for s in stories
        ]


@router.post("/admin/api/send-all-prompts", include_in_schema=False)
def api_send_all_prompts(request: Request):
    if not _auth(request):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    try:
        sent = send_weekly_prompts()
        return {"sent": sent}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


# Import needed inside functions
from .db import Language
