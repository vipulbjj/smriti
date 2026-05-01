# smriti — Preserving the Voices of a Fading Generation

*smriti (स्मृति) — Sanskrit/Hindi for memory, remembrance, that which is worth keeping.*

Design doc: YC Office Hours session, 2026-05-02
Status: APPROVED
Mode: Startup / Pre-product

---

## The Problem

India is about to lose a generation of memory permanently.

The people who lived through Partition, the Emergency, the Green Revolution, the opening of the economy — they have no video record of their lives. Video didn't exist in rural and semi-urban India in the 1960s. Photographs exist, some. Voices do not.

When they pass, their stories go with them. A grandchild who didn't record their grandfather's account of walking from Lahore to Amritsar in 1947 cannot get it back. The window is 5–10 years. It is closing.

There is no product in India that makes it easy for an affluent grandchild to capture their grandparent's voice, stories, and life — and turn it into something the family can keep forever.

StoryWorth (US, $59–$199/yr) does this for American families: weekly email prompts to a grandparent, their written/voice replies collected, a hardcover memoir book produced after a year. It has zero India presence, no Hindi/regional language support, no video, no AI. The Indian market is untouched.

---

## Demand Evidence

- **Founder's lived pain**: He personally lost grandparent stories. This is not a market hypothesis — it is irreversible personal loss.
- **Status quo**: Indian families do nothing. Stories disappear. There is no existing workaround, no service, no product. The problem is invisible because no solution has surfaced it.
- **First identified customer**: Founder's sister — 32, architect, Chandigarh, parents and nanu aging. She has NOT yet been called. This is the most important gap in the current evidence base.

**Critical gap**: No paying conversation has happened yet. The first chapter of this company is 5 real conversations before any code is written or session is booked.

---

## Who Needs This

**The buyer**: 28–38, urban Indian (Bangalore, Mumbai, Delhi, Chandigarh, Pune), professional earning ₹15–80 LPA. Deep family values. Physically distant from aging grandparents. Carries quiet guilt about not visiting enough. Has disposable income and is willing to spend on meaningful gifts.

**The buying trigger**: A near-miss. A grandparent's health scare. A death in an adjacent family. A cousin's wedding where everyone notices the patriarch is slower than last year. Not abstract love of family — grief or the anticipation of grief.

**The subject**: Grandparent or aging parent, 65–85, lives in tier-1 or tier-2 India, speaks Hindi or a regional language, has never been on camera, has decades of stories no one has systematically captured.

**The narrowest wedge**: One in-person session. The founder visits a family with a recording setup, conducts a 1–2 hour structured conversation with the grandparent, and delivers: a 5-minute video, a preserved voice recording, and a 20-page printed photo storybook. Price: ₹25,000.

---

## What People Do Now

Three things — all inadequate:

1. **Nothing** (most common). The stories disappear.
2. **WhatsApp voice notes** — ad hoc, unstructured, saved on one person's phone, eventually lost.
3. **Hire a local videographer** — one-off, no structure, no prompts, no follow-through, no book.

The status quo competitor is inaction and grief. That is a beatable competitor.

---

## The Landscape

| Player | Geography | Model | Gap |
|---|---|---|---|
| StoryWorth | US only | Email prompts → hardcover book | No India, no Hindi, no video, no AI |
| Remento | US only | Video-based weekly prompts | No India |
| Tell Mel | US only | AI phone call interviews | No India |
| Local videographers | India | One-off sessions | No structure, no prompts, no book, not scalable |
| Indian Memory Project | India | Cultural/archival (public) | Not commercial |

No direct competitor in India at any price point.

---

## Premises

