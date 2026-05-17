from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>smriti — preserve their stories</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%233B2C8F'/><text x='16' y='24' font-size='20' font-weight='bold' text-anchor='middle' fill='%23D4A84B' font-family='Georgia,serif'>&#x938;</text></svg>">
<link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%233B2C8F'/><text x='16' y='24' font-size='20' font-weight='bold' text-anchor='middle' fill='%23D4A84B' font-family='Georgia,serif'>&#x938;</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --dark:    #0C0906;
  --dark2:   #100D09;
  --cream:   #F2E8D5;
  --cream2:  #FAF7F2;
  --gold:    #D4A84B;
  --gold-dk: #A87830;
  --indigo:  #3B2C8F;
  --ind-lt:  #5848B4;
  --ind-bg:  #EDEAF8;
  --ink:     #18102E;
  --muted:   #52476A;
  --faint:   #8B82A0;
  --border:  #DDD7EE;
  --wa:      #25D366;
  --wa-dk:   #128C7E;
  --surface: #FFFFFF;
  --sh-card: 0 2px 12px rgba(26,18,48,.07);
  --sh-lift: 0 10px 44px rgba(26,18,48,.13);
}

html{scroll-behavior:smooth}
body{font-family:'Inter',system-ui,sans-serif;background:var(--dark);color:var(--cream);overflow-x:hidden}

/* ─── NAV ─── */
#nav{
  position:fixed;top:0;left:0;right:0;z-index:100;
  padding:1.2rem 2.5rem;
  display:flex;justify-content:space-between;align-items:center;
  transition:background .4s,backdrop-filter .4s,border-color .4s,box-shadow .4s;
}
#nav.scrolled{
  background:rgba(250,247,242,.93);
  backdrop-filter:blur(14px);
  border-bottom:1px solid rgba(59,44,143,.10);
  box-shadow:0 1px 24px rgba(26,18,48,.08);
}
.logo{font-family:'Lora',serif;font-size:1.3rem;font-weight:600;color:var(--cream);text-decoration:none;letter-spacing:-.01em;transition:color .4s}
.logo span{color:var(--gold)}
#nav.scrolled .logo{color:var(--ink)}
.nav-pill{
  font-size:.7rem;letter-spacing:.09em;text-transform:uppercase;
  color:rgba(242,232,213,.4);transition:color .4s;
}
#nav.scrolled .nav-pill{color:var(--faint)}

/* ─── HERO ─── */
#hero{
  min-height:100vh;display:flex;align-items:center;justify-content:center;
  text-align:center;position:relative;overflow:hidden;
  background:var(--dark);
}
#bokeh{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.grain{
  position:absolute;inset:0;pointer-events:none;opacity:.28;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='.08'/%3E%3C/svg%3E");
  background-size:200px 200px;
}
.hero-inner{
  position:relative;z-index:2;
  display:flex;flex-direction:column;align-items:center;gap:1.4rem;
  padding:8rem 1.5rem 5rem;max-width:700px;
}
.hero-badge{
  display:inline-flex;align-items:center;gap:.5rem;
  border:1px solid rgba(212,168,75,.28);border-radius:999px;
  padding:.28rem .9rem;font-size:.7rem;font-weight:500;
  color:rgba(212,168,75,.85);letter-spacing:.06em;text-transform:uppercase;
  background:rgba(212,168,75,.07);
}
.hero-inner h1{
  font-family:'Lora',serif;
  font-size:clamp(2.8rem,7vw,5.2rem);
  font-weight:700;line-height:1.06;letter-spacing:-.03em;color:var(--cream);
}
.hero-inner h1 em{font-style:italic;color:var(--gold);font-weight:400}
.hero-deva{
  font-family:'Lora',serif;font-size:.95rem;font-style:italic;
  color:rgba(212,168,75,.55);margin-top:-.4rem;
}
.hero-sub{
  font-size:1.05rem;color:rgba(242,232,213,.6);max-width:460px;
  line-height:1.78;font-weight:300;
}
.btn-wa{
  display:inline-flex;align-items:center;gap:.6rem;
  background:var(--wa);color:#fff;font-weight:600;font-size:.95rem;
  padding:.9rem 2.2rem;border-radius:999px;text-decoration:none;
  box-shadow:0 4px 28px rgba(37,211,102,.28);
  transition:background .2s,transform .15s,box-shadow .2s;
  letter-spacing:.01em;margin-top:.4rem;
}
.btn-wa:hover{background:var(--wa-dk);transform:translateY(-2px);box-shadow:0 8px 40px rgba(37,211,102,.38)}
.btn-wa svg{width:18px;height:18px;flex-shrink:0}
.hero-foot{font-size:.76rem;color:rgba(242,232,213,.3);letter-spacing:.02em}

