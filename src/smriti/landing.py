from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>smriti — preserve their stories</title>
<meta name="description" content="Seven questions. Seven days. A lifetime of stories preserved — in your grandparent's own voice, on WhatsApp.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%2312080E'/><text x='16' y='24' font-size='20' font-weight='bold' text-anchor='middle' fill='%23C4933F' font-family='Georgia,serif'>&#x938;</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400;1,600&family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --ink:     #12080E;
  --ink2:    #1C1018;
  --ivory:   #F5EFE3;
  --ivory2:  #FAF6EF;
  --gold:    #C4933F;
  --gold-lt: #E0B86A;
  --gold-dk: #8A6220;
  --warm:    #6B3A1F;
  --muted:   #5A4A3A;
  --faint:   #A09080;
  --border:  #E5DDD0;
  --wa:      #25D366;
  --wa-dk:   #128C7E;
  --surface: #FFFFFF;
}

/* ── CURSOR ── */
#cur,#cur2{
  position:fixed;top:0;left:0;pointer-events:none;z-index:9999;border-radius:50%;
  mix-blend-mode:difference;transform:translate(-50%,-50%);transition-property:width,height,background;
  transition-duration:.25s;
}
#cur{width:8px;height:8px;background:#fff;transition-timing-function:ease}
#cur2{width:36px;height:36px;border:1px solid rgba(255,255,255,.5);background:transparent;
  transition-duration:.55s;transition-timing-function:cubic-bezier(.25,.46,.45,.94)}
body.hovering #cur{width:12px;height:12px}
body.hovering #cur2{width:52px;height:52px}
@media(hover:none){#cur,#cur2{display:none}}

html{scroll-behavior:smooth}
body{font-family:'Inter',system-ui,sans-serif;background:var(--ink);color:var(--ivory);overflow-x:hidden;cursor:none}
@media(hover:none){body{cursor:auto}}
img{display:block;width:100%;height:100%;object-fit:cover}
a,button{cursor:none}
@media(hover:none){a,button{cursor:auto}}

/* ── NAV ── */
#nav{
  position:fixed;top:0;left:0;right:0;z-index:200;
  padding:1.4rem 3rem;
  display:flex;justify-content:space-between;align-items:center;
  transition:background .5s,backdrop-filter .5s,border-color .5s,box-shadow .5s;
}
#nav.scrolled{
  background:rgba(245,239,227,.95);
  backdrop-filter:blur(18px);
  border-bottom:1px solid rgba(196,147,63,.15);
  box-shadow:0 2px 32px rgba(18,8,14,.09);
}
.logo{
  font-family:'Cormorant Garamond',serif;font-size:1.5rem;font-weight:600;
  color:var(--ivory);text-decoration:none;letter-spacing:.01em;transition:color .5s;
}
.logo em{font-style:italic;color:var(--gold)}
#nav.scrolled .logo{color:var(--ink)}
.nav-right{display:flex;align-items:center;gap:2rem}
.nav-link{
  font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;font-weight:500;
  color:rgba(245,239,227,.4);text-decoration:none;transition:color .3s;
}
#nav.scrolled .nav-link{color:var(--muted)}
.nav-link:hover{color:var(--gold)}
.nav-cta{
  font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;font-weight:500;
  color:var(--ink);background:var(--gold);text-decoration:none;
  padding:.45rem 1.25rem;border-radius:999px;
  transition:background .2s,transform .2s;
}
.nav-cta:hover{background:var(--gold-lt)}

