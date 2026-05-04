# Wanderer — Product Concept Document

> *An AI-powered, community-driven companion for spontaneous travel and unplanned wandering.*

---

## 1. The Core Idea

Most travel today is over-planned. When you research a destination — say Tokyo — you end up knowing exactly what you'll see, where you'll eat, and how you'll get around before you ever land. That's not travel anymore, it's **executing a mission**. The surprise is gone. The serendipity is gone. The feeling of being a wanderer is gone.

**Wanderer flips this.** Instead of planning a trip, you open the app and tell it what you feel like. The AI plays the role of a knowledgeable local — like a friend who's lived in the city for years — and guides you through the journey in real time. It surfaces what's worth seeing, where to eat, what's special about the road you're driving on, what events are happening tonight, what hidden experiences exist nearby (haunted houses inside malls, scuba diving spots, rooftop bars, bungee jumps, secret viewpoints, anything).

The big shift: **the journey is the product, not just the destination.** Driving past Marine Drive at sunset, or down a smooth winding road through the hills, or alongside a sea-facing stretch — these *are* experiences. Wanderer treats them as first-class content, not as filler between attractions.

You can use it for:

- An **evening drive** in your own city — just take the car out, the AI plans a loose route and tells you what's interesting along the way
- **Landing in a new city** with zero plan and being walked through it like a local would
- **A multi-day spontaneous trip** where the next move is decided as you go, not pre-locked weeks ago

The whole product is anti-itinerary. It's designed for people who believe being lost on purpose is the best way to find something.

---

## 2. How the Experience Works

### 2.1 The Conversational Loop

The heart of the app is a conversation with the AI guide. The user tells it what they want — vague or specific — and the AI plans accordingly:

> "I just want to drive somewhere chill tonight."
> "I'm in Goa, take me out for nightlife."
> "Find me something with high adrenaline."
> "I'm hungry but bored of regular restaurants."

The AI responds with a plan and starts the journey. Mid-trip, the user can keep talking to it, naturally:

> "I didn't enjoy that museum, skip the next one."
> "Take me somewhere with a view instead."
> "What's that place we just passed?"
> "I'm tired, find me a cafe to sit for a while."

The AI updates the wandering in real time. It feels like texting a friend who knows the city, not like prompting an LLM.

### 2.2 Memory and Personalization

The app builds a profile of each user over time — taste, pace, budget, dietary preferences, mobility, travel style. This memory persists across trips and cities.

**Important nuance:** memory is contextual, not categorical. If a user dislikes one museum, the app does *not* permanently filter out all museums. A different museum elsewhere might be exactly their thing. Same for food — bad pizza in one place doesn't mean no Italian ever again. The AI is intelligent enough to understand specific instances vs. broad rejections.

### 2.3 Route-Aware Narration

When the user is moving — driving, walking, riding — the AI tracks GPS in real time and surfaces highlights along the route.

**The mechanic:**

- The AI plans a **rolling 30-60 minute horizon** of the route ahead
- As the user moves, it refreshes that horizon — never pre-loads the whole trip (kills spontaneity, wastes compute)
- When something interesting is **5-10 minutes ahead**, the AI surfaces it
- The user gets a light pin on the map + an optional audio/text note ("there's a great chai stall on your right in 7 minutes — locals come here after work")
- The user can pause, take it in, or keep moving — the app doesn't demand attention

This is **ambient, not attention-demanding**. The driver isn't constantly looking at the screen. They follow the map naturally and the highlights appear when relevant.

The narration is not random "look this, look that" every 30 seconds. The AI only speaks when there's actually something worth pointing out — a scenic stretch, a notable spot, a local-favorite detour.

### 2.4 The Map (Filtered View)

The map is the second pillar of the experience. It does not look like Google Maps. It strips out everything irrelevant — department stores, gas stations, generic retail — and shows only what fits the user's current vibe and prompt:

- Bars, clubs, cafes
- Museums, galleries, viewpoints
- Activity spots (bungee, scuba, skydive, haunted houses, escape rooms, etc.)
- Food spots — both famous and hidden
- Markets, street food zones
- Live events tonight
- Scenic stretches and notable roads themselves

The user sees a clean, intent-aware map that surfaces only what matters for the kind of evening or trip they're on.

### 2.5 The Onboarding — First 60 Seconds

When a brand-new user opens the app:

1. **Auto-detect city.** "You're in Gurgaon."
2. **AI generates 3-4 starter suggestions based on the city, time, and weather.** Examples might be "a chill night drive towards Damdama Lake," "rooftop bars in Sector 29," "underrated late-night food in Old Gurgaon."
3. **The user can pick one or write their own prompt freely.**
4. The journey starts.

The goal is to go from app-open to "magic moment" in under 30-60 seconds. No long signup, no preference quiz, no itinerary builder.

### 2.6 Mid-Trip Conversation

The AI is not just a one-shot planner. Throughout the journey it can:

- Proactively check in ("you've been driving 40 minutes, want to stop somewhere?")
- Respond to user mood ("I'm bored" → adjust direction)
- Take real-time prompts ("I want something with adrenaline now")
- Replan routes when the user pivots
- Explain things on demand ("what was that monument we just passed?")

It's voice-first when driving, text-first when walking or planning, flexible when sitting somewhere.

---

## 3. The Community Layer

This is what makes the AI feel like a local, not like a chatbot reading Wikipedia.

### 3.1 Why Community Data Matters

Locals know things APIs don't. They know:

- Which biryani shop is actually good vs. which one bought five-star reviews
- Which auto-rickshaw route gets you to the temple faster than Google's car-route
- Which beach has clean water on weekdays but is unswimmable on weekends after the crowd
- Which mall has a hidden haunted house on the third floor most people never visit
- Which road feels magical at sunset
- Which alley in the market has the best samosa even though it's not on Google

Wanderer collects this knowledge from the people who actually live there.

### 3.2 How Contributions Work

A contribution is either a **post** (creating a new place/route entry) or a **review** (commenting on an existing one).

**Creating a post:**

1. The contributor searches for the place or region they want to talk about
2. They drop a precise pin on the map (or define a region/route) — this gives the AI exact geolocation, not just a name
3. They write what's special about it — what to do, what time is best, what to order, what to avoid, who it's right for
4. They tag categories (food / nightlife / scenic / activity / hidden gem / etc.)
5. They submit

**Reviews:**

- Anyone can comment on existing posts
- Reviews are also part of the community signal — they validate, contradict, or add nuance to original posts
- Reviews themselves can earn likes and engagement, so reviewers are also rewarded

**The 90-second target:** the post-creation flow has to feel like a TikTok post, not a TripAdvisor essay. If contributing takes 10 minutes, locals won't do it.

### 3.3 How the AI Uses Community Data

Periodically, the AI ingests community contributions and updates its internal model of each city — what's there, what's worth recommending, what fits which user vibe.

**Ranking logic** mirrors how search engines work:

- Posts with high genuine engagement (likes, positive reviews from diverse contributors) rank higher
- Posts with low or fake-looking engagement rank lower
- A promotional post about "best biryani" that the community ignores won't surface — meanwhile the actual local favorite, validated by many independent reviewers, will dominate
- The AI is intelligent enough to read sentiment in reviews, not just count them

**Conflict resolution between locals:** whichever version the broader community supports wins. If two contributors disagree on which spot is better, the one with more diverse, organic backing ranks higher.

### 3.4 Solving the Cold-Start Problem

At launch, community data will be sparse. The app handles this by layering:

1. **Community data first** (priority when available)
2. **External APIs and sources** to fill gaps:
 - Google Places API for base POI layer
 - OpenStreetMap / Overpass API for niche / free data
 - Foursquare for vibe-based categorization
 - Atlas Obscura for quirky / hidden spots
 - Eventbrite / Meetup / Bandsintown for live events
 - Reddit (city subs) for vibe and recency
 - Travel blogs and Twitter scraping for color and storytelling
3. **As the community grows in a city, community data progressively replaces external data.**

This means the app works on day one (good enough), and gets dramatically better as the community builds up.

### 3.5 Data Quality and Trust

**Reputation system:**

- Every contributor builds a reputation score over time, based on how their content is received
- Higher-reputation contributors' posts and reviews are weighted more heavily
- BUT — a brand new contributor with a genuinely loved post can break through. Reputation is influence, not gatekeeping.

**Freshness:**

- Places close. Restaurants change menus. Roads get blocked.
- Users can flag a place as closed/changed and earn points for verified flags
- Backend manually reviews flags before removal
- The system has freshness decay built in — old posts without recent engagement get downweighted automatically

**Anti-spam / anti-gaming:**

- A café owner getting 5 friends to upvote their own posts won't outrank genuine community favorites — because the wider community is the actual filter
- Engagement is weighted by reviewer reputation and diversity (not raw count)
- Sockpuppet rings are caught by geo-diversity, device fingerprinting, and engagement pattern analysis
- High-ranking POIs may get periodic manual review

**Conflict resolution:** community vote, broadly defined, wins.

---

## 4. Business Model

### 4.1 Why Points + Subscription

The app costs real money to run — AI inference, map APIs, infrastructure. So users have to pay something. But Wanderer has a second goal: **incentivize locals to contribute high-quality data**, because that's what makes the AI feel magical.

Points solve both. Users pay to use the AI. Contributors can earn points by sharing what they know, which discounts their own usage when they travel elsewhere.

### 4.2 The Model: Subscription + Earnable Discount

**Subscription tiers (illustrative):**

| Tier | Price | Monthly Points |
|------|-------|----------------|
| Free | ₹0 | Small bucket — taste of the product |
| Wanderer | ~₹299/mo | ~500 points |
| Explorer | ~₹599/mo | ~1000 points |

(Exact pricing to be A/B tested at launch.)

**Earnable layer:**

- Users can earn additional points through community contribution
- **Capped at ~30-40% of the highest tier's monthly allocation** (so up to ~300-400 bonus points/month for an Explorer-tier user)
- Earned points come from quality posts, helpful reviews, verified closure flags, and engagement on contributions

**Why the cap:**

- Without it, top contributors use the app entirely free → no revenue
- With too low a cap, contribution feels pointless
- 30-40% is the sweet spot: a great Gurgaon contributor really can offset most of their Goa trip, but everyone still pays a base subscription

**Indicative point economy:**

| Action | Points |
|--------|--------|
| AI guide session | ~20-50 / hour (varies by mode — driving narration costs more than a quick query) |
| Quality post (high engagement) | 30-80 |
| Helpful review | 5-20 |
| Verified closure / freshness flag | 10 |
| Monthly earn cap | ~400 points (≈ 10-15 hours of guide use) |

**Credit rules (industry standard):**

