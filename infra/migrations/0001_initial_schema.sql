-- 0001_initial_schema.sql
-- Maps to spec.md §6.1. Run after 01-extensions.sql.

BEGIN;

-- ─────────── USERS ────────────────────────────────────────────────────────
CREATE TABLE users (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid     TEXT UNIQUE NOT NULL,
    display_name     TEXT,
    language         TEXT NOT NULL DEFAULT 'en',
    home_city_id     UUID,
    reputation_tier  TEXT NOT NULL DEFAULT 'bronze'
        CHECK (reputation_tier IN ('bronze', 'silver', 'gold', 'legend')),
    reputation_score INTEGER NOT NULL DEFAULT 0,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at     TIMESTAMPTZ
);
CREATE INDEX users_firebase_uid_idx ON users (firebase_uid);

-- ─────────── CITIES ───────────────────────────────────────────────────────
CREATE TABLE cities (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    country       TEXT NOT NULL,
    centroid      GEOGRAPHY(POINT, 4326) NOT NULL,
    bbox          GEOGRAPHY(POLYGON, 4326),
    flavor_pack_v INTEGER NOT NULL DEFAULT 1,
    is_seed       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX cities_centroid_idx ON cities USING GIST (centroid);
CREATE UNIQUE INDEX cities_name_country_idx ON cities (lower(name), lower(country));

ALTER TABLE users
    ADD CONSTRAINT users_home_city_fk
    FOREIGN KEY (home_city_id) REFERENCES cities(id) ON DELETE SET NULL;

-- ─────────── POIs ─────────────────────────────────────────────────────────
CREATE TABLE pois (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source           TEXT NOT NULL
        CHECK (source IN ('community', 'places', 'osm', 'atlas', 'curated')),
    source_ref       TEXT,
    city_id          UUID REFERENCES cities(id) ON DELETE SET NULL,
    name             TEXT NOT NULL,
    description      TEXT,
    location         GEOGRAPHY(POINT, 4326) NOT NULL,
    vibe_tags        TEXT[] NOT NULL DEFAULT '{}',
    category         TEXT NOT NULL,
    is_route         BOOLEAN NOT NULL DEFAULT FALSE,
    route_geom       GEOGRAPHY(LINESTRING, 4326),
    engagement_score REAL NOT NULL DEFAULT 0,
    freshness_score  REAL NOT NULL DEFAULT 1,
    is_closed        BOOLEAN NOT NULL DEFAULT FALSE,
    created_by       UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX pois_location_idx     ON pois USING GIST (location);
CREATE INDEX pois_route_geom_idx   ON pois USING GIST (route_geom) WHERE is_route;
CREATE INDEX pois_vibe_tags_idx    ON pois USING GIN  (vibe_tags);
CREATE INDEX pois_city_idx         ON pois (city_id);
CREATE INDEX pois_engagement_idx   ON pois (engagement_score DESC) WHERE NOT is_closed;
CREATE UNIQUE INDEX pois_source_ref_idx ON pois (source, source_ref) WHERE source_ref IS NOT NULL;

-- ─────────── POSTS ────────────────────────────────────────────────────────
CREATE TABLE posts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poi_id        UUID NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    author_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body          TEXT NOT NULL,
    best_time     TEXT,
    what_to_order TEXT,
    who_for       TEXT,
    vibe_tags     TEXT[] NOT NULL DEFAULT '{}',
    photos        TEXT[] NOT NULL DEFAULT '{}'
        CHECK (cardinality(photos) <= 5),
    like_count    INTEGER NOT NULL DEFAULT 0,
    status        TEXT NOT NULL DEFAULT 'live'
        CHECK (status IN ('live', 'under_review', 'removed')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX posts_poi_idx     ON posts (poi_id);
CREATE INDEX posts_author_idx  ON posts (author_id);
CREATE INDEX posts_created_idx ON posts (created_at DESC);

-- ─────────── REVIEWS ──────────────────────────────────────────────────────
CREATE TABLE reviews (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id     UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body        TEXT NOT NULL,
    sentiment   REAL,
    like_count  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX reviews_post_idx   ON reviews (post_id);
CREATE INDEX reviews_author_idx ON reviews (author_id);

-- ─────────── LIKES ────────────────────────────────────────────────────────
CREATE TABLE likes (
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL CHECK (target_type IN ('post', 'review')),
    target_id   UUID NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, target_type, target_id)
);
CREATE INDEX likes_target_idx ON likes (target_type, target_id);

-- ─────────── FLAGS ────────────────────────────────────────────────────────
CREATE TABLE flags (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flagger_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL,
    target_id   UUID NOT NULL,
    reason      TEXT NOT NULL,
    evidence    TEXT,
    status      TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'verified', 'rejected')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX flags_target_idx ON flags (target_type, target_id);
CREATE INDEX flags_status_idx ON flags (status) WHERE status = 'pending';

-- ─────────── SESSIONS ─────────────────────────────────────────────────────
CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    city_id     UUID REFERENCES cities(id) ON DELETE SET NULL,
    mode        TEXT NOT NULL CHECK (mode IN ('voice', 'text')),
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at    TIMESTAMPTZ,
    summary     TEXT,
    cost_points INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX sessions_user_idx    ON sessions (user_id, started_at DESC);
CREATE INDEX sessions_active_idx  ON sessions (user_id) WHERE ended_at IS NULL;

-- ─────────── MEMORY: profile / instance ───────────────────────────────────
CREATE TABLE memory_profile (
    user_id    UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    data       JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE memory_instance (
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    poi_id     UUID NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    sentiment  REAL NOT NULL CHECK (sentiment BETWEEN -1 AND 1),
    note       TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, poi_id)
);
CREATE INDEX memory_instance_user_idx ON memory_instance (user_id);

-- ─────────── SUBSCRIPTIONS ────────────────────────────────────────────────
CREATE TABLE subscriptions (
    user_id              UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    tier                 TEXT NOT NULL DEFAULT 'free'
        CHECK (tier IN ('free', 'wanderer', 'explorer')),
    state                TEXT NOT NULL DEFAULT 'active'
        CHECK (state IN ('active', 'grace', 'paused', 'cancelled')),
    current_period_start TIMESTAMPTZ,
    current_period_end   TIMESTAMPTZ,
    play_purchase_token  TEXT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────── POINTS LEDGER ────────────────────────────────────────────────
CREATE TABLE points_ledger (
    id         BIGSERIAL PRIMARY KEY,
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delta      INTEGER NOT NULL,
    reason     TEXT NOT NULL,
    ref_type   TEXT,
    ref_id     UUID,
    bucket     TEXT NOT NULL CHECK (bucket IN ('subscription', 'earned', 'topup')),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX points_ledger_user_idx       ON points_ledger (user_id, created_at DESC);
CREATE INDEX points_ledger_user_bucket_idx ON points_ledger (user_id, bucket)
    WHERE expires_at IS NULL OR expires_at > NOW();

-- ─────────── updated_at triggers ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pois_touch_updated_at        BEFORE UPDATE ON pois
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER memory_profile_touch         BEFORE UPDATE ON memory_profile
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER memory_instance_touch        BEFORE UPDATE ON memory_instance
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER subscriptions_touch          BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

COMMIT;
