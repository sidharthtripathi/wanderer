# Wanderer — Engineering & Design Specification

> Source of truth for v1. Pairs with `wanderer_product_doc.md` (product intent). This doc covers what we're building, how it's wired, how it looks, and in what order.

**Status:** v1 spec, locked
**Platform:** Android only (Kotlin + Jetpack Compose)
**Region:** Functionally global from day one; primary infra in GCP `asia-south1` (Mumbai)
**Last updated:** 2026-05-06

---

## 0. How to read this doc

- Sections 1–2 set the rules of the game (principles, success criteria).
- Sections 3–5 are the system: architecture, services, data.
- Sections 6–8 are the AI brain: prompts, memory, narration loop.
- Sections 9–11 are the experience: design system, screens, motion.
- Sections 12–14 are the operating reality: performance, cost, build order.
- Section 15 lists known risks and open questions.

If you're building a feature, read 1, 2, the relevant service in 4, the relevant API in 5, the screen in 10, and the build slice in 14. That's enough to start.

---

## 1. Product Principles (non-negotiable)

These shape every decision below. When in doubt, return here.

1. **Anti-itinerary.** The journey is the product. Never pre-bake a trip; plan a rolling 30–60 min horizon.
2. **Ambient, not attention-demanding.** The app speaks only when there's something worth saying. Default to silence.
3. **Conversation > forms.** Vague prompts work. The user never builds an itinerary; they talk.
4. **Locals make it magical.** Community data is the moat. Contribution must feel like a TikTok post, not a TripAdvisor essay.
5. **Memory is contextual, not categorical.** "I didn't like that museum" never becomes "no museums ever."
6. **One global persona, regional flavor.** Same voice, local references.
7. **One mode, one user.** No group mode. One phone runs the session.
8. **The map is intent-filtered.** Only show what fits the current vibe. Never look like Google Maps.
9. **Magic in 60 seconds.** From cold app open to first useful suggestion ≤ 60s.
10. **Performance is a feature.** Smoothness equals trust.

---

## 2. v1 Success Criteria

Must hit all of these before we call v1 shipped.

| Metric | Target |
|---|---|
| Cold start → first AI suggestion | ≤ 60s (P75) |
| App start (cold) | ≤ 1.5s on Pixel 6-class device |
| Conversation token latency (text mode, first token) | ≤ 800ms (P75) |
| Voice-to-voice round trip latency | ≤ 1.2s (P75) |
| Voice interruption response (user starts speaking → AI audio stops) | ≤ 200ms |
| Map frame time during pan | ≥ 55 fps sustained |
| Crash-free sessions | ≥ 99.5% |
| Contribution flow time-to-submit | ≤ 90s for a post with 3 photos |
| Background battery drain (1 hour active wandering) | ≤ 8% on a 5000 mAh device |

---

## 3. System Architecture (HLD)

### 3.1 The shape of it

```
                       ┌────────────────────────────────────────┐
                       │           Android Client               │
                       │  Kotlin + Jetpack Compose + Mapbox     │
                       │                                        │
                       │  ┌──────────┐ ┌──────────┐ ┌────────┐  │
                       │  │ Convo UI │ │  Map UI  │ │ Contrib│  │
                       │  └────┬─────┘ └────┬─────┘ └───┬────┘  │
                       │       └────────┬───┴───────────┘       │
                       │       Domain layer (UseCases)          │
                       │       Data layer (Repos, Cache)        │
                       └────────────────┬───────────────────────┘
                                        │ HTTPS / WSS / gRPC-Web
                ┌───────────────────────┼───────────────────────┐
                │                       │                       │
       ┌────────▼─────────┐   ┌─────────▼────────┐   ┌──────────▼─────────┐
       │  AI Orchestrator │   │  Realtime Edge   │   │   Core API         │
       │  Python/FastAPI  │   │       Go         │   │   Python/FastAPI   │
       │                  │   │                  │   │                    │
       │ - Convo planner  │   │ - WebSocket hub  │   │ - Auth (Firebase)  │
       │ - Tool calls     │   │ - GPS ingest     │   │ - Community CRUD   │
       │ - Memory mgmt    │   │ - Narration loop │   │ - Subscription     │
       │ - Persona shaper │   │ - Pub/sub fanout │   │ - Points ledger    │
       └────┬─────────┬───┘   └──┬───────────┬───┘   └──┬──────────────┬──┘
            │         │          │           │          │              │
            ▼         ▼          ▼           ▼          ▼              ▼
       ┌────────┐  ┌──────────┐  ┌────────┐ ┌───────┐ ┌──────────┐ ┌─────────┐
       │ Gemini │  │ Qdrant   │  │ Redis  │ │ Pub/  │ │ Postgres │ │Firebase │
       │ 2.5    │  │ (vector) │  │ (cache,│ │ Sub   │ │+PostGIS  │ │ Auth    │
       │ Pro/Live│ │          │  │ pres.) │ │       │ │+ledger   │ │         │
       └────────┘  └──────────┘  └────────┘ └───────┘ └──────────┘ └─────────┘

                  ┌─────────────────────────────────────────────┐
                  │          Async Ingestion Pipeline           │
                  │  (Cloud Run jobs + Pub/Sub + Cloud Tasks)   │
                  │  - Google Places sync                       │
                  │  - OSM/Overpass enrichment                  │
                  │  - Atlas Obscura, Foursquare scrapes        │
                  │  - Community embedding refresh              │
                  │  - Freshness decay job                      │
                  └─────────────────────────────────────────────┘
```

### 3.2 Why this shape

- **Three services, not one.** AI orchestration (Python, slow, stateful per-request) and realtime (Go, persistent connections, low latency) have very different runtime profiles. Splitting now avoids a painful split later. Core API stays Python so we share the data layer with AI orchestrator.
- **Voice-to-voice direct to Gemini Live.** No STT/TTS sandwich. Lowest latency, smallest surface area.
- **Postgres + PostGIS + Qdrant.** One relational store with first-class geo, plus a dedicated vector DB for semantic recall on community knowledge. pgvector was considered; Qdrant won for hybrid search (geo + vector + payload filter) and clean separation of concerns.
- **Firebase only for auth.** We don't use Firestore or Realtime DB — they don't fit our query patterns. Auth alone is the cheapest, fastest way to ship Google + Phone OTP on Android.
- **Async ingestion is its own pipeline.** External API sync, embedding refresh, decay — none of that belongs on the request path.

### 3.3 Tech stack