1. **The core pain is irreversibility.** Once a grandparent passes, their voice is gone. This is the emotional engine of the product and every piece of marketing.
2. **The buyer is the grandchild, not the grandparent.** Grandchild pays; grandparent participates. Same model as StoryWorth.
3. **Premium pricing is correct for the Indian market.** Mass-market pricing commoditizes a high-trust, high-emotion product and makes fulfillment economics impossible.
4. **Demand has not been validated.** Five real conversations before any build.
5. **AI is the long-term moat, not the launch requirement.** Voice cloning, photo-to-video, multilingual transcription are the defensible layer. They are not needed to prove demand in week 1.
6. **"StoryWorth for India" is a valid first wedge even without AI.** *(Contested by independent second opinion — see below. Empirical test recommended: show 10 potential customers both versions at their respective prices and observe which they choose.)*

---

## Cross-Model Second Opinion

Independent cold read (Claude subagent, no conversation history):

**Steelman**: "India is about to experience its first mass-mortality wave of the generation that lived through Partition, the Emergency, and liberalization. The window is 5-10 years and closing. A WhatsApp-native, AI-powered memory preservation service targeting affluent urban grandchildren is structurally superior to StoryWorth in every dimension: better distribution, stronger emotional urgency, no incumbent, and AI-generated artifacts a physical book cannot replicate. Done right, this is a ₹500Cr+ business with near-zero churn because the product is literally irreplaceable."

**What the conversation reveals**: *"I identified my sister — 32, architect, Chandigarh — as my ideal customer. But I have not called her."* This gap between intellectual conviction and a 10-minute phone call is the real risk. Not competition, not tech, not pricing.

**Challenged premise**: The subagent argues Premise 6 is wrong. A WhatsApp-prompt + printed book is replicable by any bootstrapped operation in 6 months. Without the AI layer, there is no defensible differentiation from a local videographer. Test: show 10 customers option A (prompts + book, ₹15k) vs option B (AI voice clone + animated video + book, ₹40k). If 6+ choose B, AI is load-bearing from the start.

**Synthesis**: The subagent is right about long-term defensibility, sequentially wrong. Proving demand does not require AI. Defending the business does. Validate demand without AI, add AI once 10 families are paying.

---

## Approaches Considered

### Approach A — The WhatsApp Wedge
Weekly story prompts via WhatsApp (Hindi/English). Grandparent replies by voice note. Human transcription + curation. Printed hardcover book at year-end.
- **Effort**: S (2–4 weeks to first paying family)
- **Risk**: Low
- **Pros**: India-native interface, fast to market, real revenue quickly
- **Cons**: Manual fulfillment, replicable, no long-term moat

### Approach B — The Memory Vault (Full Platform)
WhatsApp prompts + ElevenLabs voice cloning + photo animation (D-ID/RunwayML) + Sarvam AI Hindi transcription + printed book.
- **Effort**: XL (3–6 months to first paying family)
- **Risk**: High
- **Pros**: Defensible moat, premium pricing fully justified, true tech business
- **Cons**: 6 months before first rupee, high complexity before demand is proven

### Approach C — Concierge First *(chosen starting point)*
Founder personally conducts in-home interview sessions. Camera + microphone. Produces video, voice recording, and storybook manually. No tech — the founder is the product.
- **Effort**: M (can start this weekend)
- **Risk**: Lowest
- **Pros**: Fastest to paid revenue, teaches what families want before building, earns deep trust
- **Cons**: Founder's time is the bottleneck, capped at ~4 sessions/month, requires travel

---

## The Plan: C → A → B

### Phase 1: Concierge (Months 1–2)

Do 3–5 in-home sessions personally, in your home city only (travel makes economics negative at ₹25,000/session outside home base).

**Pricing for Phase 1**:
- Sessions 1–2: ₹10,000 ("founding family" pricing to reduce sales friction, build proof)
- Sessions 3+: ₹25,000

**What you learn**: What grandparents are willing to talk about. What triggers refusal or discomfort. What the grandchild cries about during the session. What the output should look and feel like. Whether ₹25,000 clears without negotiation.

**Equipment** (one-time, ~₹30,000): iPhone 15 Pro or equivalent + Rode Wireless GO II lapel microphone + ring light + tripod.