/* scroll cue */
.cue{
  position:absolute;bottom:2rem;left:50%;transform:translateX(-50%);
  display:flex;flex-direction:column;align-items:center;gap:.35rem;
  font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;
  color:rgba(242,232,213,.2);z-index:2;
  animation:cue-bob 2.8s ease-in-out infinite;
}
.cue::after{content:'';display:block;width:1px;height:30px;background:linear-gradient(to bottom,rgba(242,232,213,.2),transparent)}
@keyframes cue-bob{0%,100%{transform:translateX(-50%) translateY(0)}50%{transform:translateX(-50%) translateY(7px)}}

/* ─── MARQUEE ─── */
.marquee-wrap{
  background:var(--dark2);overflow:hidden;
  border-top:1px solid rgba(212,168,75,.09);
  border-bottom:1px solid rgba(212,168,75,.09);
  padding:.95rem 0;
}
.marquee-track{
  display:flex;gap:2rem;width:max-content;
  animation:scroll-left 30s linear infinite;
}
.marquee-track:hover{animation-play-state:paused}
.marquee-track span{font-family:'Lora',serif;font-size:.95rem;color:rgba(212,168,75,.45);white-space:nowrap}
.marquee-track .sep{color:rgba(212,168,75,.18);font-weight:300}
@keyframes scroll-left{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* ─── REVEAL ─── */
.reveal{opacity:0;transform:translateY(26px);transition:opacity .75s ease,transform .75s ease}
.reveal.in{opacity:1;transform:none}
.d1{transition-delay:.1s}.d2{transition-delay:.2s}.d3{transition-delay:.3s}

/* ─── CAPTURE (light) ─── */
.capture{background:var(--cream2);padding:6rem 1.5rem;color:var(--ink)}
.section-inner{max-width:1040px;margin:0 auto}
.section-head{text-align:center;margin-bottom:3.5rem}
.eyebrow{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;font-weight:600;margin-bottom:.7rem}
.section-h{
  font-family:'Lora',serif;font-size:clamp(1.8rem,4vw,2.7rem);
  font-weight:600;line-height:1.18;letter-spacing:-.025em;margin-bottom:.9rem;
}
.section-p{font-size:.97rem;color:var(--muted);line-height:1.72;font-weight:300;max-width:480px;margin:0 auto}
.capture .eyebrow{color:var(--indigo)}
.capture .section-h{color:var(--ink)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.4rem}
.card{
  background:var(--surface);border:1px solid var(--border);border-radius:20px;
  padding:2.2rem 1.9rem;display:flex;flex-direction:column;gap:.65rem;
  box-shadow:var(--sh-card);
  transition:box-shadow .25s,transform .25s;cursor:default;
}
.card:hover{box-shadow:var(--sh-lift);transform:translateY(-5px)}
.card-ico{font-size:2.1rem;line-height:1}
.card h3{font-family:'Lora',serif;font-size:1.18rem;font-weight:600;color:var(--ink)}
.card-sub{font-size:.67rem;font-weight:600;color:var(--ind-lt);letter-spacing:.1em;text-transform:uppercase;margin-top:-.3rem}
.card p{font-size:.875rem;color:var(--muted);line-height:1.7;font-weight:300}
.tags{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.3rem}
.tag{font-size:.67rem;background:var(--ind-bg);color:var(--indigo);border:1px solid rgba(59,44,143,.14);border-radius:999px;padding:.18rem .62rem;font-weight:500}

/* ─── HOW IT WORKS ─── */
.how{
  background:#F3F0FB;padding:6rem 1.5rem;color:var(--ink);
  border-top:1px solid var(--border);border-bottom:1px solid var(--border);
}
.how-grid{
  max-width:1040px;margin:0 auto;
  display:grid;grid-template-columns:1fr 1fr;gap:5rem;align-items:center;
}
.how .eyebrow{color:var(--indigo)}
.how .section-h{color:var(--ink);margin-bottom:2.5rem}
.steps{display:flex;flex-direction:column;gap:2rem}
.step{display:flex;gap:1.2rem;align-items:flex-start}
.step-n{
  width:30px;height:30px;border-radius:50%;flex-shrink:0;
  background:var(--indigo);color:#fff;
  display:flex;align-items:center;justify-content:center;
  font-size:.72rem;font-weight:700;margin-top:.15rem;
}
.step-body h3{font-family:'Lora',serif;font-size:1.02rem;font-weight:600;color:var(--ink);margin-bottom:.3rem}
.step-body p{font-size:.865rem;color:var(--muted);line-height:1.65;font-weight:300}

/* ─── PHONE MOCKUP ─── */
.phone-wrap{display:flex;justify-content:center;align-items:center}
.phone{
  width:218px;background:#1C1C1E;border-radius:40px;
  padding:10px;
  box-shadow:
    0 50px 100px rgba(0,0,0,.45),
    0 20px 40px rgba(0,0,0,.3),
    inset 0 0 0 1px rgba(255,255,255,.07);
  position:relative;
}
.phone::before{
  content:'';position:absolute;inset:-30px;z-index:-1;border-radius:70px;
  background:radial-gradient(ellipse at center,rgba(59,44,143,.22) 0%,transparent 70%);
}
.notch{width:72px;height:5px;background:#2A2A2C;border-radius:3px;margin:0 auto 7px}
.screen{
  background:#E8DDD1;border-radius:30px;overflow:hidden;
  display:flex;flex-direction:column;min-height:400px;
}
.wa-hdr{
  background:#075E54;padding:7px 10px;
  display:flex;align-items:center;gap:7px;
}
.wa-av{
  width:26px;height:26px;border-radius:50%;flex-shrink:0;
  background:var(--indigo);
  display:flex;align-items:center;justify-content:center;
  font-family:'Lora',serif;font-size:12px;font-weight:700;color:var(--gold);
}
.wa-meta .wn{font-size:8.5px;font-weight:600;color:#fff;line-height:1.3}
.wa-meta .ws{font-size:7px;color:rgba(255,255,255,.6)}
.msgs{flex:1;padding:7px 6px;display:flex;flex-direction:column;gap:4px}
.bbl{
  max-width:90%;padding:5px 7px;border-radius:10px;
  font-size:8px;line-height:1.45;color:#111;
}
.bbl .t{font-size:6px;color:rgba(0,0,0,.38);float:right;margin-left:5px;margin-top:2px}
.in{background:#fff;align-self:flex-start;border-top-left-radius:2px}
.out{background:#D9FDD3;align-self:flex-end;border-top-right-radius:2px}
.vn{display:flex;align-items:center;gap:4px;min-width:90px}
.vn-play{
  width:16px;height:16px;border-radius:50%;background:var(--wa-dk);flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
}
.vn-play::after{content:'▶';font-size:5px;color:#fff;margin-left:1px}
.waveform{display:flex;align-items:center;gap:1.5px;flex:1;height:16px}
.waveform span{width:2px;border-radius:1px;background:var(--wa-dk);opacity:.65}
.vn-dur{font-size:6px;color:rgba(0,0,0,.4)}
.wa-inp{
  background:#F0F0F0;margin:5px;border-radius:18px;
  padding:5px 10px;font-size:7px;color:rgba(0,0,0,.38);
  display:flex;align-items:center;justify-content:space-between;
}

/* ─── DARK QUOTE ─── */
.quote-sec{
  background:var(--dark);padding:7rem 1.5rem;text-align:center;
  position:relative;overflow:hidden;
}
.quote-sec::before{
  content:'';position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 65% 55% at 50% 50%,rgba(212,168,75,.06) 0%,transparent 70%);
}
.qmark{
  font-family:'Lora',serif;font-size:7rem;line-height:.75;
  color:var(--gold);opacity:.18;display:block;
  margin-bottom:-1.8rem;user-select:none;
}
blockquote{
  font-family:'Lora',serif;
  font-size:clamp(1.15rem,2.8vw,1.65rem);
  font-style:italic;color:var(--cream);
  max-width:620px;margin:0 auto;line-height:1.72;position:relative;z-index:1;
}
blockquote em{color:var(--gold);font-style:normal}
blockquote cite{
  display:block;margin-top:1.5rem;font-size:.76rem;font-style:normal;
  color:rgba(242,232,213,.3);letter-spacing:.06em;
  font-family:'Inter',sans-serif;text-transform:uppercase;
}

/* ─── FINAL CTA ─── */
.cta-sec{
  background:var(--cream2);padding:6rem 1.5rem;text-align:center;
  border-top:1px solid var(--border);
}
.cta-inner{max-width:540px;margin:0 auto}
.cta-sec .eyebrow{color:var(--indigo)}
.cta-sec .section-h{color:var(--ink);margin-bottom:1rem}
.cta-sec p{font-size:.95rem;color:var(--muted);line-height:1.72;font-weight:300;margin-bottom:2.2rem}

/* ─── FOOTER ─── */
footer{
  background:var(--dark2);padding:1.6rem 2.5rem;
  display:flex;justify-content:space-between;align-items:center;
  flex-wrap:wrap;gap:.75rem;
  border-top:1px solid rgba(212,168,75,.08);
}
footer p{font-size:.76rem;color:rgba(242,232,213,.22)}
.live{display:inline-flex;align-items:center;gap:.4rem;font-size:.72rem;color:rgba(242,232,213,.22)}
.dot{width:6px;height:6px;background:var(--wa);border-radius:50%;animation:pulse 2.5s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.78)}}

/* ─── RESPONSIVE ─── */
@media(max-width:800px){
  .how-grid{grid-template-columns:1fr;gap:3rem}
  .phone-wrap{order:-1}
}
@media(max-width:600px){
  #nav{padding:1rem 1.25rem}
  .hero-inner{padding:7rem 1.25rem 4rem}
  footer{flex-direction:column;align-items:flex-start}
}
</style>
</head>
<body>

<nav id="nav">
  <a class="logo" href="/">smriti<span>.</span></a>
  <span class="nav-pill">स्मृति &middot; memory</span>
</nav>

<!-- HERO -->
<section id="hero">
  <canvas id="bokeh"></canvas>
  <div class="grain" aria-hidden="true"></div>
  <div class="hero-inner">
    <div class="hero-badge">📖 WhatsApp-native &middot; Made for India</div>
    <h1>The stories only<br><em>they</em> can tell.</h1>
    <p class="hero-deva">स्मृति — that which is remembered</p>
    <p class="hero-sub">One gentle WhatsApp question a week. Your grandparent replies in their own voice. Their stories become a memoir — yours to keep forever.</p>
    <a class="btn-wa" href="mailto:vbajaj56@gmail.com?subject=smriti%20%E2%80%94%20get%20started">
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.117.554 4.107 1.523 5.83L0 24l6.364-1.499A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/></svg>
      Gift it to them
    </a>
    <p class="hero-foot">No app to download &middot; Just WhatsApp</p>
  </div>
  <div class="cue" aria-hidden="true">scroll</div>
</section>

<!-- MARQUEE -->
<div class="marquee-wrap" aria-hidden="true">
  <div class="marquee-track">
    <span>हिन्दी</span><span class="sep">/</span>
    <span>ਪੰਜਾਬੀ</span><span class="sep">/</span>
    <span>বাংলা</span><span class="sep">/</span>
    <span>தமிழ்</span><span class="sep">/</span>
    <span>English</span><span class="sep">/</span>
    <span>Hinglish</span><span class="sep">/</span>
    <span>मराठी</span><span class="sep">/</span>
    <span>ગુજરાતી</span><span class="sep">/</span>
    <span>తెలుగు</span><span class="sep">/</span>
    <span>हिन्दी</span><span class="sep">/</span>
    <span>ਪੰਜਾਬੀ</span><span class="sep">/</span>
    <span>বাংলা</span><span class="sep">/</span>
    <span>தமிழ்</span><span class="sep">/</span>
    <span>English</span><span class="sep">/</span>
    <span>Hinglish</span><span class="sep">/</span>
    <span>मराठी</span><span class="sep">/</span>
    <span>ગુજરાતી</span><span class="sep">/</span>
    <span>తెలుగు</span><span class="sep">/</span>
  </div>
</div>

<!-- WHAT WE CAPTURE -->
<section class="capture">
  <div class="section-inner">
    <div class="section-head reveal">
      <p class="eyebrow">What smriti preserves</p>
      <h2 class="section-h">Every family has stories<br>that live in one person's voice.</h2>
      <p class="section-p">Partition memories. Recipes. College days. The moments that should outlive us — but usually don't.</p>
    </div>
    <div class="cards">
      <div class="card reveal d1">
        <div class="card-ico">🪔</div>
        <h3>Dadi ke kissey</h3>
        <p class="card-sub">Family history</p>
        <p>Partition memories. Migration stories. How your family came to be. The history that lives in one person's voice — and disappears when it's gone.</p>
        <div class="tags">
          <span class="tag">Grandparents</span><span class="tag">Family lore</span><span class="tag">Recipes</span>
        </div>
      </div>
      <div class="card reveal d2">
        <div class="card-ico">🎓</div>
        <h3>Apni yaadein</h3>
        <p class="card-sub">Your nostalgia</p>
        <p>College hostel nights. The friend group that changed you. First heartbreaks, road trips — your story, properly told before the details fade.</p>
        <div class="tags">
          <span class="tag">College days</span><span class="tag">Friendships</span><span class="tag">Milestones</span>
        </div>
      </div>
      <div class="card reveal d3">
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

<!-- HOW IT WORKS -->
<section class="how">
  <div class="how-grid">
    <div class="how-left">
      <div class="reveal">
        <p class="eyebrow">How it works</p>
        <h2 class="section-h">So simple your dadi<br>can use it alone.</h2>
      </div>
      <div class="steps">
        <div class="step reveal d1">
          <div class="step-n">1</div>
          <div class="step-body">
            <h3>You gift it to them</h3>
            <p>Sign up smriti for your grandparent in two minutes. No app to install on either side — just their WhatsApp number and name.</p>
          </div>
        </div>
        <div class="step reveal d2">
          <div class="step-n">2</div>
          <div class="step-body">
            <h3>One question, every week</h3>
            <p>smriti sends a warm, thoughtful prompt in their language on WhatsApp. They just reply — voice note or a few words. That's it.</p>
          </div>
        </div>
        <div class="step reveal d3">
          <div class="step-n">3</div>
          <div class="step-body">
            <h3>A memoir is born</h3>
            <p>Every reply is saved, AI-polished, and woven into a private timeline — and eventually a physical memoir book and video, yours to keep.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- CSS PHONE MOCKUP -->
    <div class="phone-wrap reveal d2">
      <div class="phone">
        <div class="notch"></div>
        <div class="screen">
          <div class="wa-hdr">
            <div class="wa-av">स</div>
            <div class="wa-meta">
              <div class="wn">smriti</div>
              <div class="ws">usually replies instantly</div>
            </div>
          </div>
          <div class="msgs">
            <div class="bbl in">
              नमस्ते दादीजी 🙏<br><br>
              आज का सवाल: बचपन में आपका सबसे पसंदीदा त्योहार कौन सा था?
              <span class="t">10:00 AM ✓✓</span>
            </div>
            <div class="bbl out">
              <div class="vn">
                <div class="vn-play"></div>
                <div class="waveform">
                  <span style="height:4px"></span><span style="height:9px"></span>
                  <span style="height:13px"></span><span style="height:7px"></span>
                  <span style="height:15px"></span><span style="height:10px"></span>
                  <span style="height:12px"></span><span style="height:5px"></span>
                  <span style="height:14px"></span><span style="height:8px"></span>
                  <span style="height:11px"></span><span style="height:6px"></span>
                  <span style="height:13px"></span><span style="height:9px"></span>
                  <span style="height:4px"></span>
                </div>
                <span class="vn-dur">1:23</span>
              </div>
              <span class="t">10:34 AM</span>
            </div>
            <div class="bbl in">
              क्या खूब यादें! आपकी कहानी सुरक्षित हो गई ✨<br>
              अगला सवाल सोमवार को आएगा।
              <span class="t">10:34 AM ✓✓</span>
            </div>
          </div>
          <div class="wa-inp">
            <span>Message</span>
            <span>🎤</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- QUOTE -->
<section class="quote-sec">
  <div class="reveal">
    <span class="qmark">"</span>
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
  <div class="cta-inner reveal">
    <p class="eyebrow">Start today</p>
    <h2 class="section-h">Their stories are waiting.<br>Don't wait too long.</h2>
    <p>Sign up takes two minutes. The memoir lasts forever.</p>
    <a class="btn-wa" href="mailto:vbajaj56@gmail.com?subject=smriti%20%E2%80%94%20get%20started">
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.117.554 4.107 1.523 5.83L0 24l6.364-1.499A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/></svg>
      Start preserving
    </a>
  </div>
</section>

<footer>
  <p>smriti &copy; 2026 &middot; Made with love for India</p>
  <span class="live"><span class="dot"></span> live</span>
</footer>

<script>
// ── BOKEH ANIMATION ──
(function(){
  const c = document.getElementById('bokeh');
  const x = c.getContext('2d');
  let W, H, P = [];
  const PAL = [
    [212,168,75],[212,168,75],[212,168,75],
    [180,120,40],[139,111,217],[255,195,110],
  ];
  function resize(){W=c.width=innerWidth;H=c.height=innerHeight}
  function mk(){return{
    x:Math.random()*W,y:Math.random()*H,
    r:50+Math.random()*110,
    a:0.022+Math.random()*0.048,
    dx:(Math.random()-.5)*.22,dy:(Math.random()-.5)*.16,
    col:PAL[Math.floor(Math.random()*PAL.length)],
    t:Math.random()*Math.PI*2,
    ts:.005+Math.random()*.008,
  }}
  function init(){P=Array.from({length:15},mk)}
  function frame(){
    x.clearRect(0,0,W,H);
    for(const p of P){
      p.t+=p.ts;
      const a=p.a+Math.sin(p.t)*.013;
      const g=x.createRadialGradient(p.x,p.y,0,p.x,p.y,p.r);
      g.addColorStop(0,`rgba(${p.col},${a})`);
      g.addColorStop(1,`rgba(${p.col},0)`);
      x.fillStyle=g;x.beginPath();x.arc(p.x,p.y,p.r,0,Math.PI*2);x.fill();
      p.x+=p.dx;p.y+=p.dy;
      if(p.x<-p.r)p.x=W+p.r;else if(p.x>W+p.r)p.x=-p.r;
      if(p.y<-p.r)p.y=H+p.r;else if(p.y>H+p.r)p.y=-p.r;
    }
    requestAnimationFrame(frame);
  }
  resize();init();frame();
  window.addEventListener('resize',()=>{resize();init()},{passive:true});
})();

// ── NAV ON SCROLL ──
(function(){
  const nav=document.getElementById('nav');
  const fn=()=>nav.classList.toggle('scrolled',scrollY>55);
  window.addEventListener('scroll',fn,{passive:true});fn();
})();

// ── SCROLL REVEAL ──
(function(){
  const io=new IntersectionObserver(entries=>{
    entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in')});
  },{threshold:.12});
  document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
})();
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing():
    return _PAGE
