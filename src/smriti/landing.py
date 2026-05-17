from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>smriti — preserve your memories</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%233B2C8F'/><text x='16' y='24' font-size='20' font-weight='bold' text-anchor='middle' fill='%23F0C84A' font-family='Georgia,serif'>&#x938;</text></svg>">
<link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%233B2C8F'/><text x='16' y='24' font-size='20' font-weight='bold' text-anchor='middle' fill='%23F0C84A' font-family='Georgia,serif'>&#x938;</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    /* Surfaces */
    --page:         #F9F6F1;
    --surface:      #FFFFFF;

    /* Typography */
    --ink:          #18102E;
    --muted:        #524770;
    --faint:        #8B82A0;

    /* Brand — deep indigo */
    --indigo:       #3B2C8F;
    --indigo-dk:    #291E6A;
    --indigo-lt:    #5848B4;
    --indigo-bg:    #EDEAF8;
    --indigo-glow:  rgba(59,44,143,.14);

    /* Warm accent — antique gold */
    --gold:         #C98B28;
    --gold-dk:      #A5701E;
    --gold-bg:      #FDF6E3;

    /* Layout */
    --border:       #DDD7EE;

    /* WhatsApp */
    --wa:           #25D366;
    --wa-dark:      #128C7E;

    /* Shadows — cool-warm indigo base */
    --sh-sm:  0 1px 6px rgba(26,18,48,.07);
    --sh-md:  0 4px 24px rgba(26,18,48,.10);
    --sh-lg:  0 12px 48px rgba(26,18,48,.14);
  }

  html { scroll-behavior: smooth; }

  body {
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--page);
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
    padding: 1.25rem 2.5rem;
    border-bottom: 1px solid var(--border);
    background: rgba(249,246,241,.88);
    backdrop-filter: blur(10px);
    position: sticky;
    top: 0;
    z-index: 10;
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
    color: var(--faint);
    letter-spacing: .05em;
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
    padding: 6rem 1.5rem 5rem;
    gap: 1.5rem;
    position: relative;
    overflow: hidden;
    background:
      radial-gradient(ellipse 80% 60% at 50% -10%, rgba(59,44,143,.09) 0%, transparent 70%),
      radial-gradient(ellipse 60% 50% at 100% 100%, rgba(201,139,40,.07) 0%, transparent 60%),
      var(--page);
  }
  .devanagari {
    font-family: 'Lora', 'Noto Serif Devanagari', serif;
    font-size: clamp(5rem, 18vw, 11rem);
    line-height: 1;
    color: var(--indigo);
    opacity: .06;
    position: absolute;
    top: 3.5rem;
    left: 50%;
    transform: translateX(-50%);
    pointer-events: none;
    user-select: none;
    white-space: nowrap;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    background: var(--indigo-bg);
    color: var(--indigo-dk);
    border: 1px solid rgba(59,44,143,.20);
    font-size: .78rem;
    font-weight: 600;
    padding: .35rem 1rem;
    border-radius: 999px;
    letter-spacing: .03em;
    box-shadow: var(--sh-sm);
  }
  .badge svg { width: 14px; height: 14px; flex-shrink: 0; }
  h1 {
    font-family: 'Lora', serif;
    font-size: clamp(2.6rem, 6vw, 4rem);
    line-height: 1.12;
    max-width: 660px;
    font-weight: 600;
    letter-spacing: -.025em;
  }
  h1 em { font-style: italic; color: var(--indigo); }
  .tagline {
    font-family: 'Lora', serif;
    font-size: 1.15rem;
    font-style: italic;
    color: var(--muted);
    letter-spacing: .01em;
    margin-top: -.3rem;
  }
  .sub {
    font-size: 1.05rem;
    color: var(--muted);
    max-width: 500px;
    line-height: 1.75;
  }
  .cta-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    justify-content: center;
    margin-top: .35rem;
  }
  .cta {
    display: inline-flex;
    align-items: center;
    gap: .6rem;
    background: var(--wa);
    color: #fff;
    font-weight: 600;
    font-size: .95rem;
    padding: .85rem 2rem;
    border-radius: 999px;
    text-decoration: none;
    transition: background .15s, transform .12s, box-shadow .15s;
    box-shadow: 0 4px 18px rgba(37,211,102,.35);
    letter-spacing: .01em;
  }
  .cta:hover {
    background: var(--wa-dark);
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(37,211,102,.40);
  }
  .cta svg { width: 18px; height: 18px; }
  .cta-note {
    font-size: .8rem;
    color: var(--faint);
  }

  /* ── SECTION SHARED ── */
  .section-label {
    text-align: center;
    font-size: .72rem;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--indigo);
    font-weight: 600;
    margin-bottom: 2.75rem;
  }

  /* ── AUDIENCES ── */
  .audiences-section {
    padding: 5rem 1.5rem 3.5rem;
    max-width: 1040px;
    margin: 0 auto;
    width: 100%;
  }
  .audiences {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
    gap: 1.5rem;
  }
  .aud-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2.25rem 2rem;
    display: flex;
    flex-direction: column;
    gap: .65rem;
    box-shadow: var(--sh-sm);
    transition: box-shadow .2s, transform .2s;
  }
  .aud-card:hover {
    box-shadow: var(--sh-md);
    transform: translateY(-3px);
  }
  .aud-icon {
    font-size: 2rem;
    margin-bottom: .1rem;
    line-height: 1;
  }
  .aud-card h3 {
    font-family: 'Lora', serif;
    font-size: 1.2rem;
    font-weight: 600;
    line-height: 1.3;
  }
  .aud-subtitle {
    font-size: .71rem;
    font-weight: 600;
    color: var(--indigo-lt);
    letter-spacing: .09em;
    text-transform: uppercase;
    margin-top: -.25rem;
  }
  .aud-card p {
    font-size: .9rem;
    color: var(--muted);
    line-height: 1.7;
    margin-top: .15rem;
  }
  .aud-examples {
    display: flex;
    flex-wrap: wrap;
    gap: .4rem;
    margin-top: .5rem;
  }
  .aud-tag {
    font-size: .71rem;
    background: var(--indigo-bg);
    color: var(--indigo-dk);
    border: 1px solid rgba(59,44,143,.16);
    border-radius: 999px;
    padding: .22rem .7rem;
    font-weight: 500;
  }

  /* ── HOW IT WORKS ── */
  .how {
    background: linear-gradient(160deg, #F0EDF8 0%, #E6E0F4 100%);
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 5rem 1.5rem;
  }
  .how-inner {
    max-width: 960px;
    margin: 0 auto;
  }
  .steps {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1.5rem;
  }
  .step {
    background: rgba(255,255,255,.80);
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 20px;
    padding: 2rem 1.75rem;
    display: flex;
    flex-direction: column;
    gap: .65rem;
    box-shadow: var(--sh-sm);
    backdrop-filter: blur(4px);
    transition: box-shadow .2s, transform .2s;
  }
  .step:hover {
    box-shadow: var(--sh-md);
    transform: translateY(-2px);
  }
  .step-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: var(--indigo);
    color: #fff;
    border-radius: 50%;
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .02em;
    flex-shrink: 0;
    margin-bottom: .1rem;
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
    line-height: 1.65;
  }
  .step-icon { font-size: 1.5rem; line-height: 1; }

  /* ── LANG STRIP ── */
  .lang-strip {
    padding: 1.25rem 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: .5rem 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }
  .lang-strip span {
    font-size: .8rem;
    color: var(--muted);
    letter-spacing: .02em;
  }
  .lang-script {
    font-family: 'Lora', serif;
    color: var(--indigo);
  }
  .sep { color: var(--border); font-weight: 300; }

  /* ── QUOTE ── */
  .quote-wrap {
    padding: 5rem 1.5rem;
    text-align: center;
    position: relative;
  }
  .quote-mark {
    font-family: 'Lora', serif;
    font-size: 6rem;
    line-height: .8;
    color: var(--gold);
    opacity: .30;
    display: block;
    margin-bottom: -1.5rem;
    user-select: none;
  }
  blockquote {
    font-family: 'Lora', serif;
    font-size: clamp(1.1rem, 2.5vw, 1.45rem);
    font-style: italic;
    color: var(--ink);
    max-width: 620px;
    margin: 0 auto;
    line-height: 1.75;
  }
  blockquote cite {
    display: block;
    margin-top: 1.25rem;
    font-size: .82rem;
    font-style: normal;
    color: var(--faint);
    letter-spacing: .04em;
    font-family: 'Inter', sans-serif;
  }

  /* ── FOOTER ── */
  footer {
    padding: 1.5rem 2.5rem;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: .75rem;
    background: var(--surface);
  }
  footer p { font-size: .8rem; color: var(--faint); }
  .health-dot {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    font-size: .78rem;
    color: var(--faint);
  }
  .dot {
    width: 7px; height: 7px;
    background: var(--wa);
    border-radius: 50%;
    animation: pulse 2.5s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: .4; transform: scale(.85); }
  }

  @media (max-width: 600px) {
    nav { padding: 1rem 1.25rem; }
    .hero { padding: 4.5rem 1.25rem 3.5rem; }
    .cta-row { flex-direction: column; gap: .65rem; }
    footer { flex-direction: column; align-items: flex-start; }
    .audiences-section { padding: 3.5rem 1rem 2.5rem; }
  }