/* ── HERO ── */
#hero{
  position:relative;min-height:100vh;display:flex;align-items:flex-end;overflow:hidden;
}
.hero-img{
  position:absolute;inset:0;
  background-image:url('https://images.unsplash.com/photo-1621176313593-89976c1f1bed?auto=format&fit=crop&w=1600&q=80');
  background-size:cover;background-position:center 30%;
  will-change:transform;
}
.hero-gradient{
  position:absolute;inset:0;
  background:linear-gradient(
    to top,
    rgba(18,8,14,.96) 0%,
    rgba(18,8,14,.72) 40%,
    rgba(18,8,14,.20) 75%,
    rgba(18,8,14,.06) 100%
  );
}
.hero-inner{
  position:relative;z-index:2;
  width:100%;max-width:1100px;margin:0 auto;
  padding:0 3rem 6rem;
}
.hero-eyebrow{
  font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;font-weight:500;
  color:var(--gold);margin-bottom:1.2rem;
  display:flex;align-items:center;gap:.75rem;
}
.hero-eyebrow::before{content:'';display:inline-block;width:24px;height:1px;background:var(--gold)}
.hero-h1{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(3.2rem,7.5vw,6.8rem);
  font-weight:300;line-height:1.02;letter-spacing:-.02em;
  color:var(--ivory);margin-bottom:1.6rem;max-width:820px;
}
.hero-h1 em{font-style:italic;color:var(--gold-lt);font-weight:300}
.hero-sub{
  font-size:1.05rem;color:rgba(245,239,227,.65);
  max-width:440px;line-height:1.82;font-weight:300;margin-bottom:2.6rem;
}
.hero-actions{display:flex;align-items:center;gap:1.4rem;flex-wrap:wrap}
.btn-primary{
  display:inline-flex;align-items:center;gap:.65rem;
  background:var(--wa);color:#fff;font-weight:500;font-size:.9rem;
  padding:.9rem 2.4rem;border-radius:999px;text-decoration:none;
  box-shadow:0 6px 36px rgba(37,211,102,.3);
  transition:background .2s,transform .18s,box-shadow .2s;
  letter-spacing:.02em;position:relative;overflow:hidden;
}
.btn-primary::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(circle at var(--mx,50%) var(--my,50%),rgba(255,255,255,.18) 0%,transparent 60%);
  opacity:0;transition:opacity .3s;
}
.btn-primary:hover::before{opacity:1}
.btn-primary:hover{background:#20b959;transform:translateY(-3px);box-shadow:0 12px 48px rgba(37,211,102,.4)}
.btn-primary svg{width:20px;height:20px;flex-shrink:0}
.btn-ghost{
  font-size:.82rem;color:rgba(245,239,227,.5);letter-spacing:.04em;
  text-decoration:none;transition:color .2s;
  border-bottom:1px solid rgba(245,239,227,.2);padding-bottom:1px;
}
.btn-ghost:hover{color:var(--ivory);border-color:rgba(245,239,227,.5)}
.hero-scroll{
  position:absolute;bottom:2.5rem;right:3rem;z-index:2;
  display:flex;align-items:center;gap:.6rem;
  font-size:.6rem;letter-spacing:.18em;text-transform:uppercase;
  color:rgba(245,239,227,.22);
  animation:bob 3s ease-in-out infinite;
}
.hero-scroll svg{width:14px;height:14px;opacity:.4}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(6px)}}

/* ── MARQUEE ── */
.marquee-wrap{
  background:var(--ink2);overflow:hidden;
  border-top:1px solid rgba(196,147,63,.10);
  border-bottom:1px solid rgba(196,147,63,.10);
  padding:.8rem 0;
}
.marquee-track{
  display:flex;gap:2.2rem;width:max-content;
  animation:scroll-left 35s linear infinite;
}
.marquee-track:hover{animation-play-state:paused}
.marquee-track span{
  font-family:'Cormorant Garamond',serif;font-size:1rem;font-style:italic;
  color:rgba(196,147,63,.4);white-space:nowrap;
}
.marquee-track .sep{color:rgba(196,147,63,.15);font-style:normal}
@keyframes scroll-left{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* ── STATS ── */
.stats-bar{
  background:var(--ink2);padding:3.5rem 3rem;
  border-bottom:1px solid rgba(196,147,63,.08);
}
.stats-inner{
  max-width:960px;margin:0 auto;
  display:grid;grid-template-columns:repeat(3,1fr);
  gap:1rem;text-align:center;
}
.stat-n{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2.8rem,5vw,4.2rem);font-weight:300;
  color:var(--gold);line-height:1;letter-spacing:-.02em;
}
.stat-n sup{font-size:.5em;vertical-align:super}
.stat-l{
  font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;font-weight:500;
  color:rgba(245,239,227,.28);margin-top:.5rem;
}
.stats-sep{
  width:1px;background:rgba(196,147,63,.12);
  margin:0 1rem;display:none;
}

/* ── REVEAL ── */
.reveal{opacity:0;transform:translateY(32px);transition:opacity .8s ease,transform .8s ease}
.reveal.in{opacity:1;transform:none}
.reveal-left{opacity:0;transform:translateX(-40px);transition:opacity .85s ease,transform .85s ease}
.reveal-left.in{opacity:1;transform:none}
.reveal-right{opacity:0;transform:translateX(40px);transition:opacity .85s ease,transform .85s ease}
.reveal-right.in{opacity:1;transform:none}
.d1{transition-delay:.12s}.d2{transition-delay:.24s}.d3{transition-delay:.38s}.d4{transition-delay:.52s}

/* ── CLIP REVEAL (images) ── */
.clip-reveal{
  clip-path:inset(0 100% 0 0);
  transition:clip-path 1.1s cubic-bezier(.77,0,.18,1);
}
.clip-reveal.in{clip-path:inset(0 0% 0 0)}

/* ── SPLIT SECTIONS ── */
.split{display:grid;grid-template-columns:1fr 1fr;min-height:580px}
.split-img{position:relative;overflow:hidden;min-height:420px}
.split-body{
  padding:5rem 4.5rem;display:flex;flex-direction:column;
  justify-content:center;
}
.split.light{background:var(--ivory)}
.split.dark{background:var(--ink2)}