| Layer | Choice | Why |
|---|---|---|
| Mobile | Kotlin 2.x, Jetpack Compose, Coroutines, Hilt | Native perf, modern UI, mature DI |
| Map SDK | Mapbox Maps SDK for Android v11+ | Custom styling, vector tiles, intent-filtered look |
| AI orchestration | Python 3.12, FastAPI, Pydantic v2 | LLM ecosystem maturity, dev velocity |
| Realtime | Go 1.22+, gorilla/websocket, gRPC for service-to-service | Concurrency, low memory per connection |
| LLMs | Gemini 2.5 Pro (planning/text), 2.5 Flash (narration triggers), Live API (voice) | One vendor, Indian context strong, multimodal native |
| Relational | PostgreSQL 16 + PostGIS 3.4 | Geo queries + transactional ledger in one place |
| Vector | Qdrant (self-hosted on GKE) | Open source, hybrid filter+vector search, single binary |
| Cache / pub-sub / presence | Redis 7 | Standard tool for this job |
| Async queue | GCP Pub/Sub + Cloud Tasks | Native, cheap, reliable |
| Object storage | GCS | Photos, audio caches |
| Auth | Firebase Auth (Google + Phone OTP) | Solved problem on Android |
| Payments | Google Play Billing v7+ | Mandatory for digital subs on Android |
| Push | FCM | Mandatory for Android |
| Analytics | PostHog (self-host, EU/India region) | Product analytics + feature flags + session replay |
| Crash | Firebase Crashlytics | Native Android integration |
| Infra | GCP `asia-south1`, GKE Autopilot, Cloud Run for jobs | DPDP-friendly region, low ops |
| CI/CD | GitHub Actions → Cloud Deploy | Standard |

---

## 4. Service-by-Service LLD

### 4.1 Android client

#### Architecture

Clean architecture, three layers:

```
ui/                  Compose screens, view-models, navigation
  ├── conversation/  primary surface
  ├── map/           map view, pin sheets
  ├── contribute/    post + review flow
  ├── profile/       points, subscription, history
  └── theme/         design tokens, typography, motion

domain/              UseCases (pure Kotlin, no Android deps)
  ├── conversation/  StartSession, SendMessage, EndSession
  ├── narration/     ObserveRouteHorizon, AcknowledgePin
  ├── community/     CreatePost, AddReview, FlagPlace
  └── points/        GetBalance, EarnPoints, SpendPoints

data/                Repositories, network, DB, mappers
  ├── network/       Retrofit + OkHttp + Scarlet (WebSocket)
  ├── persistence/   Room (local cache only)
  ├── audio/         AudioRecord + Oboe for low-latency capture/playback
  ├── location/      FusedLocationProvider, geofencing
  └── media/         CameraX, ExoPlayer
```

Key choices:

- **Compose-only UI.** No fragments, no XML. Navigation via Jetpack Navigation Compose.
- **Single-activity app.** One `MainActivity`, all screens are destinations.
- **Foreground service for active wandering.** When a session is live, a foreground service holds GPS + audio + WebSocket. User sees a persistent notification ("Wanderer is with you"). Goes away the moment the session ends.
- **Audio path is Oboe (C++ NDK)** for capture and playback — gives us 20–40ms lower latency than `AudioRecord`/`AudioTrack` defaults, which matters for voice-to-voice feel.
- **Map renders on its own SurfaceView**, lifted out of Compose where possible to avoid recomposition cost during pan/zoom.
- **Local cache is Room.** We cache: last 100 conversation turns per session, current horizon POIs, user profile, point balance. We do **not** cache the whole community DB.
- **Battery-aware GPS.** During an active session: `PRIORITY_HIGH_ACCURACY`, 2s interval. When stationary > 60s: drop to `BALANCED_POWER`, 10s. Resume high accuracy on motion.

#### Threading

- UI: main dispatcher, Compose-driven.
- Network/DB: `Dispatchers.IO`.
- Audio capture/playback: dedicated NDK thread, never blocked.
- Location updates: arrive on a single coroutine flow, debounced and pushed up the stack.

#### Modules (Gradle)

```
:app                  thin entry point
:feature:conversation
:feature:map
:feature:contribute
:feature:profile
:core:design          design tokens, theme, components
:core:domain
:core:data
:core:network
:core:audio
:core:location
:core:testing
```

### 4.2 AI Orchestrator (Python / FastAPI)

The brain. Owns conversation state, tool calls, memory, persona, and narration trigger logic.

#### Responsibilities

1. Accept conversation turns from client (text or voice via Live API session).
2. Build the system prompt (persona + city flavor + memory + horizon context).
3. Call Gemini with the right tools wired up.
4. Stream tokens / audio back to client via WebSocket bridge.
5. Persist memory updates (preferences, instances, mood) to Postgres.
6. Schedule narration evaluations on the route horizon.

#### Key endpoints (HTTP)

```
POST /v1/sessions                    create session, returns session_id + ws url
POST /v1/sessions/{id}/messages      text turn (streaming response)
POST /v1/sessions/{id}/end           graceful end + summary write
GET  /v1/sessions/{id}/horizon       current planned horizon (debug/devtools)
```

Voice-to-voice runs over WebSocket (see 5.2), not HTTP.

#### Internal modules

```
orchestrator/
  conversation/
    planner.py          turn planning, calls Gemini 2.5 Pro
    tools.py            tool definitions (search_pois, get_route, ...)
    streaming.py        token streaming wrapper
  voice/
    live_session.py     Gemini Live wrapper, audio frame relay
    barge_in.py         interruption handling: detect user speech, cancel in-flight audio
  memory/
    profile.py          long-term preferences (taste, pace, budget...)
    instance.py         "didn't like X museum" — scoped, not categorical
    mood.py             current session mood (decays after session)
    summarizer.py       end-of-session compaction
  persona/
    base_prompt.py      global persona spec
    regional_flavor.py  city → flavor pack (slang, food, refs)
  horizon/
    planner.py          rolling 30-60 min plan
    narration_picker.py what to surface, when
  cost/
    budget.py           token + tool cost accounting per session
```

#### Memory model — the contextual rule

The product doc is explicit: "I didn't like that museum" must never become "no museums." We enforce this in code.

We split memory into three stores, each with different lifetimes and matching rules:

1. **Profile** (persistent, broad preferences only)
   Examples: vegetarian, dislikes loud nightlife, prefers hill drives, budget mid.
   Written **only** when an inference reaches high confidence (3+ consistent signals across sessions). Never written from a single session moment.

2. **Instance** (persistent, scoped to a specific entity)
   Example: `{poi_id: musuem_xyz, sentiment: -0.7, note: "boring"}`.
   Always entity-scoped. Never generalized to category. Used to suppress *that POI*, not *its category*.

3. **Mood** (session-only)
   Current vibe, energy, hunger, group context for this session. Discarded at session end (a one-line summary survives).

The system prompt is built fresh each turn from: persona + city flavor + profile + relevant instances (filtered to the horizon) + current mood.