**Book production**: Test one vendor before the first paid session, using placeholder content. Start with Zoomin or Canvera. Turnaround time and quality must be verified before promising delivery to a paying family.

**Edge cases to handle**:
- **Grandparent refuses on the day**: Offer one reschedule, then refund. State this policy upfront.
- **Dementia/cognitive limitation**: Shorten session to 30 min, focus on photos rather than narrative. If family discloses this in advance, scope session accordingly.
- **Language barrier** (grandparent speaks only Punjabi/Tamil/etc.): Be upfront about which languages you can currently support. Phase 1 is Hindi + English only.

**IP ownership**: All recordings, transcriptions, and produced materials are transferred fully to the family upon payment. The founder retains no copy unless explicitly agreed in writing. State this before the session begins.

**Cancellation policy**: 50% refund if cancelled more than 48 hours before session. No refund within 48 hours.

### Phase 2: WhatsApp Wedge (Months 3–4)

While running concierge sessions, build the async product. Weekly prompts sent via WhatsApp Business API. Grandparent replies by voice note. Monthly human transcription. Book produced at year-end.

**WhatsApp API dependency**: Apply to Meta for WhatsApp Business API access immediately — approval takes 1–4 weeks and can be denied. Fallback if delayed beyond Week 6: run prompts via SMS (Twilio) or a manual WhatsApp personal account until approved. Do not block Phase 2 launch on API approval.

**What happens when a grandparent stops responding**: After 4 consecutive weeks of no response, send one human follow-up call. If no response in week 5, pause the subscription and notify the grandchild. Book is produced from stories captured so far; partial refund of remaining months is offered.

**Book format**: Auto-generated PDF from transcribed responses + uploaded photos, sent to Zoomin or Canvera for printing. 40–80 pages, hardcover, color interior. Design template created once and reused.

**Shareable output**: Every delivered product includes one 60-second video clip formatted for Instagram Reels and WhatsApp Status, in addition to the full book and recordings. This is the growth engine.

**Gate to Phase 2**: At least 3 completed concierge sessions with positive family feedback.

### Phase 3: AI Memory Vault (Month 5+)

Once 10 families are paying (across Phase 1 and Phase 2 combined), add the AI layer.

**Deliverable** (what a family receives in the AI Memory Vault tier):
- AI voice clone of the grandparent (ElevenLabs or Sarvam AI), delivered as a private audio file + optional voice chatbot ("talk to grandpa")
- 5–10 animated photo clips: old family photos brought to life with voice narration
- Full transcript in English and native language
- Hardcover printed memoir book, full color
- Private web link for the family to access all materials

**AI quality standard**: Voice clone must pass a blind listening test with 3 native speakers of the grandparent's language before delivery. If it doesn't pass, deliver the raw voice recording instead and note the limitation.

**Voice cloning requirements**: Minimum 15 minutes of clean audio (ElevenLabs professional quality). The concierge session recordings from Phase 1 may already satisfy this.

**Gate to Phase 3**: 10 paying families, positive NPS, at least one organic referral received.

---

## Pricing

| Tier | Price | What they get |
|---|---|---|
| Founding concierge (sessions 1–2) | ₹10,000 | 2-hr in-home session, 5-min video, voice recording, 20-page book |
| Concierge session | ₹25,000 | Same as above, full pricing |
| WhatsApp memoir subscription | ₹15,000/yr | Weekly prompts, year of stories, hardcover book at year-end |
| AI Memory Vault | ₹50,000–₹1,50,000 | Voice clone + animated photos + transcript + book + private web link |

**Year 1 revenue mix to reach ₹50L ARR** (illustrative):
- 20 concierge sessions × ₹20,000 avg = ₹4L
- 60 WhatsApp subscribers × ₹15,000 = ₹9L
- 20 AI Memory Vault packages × ₹1,00,000 avg = ₹20L
- Subtotal: ₹33L in-year + carryover from subscriptions ≈ ₹50L by Month 12
- This requires the AI layer to be live and selling by Month 6.

---