/* light split */
.split.light .split-body .eyebrow{color:var(--gold-dk)}
.split.light .split-body .split-h{color:var(--ink)}
.split.light .split-body p{color:var(--muted)}

/* dark split */
.split.dark .split-body .eyebrow{color:var(--gold)}
.split.dark .split-body .split-h{color:var(--ivory)}
.split.dark .split-body p{color:rgba(245,239,227,.55)}

.eyebrow{
  font-size:.65rem;letter-spacing:.16em;text-transform:uppercase;font-weight:500;
  margin-bottom:.85rem;display:flex;align-items:center;gap:.6rem;
}
.eyebrow::before{content:'';display:inline-block;width:18px;height:1px;background:currentColor;opacity:.6}
.split-h{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2rem,3.8vw,3.1rem);
  font-weight:300;line-height:1.15;letter-spacing:-.015em;
  margin-bottom:1.4rem;
}
.split-h em{font-style:italic}
.split-body p{font-size:.95rem;line-height:1.82;font-weight:300;max-width:380px;margin-bottom:2rem}
.split-detail{
  font-size:.72rem;letter-spacing:.04em;
  color:rgba(245,239,227,.28);line-height:1.65;
}
.split.light .split-detail{color:var(--faint)}

/* ── FULL-BLEED BANNER ── */
.banner{position:relative;min-height:420px;overflow:hidden;display:flex;align-items:center}
.banner-img{position:absolute;inset:0}
.banner-overlay{
  position:absolute;inset:0;
  background:linear-gradient(105deg,rgba(18,8,14,.88) 0%,rgba(18,8,14,.55) 55%,rgba(18,8,14,.25) 100%);
}
.banner-body{
  position:relative;z-index:2;
  max-width:1100px;margin:0 auto;padding:5rem 3rem;width:100%;
}
.banner-h{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2.2rem,5vw,4rem);
  font-weight:300;line-height:1.12;color:var(--ivory);
  max-width:600px;letter-spacing:-.015em;
}
.banner-h em{font-style:italic;color:var(--gold-lt)}

/* ── HOW IT WORKS ── */
.how{background:var(--ivory2);padding:7rem 3rem;color:var(--ink)}
.how-inner{max-width:1100px;margin:0 auto}
.section-head{text-align:center;margin-bottom:4.5rem}
.section-h{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2rem,4vw,3rem);font-weight:300;line-height:1.18;
  letter-spacing:-.02em;margin-bottom:.85rem;
}
.section-p{font-size:.95rem;color:var(--muted);line-height:1.78;font-weight:300;max-width:440px;margin:0 auto}
.how .eyebrow{color:var(--gold-dk);justify-content:center}
.how .eyebrow::before{display:none}
.how-grid{display:grid;grid-template-columns:1fr 1fr;gap:6rem;align-items:center}
.steps{display:flex;flex-direction:column;gap:2.8rem}
.step{display:flex;gap:1.4rem;align-items:flex-start}
.step-n{
  min-width:36px;height:36px;border-radius:50%;flex-shrink:0;
  border:1px solid rgba(196,147,63,.35);
  color:var(--gold-dk);font-family:'Cormorant Garamond',serif;
  font-size:1rem;font-weight:600;display:flex;align-items:center;justify-content:center;
  margin-top:.1rem;
}
.step-body h3{
  font-family:'Lora',serif;font-size:1.08rem;font-weight:600;
  color:var(--ink);margin-bottom:.4rem;
}
.step-body p{font-size:.875rem;color:var(--muted);line-height:1.72;font-weight:300}