**Test of correctness:** "I didn't enjoy the Bombay museum" should change the user's `instance` for that POI but leave their `profile` untouched. Next trip, in Tokyo, the AI freely suggests the Edo-Tokyo Museum.

#### Tool surface (Gemini function calling)

| Tool | Purpose |
|---|---|
| `search_pois(query, lat, lng, radius_m, vibe, limit)` | Hybrid search: vector on description + geo + payload filter |
| `get_route(from, to, mode)` | Mapbox Directions API |
| `nearby_along_route(route_id, horizon_min)` | POIs the user will pass in next N min |
| `get_event_today(lat, lng, radius_m)` | Eventbrite/Meetup combined |
| `get_weather_now(lat, lng)` | Cached weather, used for vibe shaping |
| `recall_user_instance(poi_id)` | Did the user already react to this POI? |
| `flag_poi_closed(poi_id, evidence)` | Forwarded to moderation queue |
| `web_search(query, recency)` | Live web grounding via Gemini's built-in Google Search — used for freshness ("is this open today", "what's happening tonight") and for places not yet in our DB |

All tool calls run with hard timeouts (1.5s default, 3s for route) and degrade gracefully — Gemini gets an "unavailable" response and continues.

#### Persona prompt (v1, shipped in code)

```
You are Wanderer, a friend who has lived in {city} for years and loves showing
people around. You speak in {user_language}. You are warm, curious, never
pushy. You suggest, never instruct.

Local flavor for {city}: {flavor_pack}.

You point things out only when they genuinely matter. Long silences are fine.
Driving? Keep it short. Walking? You can be more conversational. Sitting? Tell
stories.

You remember what this user likes (broadly) and what they've already reacted
to (specifically). A bad museum once does not mean no museums forever.

You are not a search engine. You are a friend.
```

Regional flavor packs are short JSON files: a few slang terms, signature foods, neighborhood archetypes, do/don't notes. We start with hand-written packs for 3 seed cities (Gurgaon, Goa, Bangalore) and let Gemini infer for everywhere else with a "you have general knowledge of this city" fallback.

### 4.3 Realtime Edge (Go)

Owns persistent client connections, GPS ingest, narration evaluation.

#### Responsibilities

1. Hold one WebSocket per active session.
2. Receive GPS pings (1–2 Hz from client).
3. Maintain the rolling horizon by querying AI Orchestrator on a schedule.
4. Evaluate narration triggers (something interesting in the next 5–10 min).
5. Push narration events to the client (text + optional audio URL).
6. Bridge audio frames between client and Gemini Live for voice mode.

#### Why Go

- 10k+ concurrent WebSockets per pod cheaply.
- gorilla/websocket is battle-tested.
- Goroutines map naturally to per-connection state machines.

#### Per-session state machine

```
States: IDLE → PLANNING → CRUISING → NARRATING → CRUISING → ENDED
                  ↑__________________|

CRUISING:    GPS streaming, horizon valid, no triggers firing.
PLANNING:    Horizon being refreshed (every 5 min, or on user pivot).
NARRATING:   A trigger has fired; client is showing a pin/playing audio.
ENDED:       Session closed; cleanup; summary requested from orchestrator.
```

#### Narration trigger logic

A POI on the horizon becomes a narration candidate when **all** of:

- ETA from current location is between 4 and 10 minutes (sweet spot — not too close to feel rushed, not too far to feel premature)
- Score(POI) ≥ threshold (computed from community engagement, freshness, distance from route, vibe match)
- No narration has fired in the last 90s (rate limit — ambient, not chatty)
- The POI is not in the user's instance memory with negative sentiment

If multiple candidates qualify in the same evaluation tick, we pick the highest score and skip the rest until next tick.

#### GPS ingest

- Client sends GPS at 1 Hz when CRUISING, 0.5 Hz when stationary.
- Server applies a 5-point smoothing buffer to suppress jitter.
- Bearing is computed from last 3 fixes.
- Updates published to Redis Pub/Sub channel `session:{id}:gps`. AI Orchestrator subscribes when re-planning the horizon.

### 4.4 Core API (Python / FastAPI)

The boring but critical service. Auth, community CRUD, subscriptions, points.

#### Endpoints

```
# Auth (token verified against Firebase)
POST /v1/auth/exchange         Firebase ID token → backend session

# Profile
GET  /v1/me
PATCH /v1/me

# Community
POST /v1/posts                 create POI post
GET  /v1/posts/{id}
GET  /v1/posts?bbox=&vibe=&q=  search
POST /v1/posts/{id}/reviews
POST /v1/posts/{id}/like
POST /v1/posts/{id}/flag       closed/changed flag

# Subscription + Points
GET  /v1/subscription
POST /v1/subscription/verify   Play Billing receipt verification
GET  /v1/points/balance
GET  /v1/points/ledger?from=&to=
```

#### Points ledger

A double-entry style ledger in Postgres. Every change to a balance is a row, never an in-place update.

```sql
CREATE TABLE points_ledger (
  id            BIGSERIAL PRIMARY KEY,
  user_id       UUID NOT NULL REFERENCES users(id),
  delta         INTEGER NOT NULL,             -- can be negative
  reason        TEXT NOT NULL,                -- 'session_consume', 'post_reward', etc.
  ref_type      TEXT,                         -- 'session', 'post', 'review'
  ref_id        UUID,
  bucket        TEXT NOT NULL,                -- 'subscription' | 'earned' | 'topup'
  expires_at    TIMESTAMPTZ,                  -- subs reset monthly; earned 12mo
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON points_ledger (user_id, created_at DESC);
```

Balance = `SUM(delta)` of unexpired rows. Cached in Redis with a 60s TTL; the cache is invalidated synchronously on every write.

Earn cap (30–40% of top tier monthly allocation) is enforced at write time: before inserting an `earned`-bucket positive delta, sum the user's earned credits in the current calendar month; reject if it would exceed cap.

### 4.5 Ingestion / Enrichment Pipeline

Async, runs out-of-band on Cloud Run jobs.

#### Jobs

| Job | Cadence | What it does |
|---|---|---|
| `places_sync` | Daily per active region | Pulls Google Places into our POI table, dedupes against existing |
| `osm_enrich` | Weekly per region | Overpass queries for niche/free POI types we care about |
| `atlas_obscura_scrape` | Weekly | Crawls AO city pages, fits to our schema |
| `events_ingest` | 6× daily | Eventbrite + Meetup combined |
| `embedding_refresh` | On post create + nightly batch | Re-embeds posts whose text/photo changed |
| `freshness_decay` | Nightly | Downweights POIs with no engagement > 90 days |
| `flag_review_queue` | Manual | Routes user flags to moderators |

#### Embedding strategy