</style>
</head>
<body>

<div class="devanagari" aria-hidden="true">स्मृति</div>

<nav>
  <a class="logo" href="/">smriti<span>.</span></a>
  <span class="nav-tag">स्मृति &middot; memory</span>
</nav>

<section class="hero">
  <div class="badge">
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.117.554 4.107 1.523 5.83L0 24l6.364-1.499A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/></svg>
    WhatsApp-native &middot; Made for India
  </div>

  <h1>For the memories<br><em>you never want to lose.</em></h1>

  <p class="tagline">Some memories deserve to outlive the moment.</p>

  <p class="sub">Your dadi's stories. Your college friendships. Your child growing up. Every week smriti asks a gentle question on WhatsApp — just reply with a voice note or a few words.</p>

  <div class="cta-row">
    <a class="cta" href="mailto:vbajaj56@gmail.com?subject=smriti — get started">
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.117.554 4.107 1.523 5.83L0 24l6.364-1.499A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/></svg>
      Start preserving
    </a>
    <span class="cta-note">No app needed &middot; Just WhatsApp</span>
  </div>
</section>

<!-- Audiences -->
<section class="audiences-section">
  <p class="section-label">What smriti captures</p>
  <div class="audiences">

    <div class="aud-card">
      <div class="aud-icon">🪔</div>
      <h3>Dadi ke kissey</h3>
      <p class="aud-subtitle">Family history</p>
      <p>Partition memories. Migration stories. How your family came to be. Recipes only she knows. The history that lives in one person's voice — and disappears when it's gone.</p>
      <div class="aud-examples">
        <span class="aud-tag">Grandparents</span>
        <span class="aud-tag">Family lore</span>
        <span class="aud-tag">Recipes</span>
      </div>
    </div>

    <div class="aud-card">
      <div class="aud-icon">🎓</div>
      <h3>Apni yaadein</h3>
      <p class="aud-subtitle">Your nostalgia</p>
      <p>College hostel nights. The friend group that changed you. First heartbreaks, road trips, the moments that still make you smile years later. Your story, properly told.</p>
      <div class="aud-examples">
        <span class="aud-tag">College days</span>
        <span class="aud-tag">School friendships</span>
        <span class="aud-tag">Milestones</span>
      </div>
    </div>

    <div class="aud-card">
      <div class="aud-icon">👶</div>
      <h3>Unka bachpan</h3>
      <p class="aud-subtitle">Your children</p>
      <p>They grow up faster than you think. Their first words, the things they say that break your heart with love, the small moments you want to hold onto forever.</p>
      <div class="aud-examples">
        <span class="aud-tag">First words</span>
        <span class="aud-tag">Childhood</span>
        <span class="aud-tag">Growing up</span>
      </div>
    </div>

  </div>