## Distribution

1. **Personal network first**: Make 20 personal calls to people you know with aging grandparents. These are the first customers. No marketing budget needed.
2. **Forward-ability**: Every delivered output must be beautiful enough that the grandchild shares it on Instagram Stories or WhatsApp. The 60-second shareable clip is designed for this. Word of mouth from a delivered product is the primary growth engine.
3. **Gifting occasions**: Position as "the most meaningful gift for a parent's birthday, Diwali, or a grandparent's 80th." The buying moment is an occasion, not a rational purchase.
4. **NRI/diaspora** *(Phase 3 and beyond)*: Indians living abroad with parents/grandparents in India have high willingness to pay, high guilt, and high emotional need. Instagram ads targeting NRI communities are a Phase 3 acquisition channel, not a launch priority.

---

## Open Questions

1. **Which language to start with?** Hindi is the obvious first, but the founder is based in Chandigarh — Punjabi may be equally relevant for Phase 1. Decide before booking the first session.
2. **Sarvam AI vs ElevenLabs for Hindi**: Test both with 5-minute samples before Phase 3. Minimum bar: synthesized voice passes blind test with 3 native speakers.
3. **Gifting occasion framing**: Is the trigger a birthday? A grandparent's health scare? A death in another family? The marketing message changes completely. Learn this from the first 5 conversations.
4. **Privacy and data handling**: Grandparent voice, family photos, personal stories — explicit consent design is required before any paid session, not as an afterthought. One-page consent form before recording begins.
5. **What does the concierge session actually look like?** The question list for the grandparent needs to be created before the first session. 30–40 structured questions: childhood, family, how they met their spouse, what India was like in the 1960s, what advice they'd give. StoryWorth's public question library is a useful starting reference.

---

## Success Criteria

| Milestone | Target |
|---|---|
| Week 1 | Call sister. Book the first session (free or ₹10k founding price). |
| Month 1 | 1 completed concierge session. Output delivered. Family happy. |
| Month 2 | 3 total sessions. At least 1 referral. Founding price raised to ₹25k. |
| Month 3 | WhatsApp flow live. First 5 async subscribers at ₹15k/yr. |
| Month 6 | 20 paying families across all tiers. NPS > 70. AI vault scoped. |
| Month 9 | AI Memory Vault live. First 5 vault packages sold. |
| Month 12 | 100 families. ₹50L ARR. At least 3 testimonials from grandchildren who lost a grandparent after capture. |

---

## The Assignment

**Call your sister today.**

Not to pitch her. Say: *"Nanu is aging. I want to record his stories — sit with him for an hour and ask him about his life. Can I come do that? I'll produce a short video and a book for the family. Founding price, basically free."*

She says yes. You go. You spend two hours with nanu. You record everything. You produce the output. You give it to the family.

That one session will teach you:
- What nanu is comfortable talking about (and what he isn't)
- What your sister cries about
- What the output should look and feel like
- Whether ₹25,000 is obviously right, obviously too high, or obviously too low

Do it before writing a single line of code, before designing a logo, before building anything.

---

## What I Noticed About How You Think

- You said *"I want to build a comprehensive platform, or you can say a service."* You're holding both — the tech platform vision and the human service reality — at the same time. That's the right tension. Most founders collapse it too early in one direction. Hold it longer.
- You said StoryWorth *"might not be very scalable"* and *"might require some human touch"* — then in the same breath said *"selling it to a premium and luxury audience is worthwhile."* You already know the answer. Premium + human touch + high price is the correct wedge. Trust that instinct.
- You pushed back when I said AI differentiation was required: *"we don't even need to differentiate a lot from StoryWorth — the same thing is not available in India."* That's a founder's conviction in the face of a challenge. The independent second opinion pushed back hard on this. The right answer is to test it empirically with 10 real conversations, not to decide it in a planning doc.
- The most revealing thing: *"I haven't talked to her."* You know exactly who your customer is. You have a direct line to her. The call is the entire next chapter.