Each POI has a single embedding vector built from: name + curated description + top community-validated facts + category tags. We use `gemini-embedding-001` (1536-d). Vectors live in Qdrant; payload includes `lat`, `lng`, `vibe_tags`, `engagement_score`, `freshness_score`, `is_closed`. Searches always combine vector similarity with geo and payload filters.

---

## 5. APIs

### 5.1 REST conventions

- All endpoints under `/v1/`.
- Auth: `Authorization: Bearer <firebase_id_token>` on every call. Backend verifies + caches.
- All timestamps ISO 8601, UTC.
- Errors follow:
  ```json
  { "error": { "code": "POST_NOT_FOUND", "message": "...", "request_id": "..." } }
  ```
- Pagination: cursor-based. `?cursor=...&limit=20`. Response has `next_cursor`.

### 5.2 WebSocket protocol

One persistent connection per session: `wss://realtime.wanderer.app/v1/sessions/{id}/stream`.

Frames are JSON unless `binary=true` is negotiated for audio.

#### Client → server events

```jsonc
{ "type": "gps", "lat": 28.45, "lng": 77.05, "speed_mps": 12.3, "ts": "..." }
{ "type": "user_text", "text": "I'm bored, take me somewhere with a view" }
{ "type": "audio_frame", "seq": 142, "data": "<base64 pcm 20ms>" }   // voice mode
{ "type": "ack_pin", "poi_id": "..." }                                // user tapped a narration pin
{ "type": "mood_signal", "tag": "tired" }                             // optional explicit mood
{ "type": "end_session" }
```

#### Server → client events

```jsonc
{ "type": "agent_token", "delta": "There's ", "turn_id": "..." }      // streaming text
{ "type": "agent_audio_frame", "seq": 1, "data": "..." }              // streaming voice
{ "type": "narration", "poi_id": "...", "headline": "Chai stall in 7 min", "audio_url": "..." }
{ "type": "horizon_update", "pois": [...] }
{ "type": "tool_event", "name": "search_pois", "status": "ok" }       // for devtools
{ "type": "session_summary", "text": "...", "earned_points": 0 }
{ "type": "error", "code": "...", "message": "..." }
```

#### Reconnection

- Exponential backoff client-side: 1s, 2s, 4s, 8s, capped at 30s.
- Server retains session state for 5 min after disconnect; resumes if client reconnects with same session token.
- Audio frames in flight at disconnect are dropped (not buffered).

---

## 6. Data Model

Only the entities that matter for v1. Everything is in Postgres unless noted.

### 6.1 Entities

```sql
-- USERS
CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  firebase_uid    TEXT UNIQUE NOT NULL,
  display_name    TEXT,
  language        TEXT NOT NULL DEFAULT 'en',
  home_city_id    UUID REFERENCES cities(id),
  reputation_tier TEXT NOT NULL DEFAULT 'bronze',  -- bronze|silver|gold|legend
  reputation_score INTEGER NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at    TIMESTAMPTZ
);

-- CITIES (for flavor packs + admin)
CREATE TABLE cities (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  country         TEXT NOT NULL,
  centroid        GEOGRAPHY(POINT, 4326) NOT NULL,
  bbox            GEOGRAPHY(POLYGON, 4326),
  flavor_pack_v   INTEGER NOT NULL DEFAULT 1
);

-- POIs (the heart of the data layer)
CREATE TABLE pois (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source          TEXT NOT NULL,           -- 'community' | 'places' | 'osm' | 'atlas' | 'curated'
  source_ref      TEXT,                    -- external id when applicable
  city_id         UUID REFERENCES cities(id),
  name            TEXT NOT NULL,
  description     TEXT,                    -- curated/community description
  location        GEOGRAPHY(POINT, 4326) NOT NULL,
  vibe_tags       TEXT[] NOT NULL DEFAULT '{}',  -- 'food','nightlife','scenic',...
  category        TEXT NOT NULL,
  is_route        BOOLEAN NOT NULL DEFAULT FALSE,
  route_geom      GEOGRAPHY(LINESTRING, 4326),    -- when is_route=true
  engagement_score REAL NOT NULL DEFAULT 0,
  freshness_score  REAL NOT NULL DEFAULT 1,
  is_closed       BOOLEAN NOT NULL DEFAULT FALSE,
  created_by      UUID REFERENCES users(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX poi_geo_idx ON pois USING GIST (location);
CREATE INDEX poi_vibe_idx ON pois USING GIN (vibe_tags);

-- POSTS (community content layered onto POIs)
CREATE TABLE posts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  poi_id          UUID NOT NULL REFERENCES pois(id),
  author_id       UUID NOT NULL REFERENCES users(id),
  body            TEXT NOT NULL,
  best_time       TEXT,
  what_to_order   TEXT,
  who_for         TEXT,
  vibe_tags       TEXT[] NOT NULL DEFAULT '{}',
  photos          TEXT[] NOT NULL DEFAULT '{}',  -- GCS URIs, max 5
  like_count      INTEGER NOT NULL DEFAULT 0,
  status          TEXT NOT NULL DEFAULT 'live',   -- live|under_review|removed
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- REVIEWS
CREATE TABLE reviews (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_id         UUID NOT NULL REFERENCES posts(id),
  author_id       UUID NOT NULL REFERENCES users(id),
  body            TEXT NOT NULL,
  sentiment       REAL,                     -- -1..1, computed offline
  like_count      INTEGER NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- LIKES (uniform across posts and reviews)
CREATE TABLE likes (
  user_id         UUID NOT NULL REFERENCES users(id),
  target_type     TEXT NOT NULL,            -- 'post' | 'review'
  target_id       UUID NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, target_type, target_id)
);

-- FLAGS (closed / inaccurate / abusive)
CREATE TABLE flags (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flagger_id      UUID NOT NULL REFERENCES users(id),
  target_type     TEXT NOT NULL,
  target_id       UUID NOT NULL,
  reason          TEXT NOT NULL,            -- 'closed','wrong_info','abusive',...
  evidence        TEXT,
  status          TEXT NOT NULL DEFAULT 'pending',  -- pending|verified|rejected
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- SESSIONS (one per "wandering")
CREATE TABLE sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id),
  city_id         UUID REFERENCES cities(id),
  mode            TEXT NOT NULL,            -- 'voice' | 'text' (user-chosen, can flip)
  started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at        TIMESTAMPTZ,
  summary         TEXT,
  cost_points     INTEGER NOT NULL DEFAULT 0
);

-- MEMORY: PROFILE
CREATE TABLE memory_profile (
  user_id         UUID PRIMARY KEY REFERENCES users(id),
  data            JSONB NOT NULL DEFAULT '{}',  -- { dietary, pace, budget, mobility, ... }
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MEMORY: INSTANCE (entity-scoped reactions)
CREATE TABLE memory_instance (
  user_id         UUID NOT NULL REFERENCES users(id),
  poi_id          UUID NOT NULL REFERENCES pois(id),
  sentiment       REAL NOT NULL,            -- -1..1
  note            TEXT,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, poi_id)
);

-- SUBSCRIPTIONS
CREATE TABLE subscriptions (
  user_id         UUID PRIMARY KEY REFERENCES users(id),
  tier            TEXT NOT NULL,            -- 'free' | 'wanderer' | 'explorer'
  state           TEXT NOT NULL,            -- 'active'|'grace'|'paused'|'cancelled'
  current_period_start TIMESTAMPTZ,
  current_period_end   TIMESTAMPTZ,
  play_purchase_token  TEXT,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 6.2 Qdrant collections

| Collection | Vector source | Payload |
|---|---|---|
| `pois` | name + description + community summary | lat, lng, city_id, vibe_tags, engagement_score, freshness_score, is_closed, source |
| `posts` | post body + structured fields | poi_id, author_id, vibe_tags, like_count, created_at |
| `user_taste` | running summary of user's positive instances | user_id |

Hybrid search query example for "scenic spots near me, chill vibe":

```
vector = embed("scenic chill spots")
filter = {
  must: [{ geo_radius: { lat, lng, radius_m: 30000 } }, { is_closed: false }],
  should: [{ vibe_tags: "scenic" }, { vibe_tags: "chill" }]
}
```

### 6.3 Redis usage

| Key | Purpose | TTL |
|---|---|---|
| `points:bal:{user_id}` | Cached balance | 60s |
| `session:{id}:state` | State machine state | session-lifetime |
| `session:{id}:gps` | Pub/Sub channel | n/a |
| `session:{id}:horizon` | Current horizon (JSON) | 10 min |
| `narration:rate:{session}` | Rate-limit window | 90s |
| `firebase:token:{kid}` | Verification cache | 1h |

---

## 7. AI Layer in Depth

### 7.1 Conversation flow (text mode)

```
User taps send
  → Client posts to /v1/sessions/{id}/messages (SSE-style streaming response)
  → Orchestrator builds prompt: persona + flavor + memory + horizon + last N turns
  → Calls Gemini 2.5 Pro with tool surface
  → Streams tokens back to client as SSE
  → Tool calls (e.g., search_pois) run server-side, results fed back to model
  → On final token, orchestrator persists memory deltas & turn record