- Subscription points reset monthly (don't roll over)
- Top-up / earned points are valid for 12 months
- This pattern is used by Google AI, JetBrains, RemNote, Fireflies — proven to work

### 4.3 Why This Beats Alternatives

| Goal | How this model delivers |
|------|-------------------------|
| App makes money | Subscription is the floor — every active user pays |
| Discount feels valuable | 30-40% off through contribution is real, brag-worthy |
| Not too easy | Monthly cap prevents pure freeloading |
| Not too stingy | Top contributors save serious money |
| Status matters | Reputation tiers (Bronze / Silver / Gold / Local Legend) unlock visible badges, not just points |

The app should feel **rewarding** to contribute to without feeling **exploitable**.

### 4.4 Secondary Revenue (Roadmap)

Once the user base is established, natural affiliate revenue opportunities open up:

- Activity bookings (bungee, scuba, paragliding, etc.)
- Hotel / hostel referrals
- Restaurant reservations
- Event tickets

Placement matters — affiliate suggestions only appear at natural decision points ("want to do bungee at this spot?"). Never injected as ads. The user experience is the product.

### 4.5 What the App Does NOT Do

- No display ads inside the experience
- No selling user location data to third parties
- No paid placement ranking — community ranks everything organically

---

## 5. Modes and Modalities

### 5.1 Online Mode (Primary)

Full AI guide experience. Real-time conversation, route-aware narration, live map, community data, all external APIs. This is what most users get most of the time.

### 5.2 Offline Mode (Fallback)

For travelers in areas with poor connectivity (international roaming dead zones, hilly regions, etc.):

- The app downloads relevant map data and the offline AI model in advance
- Uses **Gemma 3n** (Google's mobile/edge model designed to run on phones) for on-device inference
- Functionality is reduced — works like a basic enhanced map with simple natural-language search ("find me a hostel nearby," "where's the closest food")
- No live community data, no real-time narration
- Core fallback so the app never feels broken

> **Note:** Originally referenced "Gemma 4" — this doesn't exist yet. Gemma 3n is the current correct model for mobile/edge AI.

### 5.3 Voice vs Text

- **Driving** → voice-first (hands-free, ambient narration)
- **Walking** → either, user's choice
- **Planning / sitting** → text-first

The interface flexes based on context.

### 5.4 Group Mode

There is no group mode. The app speaks to one person, one session at a time. If a group is wandering together, they decide among themselves whose phone runs the app. The host's prompts and preferences drive the session.

This keeps the product simple and avoids the hard problem of reconciling conflicting preferences across multiple users.

---

## 6. AI Persona and Voice

The AI has **one consistent global persona** — a friendly, knowledgeable local-guide character.

But it adopts **regional flavor** in every city. The same persona, speaking the user's preferred language (Hindi, English, whatever the user sets), naturally references local culture:

- In Goa: "this is what locals call *susegad* — basically chill mode"
- In Tokyo: drops Japanese honorifics and food terms naturally
- In Delhi: knows the difference between Old Delhi and Lutyens', uses local slang where it fits
- In Texas: regional vernacular and cultural references

The user's preferred language stays whatever they pick in their profile. The flavor comes from local references, slang, food terms, and cultural context — not from forcing them to read a different language.

This is a prompt-engineering problem, not a model-training one. Easy to implement, big impact on feel.

---

## 7. Safety and Policy

### 7.1 Position

Wanderer is a guide, not a guarantor. The same way Google Maps isn't liable if a driver gets lost in a bad neighborhood, Wanderer surfaces what's interesting but cannot take responsibility for everything that happens during a user's trip.

### 7.2 Built-In Safeguards

- **Community signal does most of the work.** Shady places get bad reviews. Unsafe areas get flagged. The AI is intelligent enough to read sentiment and downrank accordingly.
- **Contextual filtering** for high-risk combinations (e.g., solo female traveler at night → routes and spots that the community has signaled as safe get prioritized).
- **Activity recommendations** with inherent risk (bungee, scuba, skydive) come with disclaimers and the user's own consent step.
- **Clear ToS** — the user acknowledges that recommendations are community-sourced and decisions are their own.

### 7.3 Content Policy

- Verified-closed places get removed quickly via the flag system
- Posts that promote illegal or harmful activity are removed by moderation
- Reputation can be revoked for bad-faith contributors

---

## 8. Bootstrap Strategy

### 8.1 Launch with One City

Pick one city with a known local — ideally one of the founders' home cities (e.g., Gurgaon). Hand-curate **200-300 highlight POIs** across food / nightlife / experiences / scenic routes, plus **20-30 pre-built wander loops** of 2-4 hours each.

This is a few weeks of focused work and gives the AI enough context to feel magical from day one.

### 8.2 Seed the Community

- Recruit 50-100 enthusiastic locals as founding contributors
- Give them generous launch-period point bonuses
- Create a "Founding Local" badge that's permanent and visible — status-driven incentive
- Host local meetups in launch cities to build identity around the contributor community

### 8.3 Expand by City, Not by Country

Don't try to be global on day one. Expand one city at a time, repeating the pattern: hand-curate a base layer, recruit founding locals, layer in external APIs, let the community grow it.

### 8.4 Validation Milestones Before Expansion

For each city before declaring it "ready":

- 300+ quality POIs (mix of curated + community)
- 50+ active contributors
- 10+ wander loops with positive feedback
- AI conversations that feel local, not generic

---

## 9. Risks and How They're Mitigated

| Risk | Mitigation |
|------|------------|
| Cold-start: no community data at launch | External APIs + hand-curated launch base + founding contributor program |
| Promotional spam / paid reviews | Community-weighted ranking; spam can't outshine genuine engagement |
| Stale data (closed places, wrong info) | User-flagged closure system + freshness decay + manual review |
| Conflicting recommendations between locals | Broader community engagement decides |
| Sockpuppet rings inflating reputation | Geo-diversity checks, device fingerprinting, engagement pattern analysis |
| Driver distraction from narration | Ambient design — pins and optional audio, not constant voice |
| Liability for activity recommendations | Disclaimers, user consent, community signal filtering |
| AI feels generic | Regional persona flavor + community data backbone |
| Contribution flow too slow → no content supply | 90-second post-creation target, sub-2-minute UX requirement |
| Points feel pointless OR too generous | 30-40% cap; A/B test exact ratios |

---

## 10. What v1 Looks Like (Recommended Scope)

To avoid endless brainstorming and actually ship:

**Launch city:** Gurgaon (or whichever city the team knows deeply).

**Core features:**

1. **Conversational AI guide** with memory and mid-trip updates
2. **Filtered map view** showing only relevant POIs based on user vibe
3. **Route-aware narration** with rolling 30-60 min horizon
4. **Community contribution flow** (post + review + likes/engagement)
5. **Subscription + earnable points** monetization

**Cut from v1:**

- Offline mode (add later, after online experience is dialed in)
- Affiliate booking integration (add once base experience proves out)
- International expansion (one city first)
- Multiple persona variants
- Group mode (never — out of scope by design)

**The first user is the founder.** If the founder can't take an evening drive in their own city using v1 and have a magical experience, nothing else matters yet.

---

## 11. Open Build-Time Decisions

These are not idea-stage questions, but they will need answers during build:

- Exact subscription pricing (A/B test)
- Tech stack (mobile framework, backend, vector DB for community knowledge, model choices for online inference)
- Specific external API mix and budgeting (Google Places gets expensive at scale)
- Contribution UI (Figma → prototype → time-test)
- Moderation team structure
- Legal entity and ToS
- Customer support model

---

## 12. The One-Sentence Pitch

> **Wanderer is the app for people who think the journey matters more than the destination — an AI local guide that turns any evening, any city, any unplanned moment into a real experience, powered by the people who actually live there.**

---

## Appendix: Glossary

- **POI** — Point of Interest. Any place worth visiting (cafe, bar, viewpoint, activity, etc.).
- **Wander loop** — A pre-curated 2-4 hour route that flows naturally through interesting spots.
- **Rolling horizon** — The 30-60 minute window of upcoming route the AI plans for at any time.
- **Founding Local** — Permanent badge for early contributors in each city.
- **Reputation score** — A contributor's standing, built from community engagement on their posts/reviews.
- **Freshness decay** — Automatic downweighting of old posts without recent engagement.
- **Susegad** — Konkani term for a relaxed, unhurried way of life. Example of the kind of local-flavor reference the AI should know.

---

*End of document.*