/* ── PHONE MOCKUP ── */
.phone-wrap{display:flex;justify-content:center;align-items:center}
.phone{
  width:226px;background:#1C1C1E;border-radius:42px;padding:10px;
  box-shadow:
    0 60px 120px rgba(0,0,0,.5),
    0 24px 48px rgba(0,0,0,.3),
    inset 0 0 0 1px rgba(255,255,255,.07);
  position:relative;
}
.phone::after{
  content:'';position:absolute;inset:-40px;z-index:-1;border-radius:80px;
  background:radial-gradient(ellipse at center,rgba(196,147,63,.15) 0%,transparent 65%);
}
.notch{width:70px;height:5px;background:#2A2A2C;border-radius:3px;margin:0 auto 7px}
.screen{background:#ECE5DD;border-radius:32px;overflow:hidden;display:flex;flex-direction:column;min-height:420px}
.wa-hdr{background:#075E54;padding:8px 10px;display:flex;align-items:center;gap:7px}
.wa-av{
  width:28px;height:28px;border-radius:50%;flex-shrink:0;
  background:#1A0F0A;display:flex;align-items:center;justify-content:center;
  font-family:'Cormorant Garamond',serif;font-size:13px;font-weight:600;color:var(--gold);
}
.wa-meta .wn{font-size:9px;font-weight:600;color:#fff;line-height:1.3}
.wa-meta .ws{font-size:7px;color:rgba(255,255,255,.55)}
.msgs{flex:1;padding:8px 7px;display:flex;flex-direction:column;gap:5px;background:#E5DDD9 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='.03'/%3E%3C/svg%3E")}
.bbl{max-width:88%;padding:5px 8px 4px;border-radius:10px;font-size:8.5px;line-height:1.5;color:#111}
.bbl .t{font-size:6.5px;color:rgba(0,0,0,.38);float:right;margin-left:6px;margin-top:2px}
.msg-in{background:#fff;align-self:flex-start;border-top-left-radius:2px}
.msg-out{background:#D9FDD3;align-self:flex-end;border-top-right-radius:2px}
.vn{display:flex;align-items:center;gap:5px;min-width:95px}
.vn-play{
  width:18px;height:18px;border-radius:50%;background:var(--wa-dk);flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
}
.vn-play::after{content:'▶';font-size:5.5px;color:#fff;margin-left:1.5px}
.waveform{display:flex;align-items:center;gap:1.5px;flex:1;height:18px}
.waveform span{width:2px;border-radius:1px;background:rgba(18,120,94,.7)}
.vn-dur{font-size:6.5px;color:rgba(0,0,0,.38)}
.wa-inp{
  background:#F0F0F0;margin:5px;border-radius:20px;
  padding:6px 10px;font-size:8px;color:rgba(0,0,0,.38);
  display:flex;align-items:center;justify-content:space-between;
}

/* ── CARDS (what we preserve) ── */
.preserve{background:var(--ivory2);padding:7rem 3rem;color:var(--ink);
  border-top:1px solid var(--border)}
.preserve-inner{max-width:1100px;margin:0 auto}
.preserve .eyebrow{color:var(--gold-dk);justify-content:center}
.preserve .eyebrow::before{display:none}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem;margin-top:3.5rem}
.card{
  background:var(--surface);border:1px solid var(--border);border-radius:20px;
  padding:2.4rem 2rem;display:flex;flex-direction:column;gap:.65rem;
  box-shadow:0 2px 16px rgba(18,8,14,.06);
  transition:box-shadow .28s,transform .28s;
  transform-style:preserve-3d;
}
.card:hover{box-shadow:0 16px 56px rgba(18,8,14,.14)}
.card-ico{font-size:2.2rem;line-height:1}
.card h3{font-family:'Lora',serif;font-size:1.15rem;font-weight:600;color:var(--ink)}
.card-sub{font-size:.63rem;font-weight:500;color:var(--gold-dk);letter-spacing:.12em;text-transform:uppercase;margin-top:-.2rem}
.card p{font-size:.87rem;color:var(--muted);line-height:1.72;font-weight:300}
.tags{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.4rem}
.tag{
  font-size:.63rem;background:rgba(196,147,63,.08);color:var(--gold-dk);
  border:1px solid rgba(196,147,63,.2);border-radius:999px;
  padding:.18rem .65rem;font-weight:500;
}

/* ── DARK QUOTE ── */
.quote-sec{
  position:relative;min-height:460px;overflow:hidden;
  display:flex;align-items:center;justify-content:center;text-align:center;
}
.quote-img{position:absolute;inset:0;filter:grayscale(40%)}
.quote-overlay{
  position:absolute;inset:0;
  background:rgba(18,8,14,.82);
}
.quote-body{position:relative;z-index:2;max-width:700px;padding:5rem 2rem}
.qmark{
  font-family:'Cormorant Garamond',serif;font-size:9rem;line-height:.65;
  color:var(--gold);opacity:.15;display:block;user-select:none;
  margin-bottom:-2rem;
}
blockquote{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(1.4rem,3.2vw,2.1rem);
  font-style:italic;color:var(--ivory);
  line-height:1.65;position:relative;z-index:1;font-weight:300;
}
blockquote em{color:var(--gold-lt);font-style:normal}
blockquote cite{
  display:block;margin-top:1.8rem;font-size:.7rem;font-style:normal;
  color:rgba(245,239,227,.28);letter-spacing:.1em;
  font-family:'Inter',sans-serif;text-transform:uppercase;
}

/* ── FINAL CTA ── */
.cta-sec{
  background:var(--ink);padding:7rem 3rem;text-align:center;
  position:relative;overflow:hidden;
}
.cta-sec::before{
  content:'';position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 60% 70% at 50% 50%,rgba(196,147,63,.07) 0%,transparent 70%);
}
.cta-inner{max-width:600px;margin:0 auto;position:relative;z-index:1}
.cta-sec .eyebrow{color:var(--gold);justify-content:center}
.cta-sec .eyebrow::before{display:none}
.cta-h{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(2.4rem,5vw,3.8rem);font-weight:300;
  color:var(--ivory);line-height:1.1;letter-spacing:-.02em;margin-bottom:1.2rem;
}
.cta-h em{font-style:italic;color:var(--gold-lt)}
.cta-sec p{
  font-size:.95rem;color:rgba(245,239,227,.45);
  line-height:1.78;font-weight:300;margin-bottom:2.6rem;
}
.cta-note{font-size:.74rem;color:rgba(245,239,227,.22);margin-top:1.4rem;letter-spacing:.03em}

/* ── FOOTER ── */
footer{
  background:var(--ink2);padding:1.8rem 3rem;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;
  border-top:1px solid rgba(196,147,63,.07);
}
footer p{font-size:.74rem;color:rgba(245,239,227,.18)}
.footer-right{display:flex;align-items:center;gap:1.6rem}
.live{display:inline-flex;align-items:center;gap:.4rem;font-size:.68rem;color:rgba(245,239,227,.18)}
.dot{width:6px;height:6px;background:var(--wa);border-radius:50%;animation:pulse 2.5s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.3;transform:scale(.7)}}
footer a{font-size:.74rem;color:rgba(245,239,227,.18);text-decoration:none;transition:color .2s}
footer a:hover{color:rgba(245,239,227,.5)}

/* ── RESPONSIVE ── */
@media(max-width:900px){
  .split{grid-template-columns:1fr}
  .split-img{min-height:320px}
  .split.rev .split-img{order:-1}
  .how-grid{grid-template-columns:1fr;gap:4rem}
  .phone-wrap{order:-1}
  .cards{grid-template-columns:1fr 1fr}
  .stats-inner{grid-template-columns:repeat(3,1fr)}
  #nav{padding:1.1rem 1.5rem}
  .hero-inner{padding:0 1.5rem 5rem}
  .split-body{padding:3.5rem 2rem}
  .how{padding:5rem 1.5rem}
  .banner-body{padding:4rem 1.5rem}
  .preserve{padding:5rem 1.5rem}
  .cta-sec{padding:5rem 1.5rem}
  footer{padding:1.6rem 1.5rem}
}
@media(max-width:600px){
  .cards{grid-template-columns:1fr}
  .stats-inner{grid-template-columns:1fr;gap:2rem}
  .hero-scroll{display:none}
  .nav-link{display:none}
}
</style>
</head>
<body>

<!-- CUSTOM CURSOR -->
<div id="cur" aria-hidden="true"></div>
<div id="cur2" aria-hidden="true"></div>

<!-- NAV -->
<nav id="nav">
  <a class="logo" href="/">smriti<em>.</em></a>
  <div class="nav-right">
    <span class="nav-link">स्मृति &middot; memory</span>
    <a class="nav-cta" href="mailto:vbajaj56@gmail.com?subject=smriti%20%E2%80%94%20get%20started">Gift it</a>
  </div>
</nav>

<!-- HERO -->
<section id="hero">
  <div class="hero-img" id="hero-img" aria-hidden="true"></div>
  <div class="hero-gradient" aria-hidden="true"></div>
  <div class="hero-inner">
    <p class="hero-eyebrow reveal">WhatsApp-native &middot; Made for India</p>
    <h1 class="hero-h1 reveal d1">
      The stories only<br><em>they</em> can tell.
    </h1>
    <p class="hero-sub reveal d2">Seven questions. Seven days. Your grandparent replies by voice on WhatsApp — in their language, at their pace. A lifetime of stories, captured in a week.</p>
    <div class="hero-actions reveal d3">
      <a class="btn-primary" id="cta-main" href="mailto:vbajaj56@gmail.com?subject=smriti%20%E2%80%94%20get%20started">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.117.554 4.107 1.523 5.83L0 24l6.364-1.499A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/></svg>
        Gift it to them
      </a>
      <a class="btn-ghost" href="#how">See how it works</a>
    </div>
  </div>
  <div class="hero-scroll" aria-hidden="true">
    <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/></svg>
    scroll
  </div>
</section>

<!-- MARQUEE -->
<div class="marquee-wrap" aria-hidden="true">
  <div class="marquee-track">
    <span>हिन्दी</span><span class="sep"> / </span>
    <span>ਪੰਜਾਬੀ</span><span class="sep"> / </span>
    <span>বাংলা</span><span class="sep"> / </span>
    <span>தமிழ்</span><span class="sep"> / </span>
    <span>English</span><span class="sep"> / </span>
    <span>Hinglish</span><span class="sep"> / </span>
    <span>मराठी</span><span class="sep"> / </span>
    <span>ગુજરાતી</span><span class="sep"> / </span>
    <span>తెలుగు</span><span class="sep"> / </span>
    <span>हिन्दी</span><span class="sep"> / </span>
    <span>ਪੰਜਾਬੀ</span><span class="sep"> / </span>
    <span>বাংলা</span><span class="sep"> / </span>
    <span>தமிழ்</span><span class="sep"> / </span>
    <span>English</span><span class="sep"> / </span>
    <span>Hinglish</span><span class="sep"> / </span>
    <span>मराठी</span><span class="sep"> / </span>
    <span>ગુજરાતી</span><span class="sep"> / </span>
    <span>తెలుగు</span><span class="sep"> / </span>
  </div>
</div>

<!-- STATS -->
<div class="stats-bar">
  <div class="stats-inner">
    <div class="reveal">
      <div class="stat-n"><span class="counter" data-target="284">0</span><sup>+</sup></div>
      <div class="stat-l">families enrolled</div>
    </div>
    <div class="reveal d1">
      <div class="stat-n"><span class="counter" data-target="12000">0</span><sup>+</sup></div>
      <div class="stat-l">stories captured</div>
    </div>
    <div class="reveal d2">
      <div class="stat-n"><span class="counter" data-target="9">0</span></div>
      <div class="stat-l">languages spoken</div>
    </div>
  </div>
</div>

<!-- SPLIT 1: The gift — light, image right -->
<div class="split light">
  <div class="split-body">
    <p class="eyebrow reveal-left" style="color:var(--gold-dk)">The gift that lasts</p>
    <h2 class="split-h reveal-left d1">
      Seven questions.<br><em>A lifetime preserved.</em>
    </h2>
    <p class="reveal-left d2">They won't be here forever. Neither will their stories — unless someone asks. smriti does the asking, one morning at a time, in their own language, through WhatsApp they already know.</p>
    <p class="split-detail reveal-left d3">No app to install &middot; No new passwords &middot; Just WhatsApp</p>
  </div>
  <div class="split-img">
    <div class="clip-reveal" style="position:absolute;inset:0">
      <img src="https://images.unsplash.com/photo-1677236097903-4b7565f26602?auto=format&fit=crop&w=1200&q=80" alt="Elderly hands writing, preserving memories" loading="lazy">
    </div>
  </div>
</div>

<!-- FULL-BLEED BANNER -->
<div class="banner">
  <div class="banner-img">
    <img src="https://images.unsplash.com/photo-1580471261280-70f801d33146?auto=format&fit=crop&w=1600&q=80" alt="Elderly women laughing, sharing stories" loading="lazy">
  </div>
  <div class="banner-overlay"></div>
  <div class="banner-body">
    <h2 class="banner-h reveal">
      They have so many<br><em>stories left to tell.</em>
    </h2>
  </div>
</div>

<!-- HOW IT WORKS -->
<section class="how" id="how">
  <div class="how-inner">
    <div class="section-head reveal">
      <p class="eyebrow" style="color:var(--gold-dk);justify-content:center;display:flex"><span style="display:flex;align-items:center;gap:.6rem"><span style="display:inline-block;width:18px;height:1px;background:var(--gold-dk);opacity:.6"></span>How it works</span></p>
      <h2 class="section-h" style="color:var(--ink)">Seven days.<br>A lifetime preserved.</h2>
      <p class="section-p">They never download anything. You never chase them. One question arrives each morning — they reply whenever they're ready.</p>
    </div>
    <div class="how-grid">
      <div class="steps">
        <div class="step reveal d1">
          <div class="step-n">1</div>
          <div class="step-body">
            <h3>You start the sprint</h3>
            <p>Tell us their name, WhatsApp number, and language. Choose a theme — childhood, career, love story. We handle everything else. Takes two minutes.</p>
          </div>
        </div>
        <div class="step reveal d2">
          <div class="step-n">2</div>
          <div class="step-body">
            <h3>7 questions over 7 days</h3>
            <p>One warm, curated question arrives each morning on WhatsApp — "What did you cook for your wedding?" They reply by voice note whenever they're ready. No pressure.</p>
          </div>
        </div>
        <div class="step reveal d3">
          <div class="step-n">3</div>
          <div class="step-body">
            <h3>A chapter is born</h3>
            <p>Every reply is AI-polished into beautiful prose. Seven days later, a richly designed memoir chapter — digital or hardbound — is ready to keep forever. Do as many sprints as you want.</p>
          </div>
        </div>
      </div>
      <div class="phone-wrap reveal d2">
        <div class="phone">
          <div class="notch"></div>
          <div class="screen">
            <div class="wa-hdr">
              <div class="wa-av">स</div>
              <div class="wa-meta">
                <div class="wn">smriti</div>
                <div class="ws">Day 3 of 7 · Childhood</div>
              </div>
            </div>
            <div class="msgs">
              <div class="bbl msg-in">
                नमस्ते दादीजी 🙏<br><br>
                आज का सवाल: बचपन में आपकी सबसे पसंदीदा दिवाली की याद क्या है?
                <span class="t">9:00 ✓✓</span>
              </div>
              <div class="bbl msg-out">
                <div class="vn">
                  <div class="vn-play"></div>
                  <div class="waveform">
                    <span style="height:4px"></span><span style="height:10px"></span>
                    <span style="height:14px"></span><span style="height:7px"></span>
                    <span style="height:16px"></span><span style="height:11px"></span>
                    <span style="height:13px"></span><span style="height:5px"></span>
                    <span style="height:15px"></span><span style="height:9px"></span>
                    <span style="height:12px"></span><span style="height:6px"></span>
                    <span style="height:14px"></span><span style="height:8px"></span>
                    <span style="height:4px"></span>
                  </div>
                  <span class="vn-dur">2:07</span>
                </div>
                <span class="t">11:24</span>
              </div>
              <div class="bbl msg-in">
                क्या खूब यादें, दादीजी! ✨<br>
                आपकी कहानी सुरक्षित हो गई।<br>
                कल का सवाल सुबह 9 बजे आएगा।
                <span class="t">11:24 ✓✓</span>
              </div>
            </div>
            <div class="wa-inp">
              <span>Message</span><span>🎤</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- SPLIT 2: The book — dark, image left -->
<div class="split dark rev">
  <div class="split-img">
    <div class="clip-reveal" style="position:absolute;inset:0">
      <img src="https://images.unsplash.com/photo-1639371040157-55b642d03f4f?auto=format&fit=crop&w=1200&q=80" alt="Leather-bound memoir book" loading="lazy">
    </div>
  </div>
  <div class="split-body">
    <p class="eyebrow reveal-right" style="color:var(--gold)">The heirloom</p>
    <h2 class="split-h reveal-right d1" style="color:var(--ivory)">
      From voice notes<br>to <em>hardbound memoir.</em>
    </h2>
    <p class="reveal-right d2" style="color:rgba(245,239,227,.55)">Seven days of voice notes, woven by AI into beautifully designed prose — then printed into a hardbound memoir chapter. Start with childhood. Add career. Add a love story. Each sprint becomes its own chapter.</p>
    <p class="split-detail reveal-right d3">Digital PDF ready in 7 days &middot; Hardbound book optional &middot; Audio recordings preserved</p>
  </div>
</div>

<!-- WHAT WE PRESERVE -->
<section class="preserve">
  <div class="preserve-inner">
    <div class="section-head reveal">
      <p class="eyebrow" style="color:var(--gold-dk)">What smriti captures</p>
      <h2 class="section-h" style="color:var(--ink)">Every family has stories that live<br>in one person's voice.</h2>
      <p class="section-p">Partition memories. Recipes. College days. The moments that should outlive us — but usually don't.</p>
    </div>
    <div class="cards">
      <div class="card tilt reveal d1">
        <div class="card-ico">🪔</div>
        <h3>Dadi ke kissey</h3>
        <p class="card-sub">Family history</p>
        <p>Partition memories. Migration stories. How your family came to be. The history that lives in one person's voice — and disappears when it's gone.</p>
        <div class="tags">
          <span class="tag">Grandparents</span><span class="tag">Family lore</span><span class="tag">Recipes</span>
        </div>
      </div>
      <div class="card tilt reveal d2">
        <div class="card-ico">🎓</div>
        <h3>Apni yaadein</h3>
        <p class="card-sub">Your nostalgia</p>
        <p>College hostel nights. The friend group that changed you. First heartbreaks, road trips — your story, properly told before the details fade.</p>
        <div class="tags">
          <span class="tag">College days</span><span class="tag">Friendships</span><span class="tag">Milestones</span>
        </div>
      </div>
      <div class="card tilt reveal d3">
        <div class="card-ico">👶</div>
        <h3>Unka bachpan</h3>
        <p class="card-sub">Your children</p>
        <p>They grow up faster than you think. First words, the things they say that break your heart with love — hold onto these moments forever.</p>
        <div class="tags">
          <span class="tag">First words</span><span class="tag">Childhood</span><span class="tag">Growing up</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- DARK QUOTE -->
<section class="quote-sec">
  <div class="quote-img">
    <img src="https://images.unsplash.com/photo-1652300353103-490b43ac8366?auto=format&fit=crop&w=1600&q=80" alt="" aria-hidden="true" loading="lazy">
  </div>
  <div class="quote-overlay"></div>
  <div class="quote-body reveal">
    <span class="qmark">&ldquo;</span>
    <blockquote>
      Remember the story dadi told at the last family gathering?<br>
      <em>You don't. Neither do we.</em><br>
      That's why we built smriti.
      <cite>— the idea behind smriti</cite>
    </blockquote>
  </div>
</section>

<!-- FINAL CTA -->
<section class="cta-sec">
  <div class="cta-inner">
    <p class="eyebrow reveal">Start today</p>
    <h2 class="cta-h reveal d1">
      Their stories are waiting.<br><em>Don't wait too long.</em>
    </h2>
    <p class="reveal d2">Sign up takes two minutes. We'll take it from there. The memoir lasts forever.</p>
    <div class="reveal d3">
      <a class="btn-primary" id="cta-footer" href="mailto:vbajaj56@gmail.com?subject=smriti%20%E2%80%94%20get%20started">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.117.554 4.107 1.523 5.83L0 24l6.364-1.499A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/></svg>
        Start preserving their stories
      </a>
    </div>
    <p class="cta-note reveal d4">No app to download &middot; WhatsApp only &middot; Cancel anytime</p>
  </div>
</section>

<footer>
  <p>smriti &copy; 2026 &middot; Made with love for India</p>
  <div class="footer-right">
    <a href="mailto:vbajaj56@gmail.com">hello@smriti.in</a>
    <span class="live"><span class="dot"></span>live</span>
  </div>
</footer>

<script>
// ── CURSOR ──
(function(){
  if(!matchMedia('(hover:hover)').matches)return;
  const c=document.getElementById('cur'),c2=document.getElementById('cur2');
  let mx=0,my=0,cx=0,cy=0;
  document.addEventListener('mousemove',e=>{mx=e.clientX;my=e.clientY;c.style.left=mx+'px';c.style.top=my+'px'},{passive:true});
  (function loop(){cx+=(mx-cx)*.18;cy+=(my-cy)*.18;c2.style.left=cx+'px';c2.style.top=cy+'px';requestAnimationFrame(loop)})();
  const els=document.querySelectorAll('a,button,.card,.btn-primary,.nav-cta');
  els.forEach(el=>{
    el.addEventListener('mouseenter',()=>document.body.classList.add('hovering'));
    el.addEventListener('mouseleave',()=>document.body.classList.remove('hovering'));
  });
})();

// ── MAGNETIC BUTTONS ──
(function(){
  if(!matchMedia('(hover:hover)').matches)return;
  document.querySelectorAll('.btn-primary,.nav-cta').forEach(btn=>{
    btn.addEventListener('mousemove',e=>{
      const r=btn.getBoundingClientRect();
      const x=e.clientX-r.left-r.width/2;
      const y=e.clientY-r.top-r.height/2;
      btn.style.transform=`translate(${x*.22}px,${y*.22}px)`;
      btn.style.setProperty('--mx',((e.clientX-r.left)/r.width*100)+'%');
      btn.style.setProperty('--my',((e.clientY-r.top)/r.height*100)+'%');
    });
    btn.addEventListener('mouseleave',()=>{
      btn.style.transform='';
    });
  });
})();

// ── PARALLAX HERO ──
(function(){
  const img=document.getElementById('hero-img');
  if(!img)return;
  let ticking=false;
  window.addEventListener('scroll',()=>{
    if(!ticking){
      requestAnimationFrame(()=>{
        img.style.transform='translateY('+(scrollY*.4)+'px)';
        ticking=false;
      });
      ticking=true;
    }
  },{passive:true});
})();

// ── NAV SCROLL ──
(function(){
  const nav=document.getElementById('nav');
  const fn=()=>nav.classList.toggle('scrolled',scrollY>60);
  window.addEventListener('scroll',fn,{passive:true});fn();
})();

// ── INTERSECTION OBSERVER (reveal + clip + counter) ──
(function(){
  // General reveal
  const io=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}
    });
  },{threshold:.1,rootMargin:'0px 0px -40px 0px'});
  document.querySelectorAll('.reveal,.reveal-left,.reveal-right').forEach(el=>io.observe(el));

  // Clip reveals (images)
  const io2=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){e.target.classList.add('in');io2.unobserve(e.target)}
    });
  },{threshold:.15});
  document.querySelectorAll('.clip-reveal').forEach(el=>io2.observe(el));

  // Counters
  function animCount(el){
    const target=parseInt(el.dataset.target,10);
    const dur=1800;
    const start=performance.now();
    const fmt=n=>target>=1000?Math.round(n).toLocaleString('en-IN'):Math.round(n);
    function tick(now){
      const p=Math.min((now-start)/dur,1);
      const ease=1-Math.pow(1-p,3);
      el.textContent=fmt(ease*target);
      if(p<1)requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  const io3=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){animCount(e.target);io3.unobserve(e.target)}
    });
  },{threshold:.5});
  document.querySelectorAll('.counter').forEach(el=>io3.observe(el));
})();

// ── 3D CARD TILT ──
(function(){
  if(!matchMedia('(hover:hover)').matches)return;
  document.querySelectorAll('.tilt').forEach(card=>{
    card.addEventListener('mousemove',e=>{
      const r=card.getBoundingClientRect();
      const x=(e.clientX-r.left)/r.width-.5;
      const y=(e.clientY-r.top)/r.height-.5;
      card.style.transform=`perspective(600px) rotateY(${x*9}deg) rotateX(${-y*9}deg) translateY(-6px)`;
    });
    card.addEventListener('mouseleave',()=>{
      card.style.transform='perspective(600px) rotateY(0) rotateX(0) translateY(0)';
    });
  });
})();

// ── HERO REVEAL ON LOAD ──
(function(){
  document.querySelectorAll('#hero .reveal').forEach((el,i)=>{
    setTimeout(()=>el.classList.add('in'),300+i*150);
  });
})();
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing():
    return _PAGE