```

### 7.2 Conversation flow (voice mode — Gemini Live)

Voice mode is **always-on / hands-free** once the user enters it. Mic is open continuously, audio streams in both directions, the user can interrupt at any moment.

```
User taps mic → enters voice mode
  → Client opens continuous audio capture (Oboe, 20ms PCM frames)
  → Client streams frames to Realtime Edge over WS (uplink always live)
  → Realtime Edge bridges frames to a Gemini Live API session
       (one Live session per Wanderer session in voice mode)
  → Gemini Live streams audio response frames back
  → Realtime Edge relays to client; client plays via Oboe
  → Function calls from Live API are dispatched to AI Orchestrator
       (which executes tools and returns results to Live)
```

Why Realtime Edge mediates instead of client → Gemini Live direct: we need server-side tool execution against our DB and we don't want the API key on the device.

#### Interruption (barge-in) — first-class behavior

The user must be able to talk over the AI mid-sentence and have the AI stop and listen. Mechanics:

1. **Continuous uplink.** Client never stops sending mic frames in voice mode (subject to AEC, see below).
2. **Server-side VAD.** Gemini Live performs voice activity detection on uplink frames. When user speech is detected during active model output, Live cancels its in-flight audio response and begins listening.
3. **Client-side fast-cut.** The instant Realtime Edge sees a "user_speech_started" signal (either from Live or from a client-side VAD hint), it stops forwarding pending agent audio frames and the client flushes its audio output buffer within ~100ms. Combined target: ≤ 200ms from user speech onset to silence.
4. **Acoustic echo cancellation.** Android's `AcousticEchoCanceler` is enabled on the capture pipeline so the AI's playback doesn't get re-detected as user speech. Ducking on the playback side compounds this.
5. **Voice variability is acceptable.** We don't pin to a specific Gemini Live voice as a brand commitment. We pick a sensible default and allow the actual voice to evolve as Google updates the API. The product principle is "feels alive" (interruptible, quick, expressive), not "sounds like one specific person forever."

#### Audio path on the device

```
Mic ──► AEC ──► VAD hint ──► OkHttp WS ──► Realtime Edge ──► Gemini Live
                                                                  │
Speaker ◄── Oboe playback ◄── Audio frame queue ◄── Realtime Edge ◄┘
                  ▲
                  └── flushed on barge-in within 100ms
```

### 7.3 Mode switching

The user can flip between voice and text mid-session. We end the Live session cleanly (server side) and the next text turn picks up with all memory intact. We do not run both simultaneously.

### 7.4 Narration

System-initiated, not user-initiated. Lives entirely in the Realtime Edge state machine (4.3). When a trigger fires:

1. Realtime Edge asks AI Orchestrator: "Generate a one-line narration for POI X, user vibe Y, current activity Z."
2. Orchestrator calls Gemini 2.5 Flash (cheaper, faster) with a narrow prompt.
3. Optional: TTS the line via Gemini Live's voice in batch mode → upload to GCS → return URL.
4. Realtime Edge pushes `narration` event to client.
5. Client shows pin on map + plays audio if user is in voice mode.

Narration is **never** synthesized inside the conversation thread. It's a separate, ambient channel.

### 7.5 Cost & budget guardrails

Per-session budget tracker in Redis. We log estimated token spend per turn and per narration. If a session exceeds the user's tier hourly point allowance, we soft-warn the client and downshift narration frequency. We do not hard-cut a session mid-trip — that would feel hostile.

---

## 8. Community Layer

### 8.1 Contribution flow (≤ 90s target)

Five steps, each timeboxed in design:

1. **Drop pin** (≤ 10s) — map opens at user's GPS; one tap to confirm or drag to refine. Address auto-fills.
2. **Pick category** (≤ 5s) — visual chips, multi-select up to 3.
3. **Body** (≤ 30s) — single text field with three optional one-line prompts: "best time?" "what to order?" "who's it for?". No required fields besides body.
4. **Photos** (≤ 30s) — pick from gallery or camera. Up to 5. Compressed client-side.
5. **Submit** — post is `live` immediately; embedding generated async; first impression of community engagement starts the rep score.

### 8.2 Ranking

`composite_score = w1·engagement + w2·freshness + w3·vibe_match + w4·diversity_signal − penalty`

- `engagement` = log-scaled likes + reviewer-reputation-weighted reviews
- `freshness` = decay function `exp(-Δt / 90 days)` on most recent engagement
- `vibe_match` = cosine sim between query embedding and POI embedding
- `diversity_signal` = unique-IP / unique-device entropy of recent likers (anti-sockpuppet)
- `penalty` = closure flags, reputation hits

Weights start at `(0.35, 0.20, 0.35, 0.10)`. Tunable from a config service without redeploy.

### 8.3 Reputation

```
reputation_score = sum_over_user_content(
    likes_received * 1
  + reviews_received * 0.5
  + verified_flags * 5
  - removed_content * 20
)
```

Tiers: bronze < 50, silver 50–200, gold 200–1000, legend 1000+.
Rep is *influence* (review weight) not *gating* (everyone can post).

---

## 9. Design System

### 9.1 Design north star

- **Airbnb's warmth** — softness, generous whitespace, photography as a first-class element.
- **Cal.com's restraint** — typography does the heavy lifting; chrome stays out of the way.
- **A touch of Polywork's playfulness** — small, delightful details (motion, micro-copy) that make the app feel alive without being loud.

We are not loud. We are confident, warm, and quiet.

### 9.2 Color tokens

#### Light mode

| Token | Hex | Usage |
|---|---|---|
| `bg` | `#FBF4E8` | App background (warm cream) |
| `surface` | `#FFFEF9` | Cards, sheets |
| `surface-sunken` | `#F4EBDA` | Inset elements (chat input bg, etc.) |
| `ink` | `#2A2520` | Primary text (warm near-black) |
| `ink-muted` | `#6E665C` | Secondary text |
| `ink-subtle` | `#A89F92` | Placeholders, disabled |
| `border` | `#E8DFD0` | Hairlines |
| `primary` | `#C45A3F` | Terracotta — CTAs, brand |
| `primary-soft` | `#F5D8CC` | Primary background tint |
| `accent` | `#4A7C7E` | Muted teal — used sparingly |
| `success` | `#6B8E5A` | Sage |
| `warning` | `#C9974A` | Muted gold |
| `error` | `#B05545` | Brick |