</section>

<!-- How it works -->
<section class="how">
  <div class="how-inner">
    <p class="section-label">How it works</p>
    <div class="steps">
      <div class="step">
        <div class="step-icon">💛</div>
        <div class="step-badge">1</div>
        <h3>You gift it to them</h3>
        <p>The grandchild signs up smriti for their grandparent. No app to install on either side — just a WhatsApp number and a name.</p>
      </div>
      <div class="step">
        <div class="step-icon">✨</div>
        <div class="step-badge">2</div>
        <h3>One question, every week</h3>
        <p>smriti sends a gentle prompt to the grandparent on WhatsApp — in Hindi, Punjabi, or English. They just reply with a voice note or a few words.</p>
      </div>
      <div class="step">
        <div class="step-icon">🗂️</div>
        <div class="step-badge">3</div>
        <h3>A living archive grows</h3>
        <p>Every memory is saved, AI-enhanced, and turned into a private timeline — shareable with family, and yours to keep as a book and video forever.</p>
      </div>
    </div>
  </div>
</section>

<!-- Language strip -->
<div class="lang-strip">
  <span class="lang-script">हिन्दी</span>
  <span class="sep">&middot;</span>
  <span class="lang-script">ਪੰਜਾਬੀ</span>
  <span class="sep">&middot;</span>
  <span>English</span>
  <span class="sep">&middot;</span>
  <span>Hinglish</span>
  <span class="sep">&middot;</span>
  <span class="lang-script">বাংলা</span>
  <span class="sep">&middot;</span>
  <span class="lang-script">தமிழ்</span>
  <span class="sep">&middot;</span>
  <span>and more</span>
</div>

<!-- Quote -->
<div class="quote-wrap">
  <span class="quote-mark" aria-hidden="true">"</span>
  <blockquote>
    "Remember the story dadi told at the last family gathering?<br>
    You don't. Neither do we.<br>
    That's why we built smriti."
    <cite>— the idea behind smriti</cite>
  </blockquote>
</div>

<footer>
  <p>smriti &copy; 2026 &middot; Made with love for India</p>
  <span class="health-dot"><span class="dot"></span> live</span>
</footer>

</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing():
    return _PAGE
