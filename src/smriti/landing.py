from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>smriti — preserve your family's stories</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --cream:     #FBF5EC;
    --ink:       #1C1917;
    --muted:     #78716C;
    --gold:      #B45309;
    --gold-light:#FEF3C7;
    --wa:        #22C55E;
    --wa-dark:   #16A34A;
    --border:    #E7DDD0;
  }

  html { scroll-behavior: smooth; }

  body {
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--cream);
    color: var(--ink);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* ── NAV ── */
  nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 2rem;
    border-bottom: 1px solid var(--border);
  }
  .logo {
    font-family: 'Lora', serif;
    font-size: 1.35rem;
    font-weight: 600;
    letter-spacing: -.01em;
    color: var(--ink);
    text-decoration: none;
  }
  .logo span { color: var(--gold); }
  .nav-tag {
    font-size: .75rem;
    color: var(--muted);
    letter-spacing: .04em;
    text-transform: uppercase;
  }

  /* ── HERO ── */
  .hero {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 5rem 1.5rem 4rem;
    gap: 1.5rem;
  }
  .devanagari {
    font-family: 'Lora', 'Noto Serif Devanagari', serif;
    font-size: clamp(4rem, 14vw, 8rem);
    line-height: 1;
    color: var(--gold);
    opacity: .18;
    position: absolute;
    top: 4.5rem;
    left: 50%;
    transform: translateX(-50%);
    pointer-events: none;
    user-select: none;
    white-space: nowrap;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    background: var(--gold-light);
    color: var(--gold);
    font-size: .78rem;
    font-weight: 500;
    padding: .3rem .85rem;
    border-radius: 999px;
    letter-spacing: .02em;
  }
  .badge svg { width: 14px; height: 14px; }
  h1 {
    font-family: 'Lora', serif;
    font-size: clamp(2rem, 5vw, 3.25rem);
    line-height: 1.2;
    max-width: 640px;
    font-weight: 600;
    letter-spacing: -.02em;
  }
  h1 em { font-style: italic; color: var(--gold); }
  .sub {
    font-size: 1.05rem;
    color: var(--muted);
    max-width: 480px;
    line-height: 1.65;
  }
  .tagline {
    font-family: 'Lora', serif;
    font-size: 1.15rem;
    font-style: italic;
    color: var(--gold);
    letter-spacing: .01em;
    margin-top: -.5rem;
  }
  .cta {
    display: inline-flex;
    align-items: center;
    gap: .55rem;
    background: var(--wa);
    color: #fff;
    font-weight: 500;
    font-size: .95rem;
    padding: .8rem 1.75rem;
    border-radius: 999px;
    text-decoration: none;
    transition: background .15s, transform .1s;
    box-shadow: 0 2px 12px rgba(34,197,94,.3);
    margin-top: .5rem;
  }
  .cta:hover { background: var(--wa-dark); transform: translateY(-1px); }
  .cta svg { width: 18px; height: 18px; }

  /* ── HOW IT WORKS ── */
  .how {
    padding: 4rem 1.5rem;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
  }
  .section-label {
    text-align: center;
    font-size: .75rem;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 2.5rem;
  }
  .steps {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.5rem;
  }
  .step {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.75rem 1.5rem;
    display: flex;
    flex-direction: column;
    gap: .65rem;
  }
  .step-num {
    font-size: .72rem;
    font-weight: 500;
    color: var(--gold);
    letter-spacing: .06em;
    text-transform: uppercase;
  }
  .step h3 {
    font-family: 'Lora', serif;
    font-size: 1.05rem;
    font-weight: 600;
    line-height: 1.3;
  }
  .step p {
    font-size: .88rem;
    color: var(--muted);
    line-height: 1.6;
  }
  .step-icon {
    font-size: 1.5rem;
    margin-bottom: .25rem;
  }

  /* ── QUOTE ── */
  .quote-wrap {
    background: #fff;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 3.5rem 1.5rem;
    text-align: center;
  }
  blockquote {
    font-family: 'Lora', serif;
    font-size: clamp(1.1rem, 2.5vw, 1.45rem);
    font-style: italic;
    color: var(--ink);
    max-width: 560px;
    margin: 0 auto;
    line-height: 1.65;
  }
  blockquote cite {
    display: block;
    margin-top: 1rem;
    font-size: .82rem;
    font-style: normal;
    color: var(--muted);
    letter-spacing: .03em;
  }

  /* ── FOOTER ── */
  footer {
    padding: 1.5rem 2rem;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: .75rem;
  }
  footer p { font-size: .8rem; color: var(--muted); }
  .health-dot {
    display: inline-flex;
    align-items: center;
    gap: .35rem;
    font-size: .78rem;
    color: var(--muted);
  }
  .dot {
    width: 7px; height: 7px;
    background: var(--wa);
    border-radius: 50%;
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: .35; }
  }
</style>
</head>
<body>

<div class="devanagari">स्मृति</div>

<nav>
  <a class="logo" href="/">smriti<span>.</span></a>
  <span class="nav-tag">स्मृति &middot; memory</span>
</nav>

<section class="hero">
  <div class="badge">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.117.554 4.107 1.523 5.83L0 24l6.364-1.499A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/></svg>
    WhatsApp-native
  </div>

  <h1>Your family's stories,<br><em>preserved forever.</em></h1>

  <p class="tagline">Some memories deserve to outlive us.</p>

  <p class="sub">Every Monday, smriti sends your grandparent one gentle question on WhatsApp. Their answers become a book your family will keep for generations.</p>

  <a class="cta" href="mailto:vbajaj56@gmail.com?subject=smriti — get started">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.117.554 4.107 1.523 5.83L0 24l6.364-1.499A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/></svg>
    Get started
  </a>
</section>

<section class="how">
  <p class="section-label">How it works</p>
  <div class="steps">
    <div class="step">
      <div class="step-icon">🪔</div>
      <p class="step-num">Week 1</p>
      <h3>A question arrives</h3>
      <p>Every Monday, your grandparent receives a warm question on WhatsApp — in Hindi, English, or Punjabi.</p>
    </div>
    <div class="step">
      <div class="step-icon">🎙️</div>
      <p class="step-num">Any time</p>
      <h3>They reply their way</h3>
      <p>A voice note, a few typed words, a long story. No app to download. No account to create.</p>
    </div>
    <div class="step">
      <div class="step-icon">📖</div>
      <p class="step-num">Week 52</p>
      <h3>A book for your family</h3>
      <p>After 52 weeks, all their stories are woven into a beautifully typeset book — yours to print and keep.</p>
    </div>
  </div>
</section>

<div class="quote-wrap">
  <blockquote>
    "The stories our elders carry are not just memories — they are the roots that hold a family together."
    <cite>— the idea behind smriti</cite>
  </blockquote>
</div>

<footer>
  <p>smriti &copy; 2026 &middot; Made with love for Indian families</p>
  <span class="health-dot"><span class="dot"></span> live</span>
</footer>

</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing():
    return _PAGE