#### Dark mode

| Token | Hex | Usage |
|---|---|---|
| `bg` | `#1A1714` | App background (warm near-black) |
| `surface` | `#25201C` | Cards, sheets |
| `surface-sunken` | `#13110F` | Inset elements |
| `ink` | `#F5EBDD` | Primary text (warm off-white) |
| `ink-muted` | `#A89B89` | Secondary text |
| `ink-subtle` | `#6E665C` | Placeholders, disabled |
| `border` | `#3A332D` | Hairlines |
| `primary` | `#E07559` | Terracotta — brightened for contrast |
| `primary-soft` | `#3D2520` | Primary background tint |
| `accent` | `#6FA5A8` | Muted teal — brightened |
| `success` | `#8FAB7F` |  |
| `warning` | `#E0B068` |  |
| `error` | `#D17363` |  |

**Palette discipline:** that's the entire palette. No additional brand colors. State colors (success/warning/error) appear only on toasts and validation — never decoratively.

### 9.3 Typography

Two families. Both load locally (bundled in APK), no runtime fetch.

- **Display: Fraunces** (variable, soft optical size, slight playfulness from `SOFT` axis at 50)
- **Body: Inter** (variable, used at `wght` 400/500/600)

Scale (line-height in parens):

| Token | Size / LH | Family / Weight |
|---|---|---|
| `display` | 40 / 48 | Fraunces 600, optical 60 |
| `h1` | 32 / 40 | Fraunces 600, optical 50 |
| `h2` | 24 / 32 | Fraunces 600, optical 36 |
| `h3` | 20 / 28 | Inter 600 |
| `body-lg` | 18 / 28 | Inter 400 |
| `body` | 16 / 24 | Inter 400 |
| `body-sm` | 14 / 20 | Inter 400 |
| `caption` | 12 / 16 | Inter 500 |
| `numeric` | 16 / 24 | Inter 500, tabular nums (points, time) |

Letter spacing: `-0.01em` on `display` and `h1`, default elsewhere. No all-caps text in the product except a single legal/system context.

### 9.4 Spacing & layout

4 px base unit.

| Token | px |
|---|---|
| `space-1` | 4 |
| `space-2` | 8 |
| `space-3` | 12 |
| `space-4` | 16 |
| `space-6` | 24 |
| `space-8` | 32 |
| `space-12` | 48 |
| `space-16` | 64 |

- Default screen horizontal padding: `space-4` (16).
- Card internal padding: `space-4` to `space-6`.
- Vertical rhythm between sections: `space-8`.
- Touch targets: minimum 48 × 48 dp.

### 9.5 Radius, elevation, motion

**Radius**

| Token | px |
|---|---|
| `radius-sm` | 8 |
| `radius-md` | 12 |
| `radius-lg` | 20 |
| `radius-xl` | 28 |
| `radius-pill` | 9999 |

Default: cards `radius-lg`, buttons `radius-pill`, inputs `radius-md`, modals `radius-xl` on top corners.

**Elevation**
Borders + soft tinted shadows over hard drop shadows.

| Token | Spec |
|---|---|
| `elev-0` | none, `1px border` |
| `elev-1` | `0 1px 2px rgba(42,37,32,0.06)` |
| `elev-2` | `0 4px 16px rgba(42,37,32,0.08)` |
| `elev-3` | `0 12px 32px rgba(42,37,32,0.10)` |

In dark mode, shadows fade and we lean on `border` and `surface` contrast instead.

**Motion**
- Standard ease: `cubic-bezier(0.2, 0.8, 0.2, 1)`.
- Spring for interactive feedback (Compose `spring(stiffness=Medium, damping=0.8)`).
- Durations: `fast` 120ms, `base` 200ms, `slow` 320ms.
- Honour `Settings → Reduce motion`. When enabled, no parallax, no spring overshoot, durations clamped to `fast`.

**Iconography**
One icon set: **Phosphor Icons (regular + duotone)**. 24 dp default. Duotone primary used sparingly on hero/empty states.

### 9.6 Component library

Every component built once in `:core:design`. Compose `@Preview` for every variant.

| Component | Variants | Notes |
|---|---|---|
| `Button` | primary, secondary, ghost, destructive | Pill radius, single weight per variant |
| `IconButton` | filled, ghost | 48dp tappable area |
| `TextField` | default, focused, error, with-icon | Single bottom border on focus, no boxes |
| `Chip` | choice, filter, removable | Used heavily for vibe tags |
| `Card` | flat, elevated, interactive | Default to flat — elevation is rare |
| `Sheet` | half, full, peek | Bottom sheets are the default modality |
| `MapPin` | poi, narration, route, user | Custom shapes per vibe category |
| `ChatBubble` | user, agent, narration | Agent uses Fraunces for first phrase, Inter after |
| `MicButton` | idle, listening, speaking | Animated radial pulse, `accent` color |
| `EmptyState` | first-time, no-results, offline | Always with a single CTA |
| `Toast` | info, success, warning, error | Top-anchored, auto-dismiss 4s |

### 9.7 Voice / tone (microcopy)

- Talks like a friend, not a brand.
- No exclamation marks except in genuinely warm moments (welcome, milestone).
- No "Awesome!" / "Great!". Use specific praise: "Nice spot to drop a pin."
- Errors say what happened, not what you did wrong: "I lost connection — retry?"
- Empty states are inviting: "No posts here yet. Drop a pin and start the story."

### 9.8 Accessibility

- Minimum text contrast 4.5:1 (verified for both modes against `bg` and `surface`).
- Every interactive element labelled for TalkBack.
- Dynamic type up to 200% supported on screens that don't run on the map canvas.
- Map screen: focus order goes search → mic → map; map gestures are escapable via a "list view" toggle for low-vision users.

---

## 10. Screens (UX)

Five top-level surfaces. Bottom navigation has three tabs: **Wander** (conversation), **Map**, **You**.

### 10.1 Onboarding (first 60 seconds)

```
[Splash 0.6s]
  ↓
[Welcome screen]   — single line: "Where's the wander tonight?"
                   — two CTAs: Continue with Google · Continue with Phone
  ↓
[Permission ask]   — location + notifications, one combined screen, plain language
  ↓
[Auto-detect city]  — "You're in Gurgaon. Want to explore?"
                    — show 3 starter prompts on warm cards (Fraunces headline)
                    — bottom: "Or tell me what you feel like..." input
  ↓
[Wander screen with first response streaming in]
```

No preference quiz. Profile gets built passively from the first conversation.

### 10.2 Wander (the conversation)

The home screen. Full-bleed warm `bg`. A scrollable conversation. At the bottom a unified input bar:

- Left: voice/text mode toggle (single tap to flip).
- Center: text input (when in text mode) OR live waveform (when in voice mode and listening).
- Right: send button (text) OR mic state pill (voice).

Agent bubbles render the **first phrase in Fraunces** (italic, warm), the rest in Inter. This single typographic move is the core of the brand feel.

When narration fires mid-session, a small inline card slides in between bubbles ("Chai stall in 7 min →") that the user can tap to open the map at that pin or dismiss.

### 10.3 Map

Mapbox custom style: cream/teracotta day, deep ink night. We strip:

- Department stores, generic retail, gas stations, parking
- ATMs, banks
- Highway annotations beyond essentials

We keep:

- Roads (varied weight by hierarchy, but quietly)
- Water, green spaces (slightly saturated for warmth)
- POI pins from our filtered set only

POI pins are intent-aware — the icon and color shift by vibe tag (food/nightlife/scenic/activity/hidden). Tap → bottom half-sheet with photos, body, key facts, "ask Wanderer about this" CTA.

A persistent FAB at top-right toggles a list view (accessibility + low-bandwidth fallback).

### 10.4 Contribute

Triggered from anywhere via long-press on map or "Share a place" in the You tab. The 5-step flow from §8.1, designed as a single vertically-scrolling sheet with progressive disclosure — feels like one screen, not a wizard.

### 10.5 You (profile)

Stack:

1. Identity card — name, city, reputation tier badge, member since
2. Points: current balance with a sparkline of the last 30 days
3. Subscription: tier, renewal date, "Manage" → Play Store
4. Recent contributions
5. Trip history (last 20 sessions, each a one-line summary)
6. Settings — language, mode preference (voice/text default), reduce motion, dark mode (auto/light/dark), data download, delete account

### 10.6 Empty / error states

| Surface | Empty | Error |
|---|---|---|
| Wander | Three suggested prompt chips + "Or just tell me what you feel like." | "I lost the thread. Retry?" with single retry CTA |
| Map | Single line in middle + chip cluster of suggested vibes | Inline banner, map stays interactive |
| Contribute | Pin first, the rest unlocks | Inline field-level errors |

---

## 11. Performance & Smoothness

What we do specifically to hit the §2 numbers.

### 11.1 Cold start (≤ 1.5s to interactive)

- Baseline Profile + Profile Installer enabled (`androidx.profileinstaller`).
- Precomputed Macrobenchmark profiles in CI; fail PR if startup regresses > 10%.
- Splash `<= 600ms` minimum-visible to mask Compose first-frame.
- Lazy-init non-critical singletons (analytics, billing client, map renderer) until after first frame.
- Map module deferred — not in start-path classpath.

### 11.2 First AI suggestion (≤ 60s cold)

- Fire `/v1/sessions` + auth refresh + GPS request **in parallel** the moment user lands on Wander.
- City detection uses last-known GPS first; only blocks on fresh fix if older than 10 min.
- Starter prompts are pre-cached per detected city (CDN-edged JSON, < 10KB).
- The "first response" stream begins as soon as Gemini emits the first token — usually 400–800ms after request.

### 11.3 Conversation latency

- Streaming SSE / WebSocket end-to-end. We render tokens as they arrive.
- On voice: Oboe ring buffer sized for 20ms frames; we never wait for a full sentence to start playback.
- We use Gemini's "low latency" tier for voice-to-voice.

### 11.4 Map performance

- Vector tiles only. No raster.
- POI pin layer is GeoJSON source updated diffed (only changed pins).
- Camera animations use Mapbox's native easing, not Compose-driven.
- Map view is hosted in a `AndroidView` with `remember`-stable update lambdas; all state writes funnel through a single `MapViewModel`.
- Pin clustering kicks in above zoom-out threshold to keep < 200 visible markers.

### 11.5 Battery during active wandering

- Single foreground service holds GPS + WS + audio.
- WebSocket ping interval 30s, pong 5s.
- GPS adaptive (see §4.1). On-screen-off, drop to `PRIORITY_BALANCED_POWER` and 10s interval.
- Audio capture only while mic is held / VAD active.
- Network: HTTP/2 + connection pooling; minimum DNS lookups.

### 11.6 Memory & jank

- Strict R8 + minify.
- `androidx.compose.runtime:runtime-tracing` in debug to spot recompositions.
- All lists use `LazyColumn` with stable keys.
- Images via Coil with explicit `size()` hints; no full-bitmap decodes.

---

## 12. Cost Notes (rough, illustrative)

Per active hour of voice mode (worst case): Gemini Live ~ ₹6–12 + tool calls ~ ₹1 + Mapbox ~ ₹0.5 + infra ~ ₹0.5 ≈ **₹8–14/hr**. A "Wanderer" tier user has ~500 points; if 1 hour costs 30 points, they get ~16 hrs/month, which feels right given the cap math in the product doc.

Hot spots to watch:

- **Voice tokens dominate.** Voice-to-voice is dramatically more expensive than text. We default new users to text and let them switch.
- **Google Places** charges per request — heavy use of `nearby` search burns money. We cache aggressively (15 min per geo-tile) and prefer our own POI table once seeded.
- **Embedding refresh** is cheap individually but adds up on community growth. We batch nightly.

---

## 13. Privacy, Trust, Compliance

- **DPDP Act 2023.** Data resident in `asia-south1`. Consent surfaces on signup. Right to erasure surfaced in `You → Settings → Delete account` (full pipeline within 30 days).
- **Location data** never sold or shared. Used only to power the active session and (with consent) to improve community ranking.
- **Voice audio** is streamed to Gemini Live in real time; we do not persist raw audio. Transcripts of voice conversations are persisted only when the user opts in.
- **PII** in posts is the contributor's responsibility. We strip EXIF GPS from uploaded photos by default unless the contributor explicitly opts in.
- **Children.** Minimum age 16 (signup gate). Aligned with DPDP under-18 consent rules.

---

## 14. Build Sequencing

A pragmatic 8–12 week MVP path. Each slice ends in something demoable.

### Slice 1 — Foundation (week 1–2)
- Repo, modules, CI, R8, baseline profiles
- Design system (`:core:design`) with tokens, typography, base components
- Firebase Auth (Google + Phone OTP) end-to-end
- Empty Wander screen behind auth
- Postgres + PostGIS + Qdrant + Redis up in `asia-south1`

### Slice 2 — Conversation, text mode (week 3–4)
- AI Orchestrator scaffold; Gemini 2.5 Pro wired with persona prompt and one tool (`search_pois`)
- Conversation screen, streaming bubbles, basic memory (profile + instance write paths)
- Hand-curated 100 POIs in Postgres + embeddings in Qdrant for one seed city
- Demo: text wander in Gurgaon, AI suggests real places

### Slice 3 — Map (week 5)
- Mapbox custom style (light + dark)
- POI pin layer, intent filtering by current session vibe
- POI detail sheet
- Map ↔ conversation cross-linking ("show me on map")

### Slice 4 — Voice mode (week 6–7)
- Realtime Edge service + WebSocket protocol
- Oboe-based audio path on client with continuous capture + AEC
- Gemini Live bridge with tool dispatch
- Barge-in / interruption handling (≤ 200ms target)
- Mode toggle + clean handoff between text/voice

### Slice 5 — Route narration (week 7–8)
- Foreground service, GPS ingest pipeline
- Horizon planner + narration trigger logic
- Narration cards in conversation, audio playback in voice mode

### Slice 6 — Community (week 8–9)
- Post creation flow (≤ 90s target measured)
- Reviews, likes, flags
- Embedding refresh job
- Ranking weights tuned on seed data

### Slice 7 — Subscription & Points (week 9–10)
- Play Billing integration
- Points ledger, earn cap enforcement
- Profile / You screen with balance & history

### Slice 8 — Polish & launch prep (week 10–12)
- Performance pass against §2 targets
- Crash + analytics dashboards
- Privacy flows (export, delete)
- Internal alpha → closed beta in seed cities

### What we are explicitly **not** building in v1

- Offline mode (post-launch)
- Affiliate booking integration (post-launch)
- Group mode (never)
- iOS / Web (post-launch)
- Multiple AI persona variants (single persona only)
- A signature, branded, permanent voice (we use Gemini Live's native voice; voice may evolve as Google updates the API — interruptibility and quickness are the priorities, not voice ownership)

---

## 15. Risks & Open Questions

### Designed-in: layered data fallback (not a risk)

The app works **anywhere from day one** because the AI synthesizes across four sources, in this priority order:

1. **Community posts** — highest trust when present; the local-tip texture
2. **External APIs** — Google Places, OSM/Overpass, Atlas Obscura, Foursquare, Eventbrite, Reddit, travel blogs (ingestion pipeline)
3. **LLM general knowledge** — Gemini already knows most cities, neighborhoods, famous and semi-famous places
4. **Live web grounding** — the `web_search` tool, used for freshness ("is this open today", "what's happening tonight") and for places not in our DB

In a city with rich community data (a seed city), source 1 dominates and the experience feels distinctly local. In a city with no community data, sources 2–4 carry it — the experience feels well-researched rather than locally-textured, but it never feels broken or empty. As community grows, source 1 progressively replaces the others.

This is the design, not a risk. Seed cities (2–3, hand-curated at launch) just front-load source 1 in the places we control.

### Known risks

| Risk | Mitigation | Owner |
|---|---|---|
| Voice cost runs away | Default new users to text; expose "voice minutes" remaining in UI; downshift narration on low budget | Backend + Client |
| Map feels generic if Mapbox style is wrong | Treat Mapbox style as a design artifact, not a config; iterate weekly | Design |
| Battery drain in active sessions | Strict adaptive GPS; profile every release | Client |
| Voice mode echo / false interruption | Android `AcousticEchoCanceler` + playback ducking + tuned VAD threshold | Client |
| Promotional spam in community | Reputation-weighted ranking, diversity signal, manual review of high-ranking POIs | Backend |
| Gemini Live voice changes mid-release breaking expectations | We accept this — voice is not a brand commitment. Pin a default and update if Google deprecates | AI Orchestrator |

### Open questions (to resolve during build)

1. **Subscription pricing** — A/B test ₹299/₹599 vs alternatives once we have ~500 weekly actives.
2. **Moderation team** — for v1, founder + one trusted contributor handle flags. Doesn't scale beyond ~5k DAU.
3. **Family / shared device** — ignored in v1. Revisit if observed in usage data.
4. **City-aware home tab** — when a user crosses cities, do we auto-pivot the suggestion set or wait for explicit prompt? Default: auto-detect, ask once: "Looks like you're in Goa now. Pick up here?"
5. **Push-to-talk fallback** — voice mode is hands-free by default. Do we offer a push-to-talk option for noisy environments? Decide after early user testing.

---

## 16. Glossary

- **Session** — One bout of wandering, from app-open intent to end. Has memory and a points cost.
- **Horizon** — The 30–60 minute forward window of route the AI plans for.
- **Narration** — A system-initiated, ambient note about something on the horizon.
- **Instance memory** — A user's reaction to a *specific* POI. Never generalized.
- **Profile memory** — A user's broad, persistent preferences. Updated only with strong evidence.
- **Vibe tag** — A short category-ish label for a POI: `food`, `nightlife`, `scenic`, `activity`, `hidden`, etc.
- **Wander loop** — A pre-curated 2–4 hour route through interesting spots.
- **Founding Local** — Permanent badge for early contributors in any seeded city.

---

*End of spec. If something here contradicts the product doc, the product doc wins on intent; flag and update this spec.*
