-- Database Initialization Script
-- Video Insight Platform

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    avatar_url TEXT,
    company VARCHAR(100),
    job_title VARCHAR(50),
    preferences JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_expires TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Creators table
CREATE TABLE IF NOT EXISTS creators (
    id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    creator_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    follower_count BIGINT DEFAULT 0,
    following_count BIGINT DEFAULT 0,
    total_likes BIGINT DEFAULT 0,
    avg_play_count BIGINT DEFAULT 0,
    avg_interaction_rate FLOAT,
    main_category VARCHAR(50),
    stats_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(platform, creator_id)
);

CREATE INDEX IF NOT EXISTS idx_creators_follower ON creators(follower_count DESC);

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
    id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    video_id VARCHAR(100) NOT NULL,
    video_url TEXT NOT NULL,
    title VARCHAR(500),
    description TEXT,
    cover_image_url TEXT,
    duration INT,
    publish_time TIMESTAMPTZ,
    play_count BIGINT DEFAULT 0,
    like_count BIGINT DEFAULT 0,
    comment_count BIGINT DEFAULT 0,
    share_count BIGINT DEFAULT 0,
    collect_count BIGINT DEFAULT 0,
    forward_count BIGINT DEFAULT 0,
    creator_id BIGINT REFERENCES creators(id),
    category VARCHAR(50),
    tags TEXT[],
    ai_generated_tags TEXT[],
    data_quality_score FLOAT DEFAULT 1.0,
    is_denoised BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(platform, video_id)
);

CREATE INDEX IF NOT EXISTS idx_videos_platform_publish ON videos(platform, publish_time);
CREATE INDEX IF NOT EXISTS idx_videos_play_count ON videos(play_count DESC);
CREATE INDEX IF NOT EXISTS idx_videos_category ON videos(category);
CREATE INDEX IF NOT EXISTS idx_videos_creator ON videos(creator_id);

-- Video Scripts table
CREATE TABLE IF NOT EXISTS video_scripts (
    id BIGSERIAL PRIMARY KEY,
    video_id BIGINT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    asr_text TEXT,
    asr_confidence FLOAT,
    ocr_text TEXT,
    ocr_frames JSONB,
    keyframes JSONB,
    bgm_info JSONB,
    audio_emotion VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_video_scripts_video ON video_scripts(video_id);

-- Video Insights table
CREATE TABLE IF NOT EXISTS video_insights (
    id BIGSERIAL PRIMARY KEY,
    video_id BIGINT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    ai_summary TEXT,
    hook_3s TEXT,
    hook_type VARCHAR(30),
    structure_type VARCHAR(30),
    structure_analysis JSONB,
    keywords TEXT[],
    entity_tags JSONB,
    sentiment_score FLOAT,
    comment_high_freq TEXT[],
    user_feedback JSONB,
    viral_factors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_video_insights_video ON video_insights(video_id);
CREATE INDEX IF NOT EXISTS idx_video_insights_hook_type ON video_insights(hook_type);
CREATE INDEX IF NOT EXISTS idx_video_insights_structure ON video_insights(structure_type);

-- Collections table
CREATE TABLE IF NOT EXISTS collections (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_type VARCHAR(20) NOT NULL,
    item_id BIGINT NOT NULL,
    notes TEXT,
    tags TEXT[],
    folder VARCHAR(100),
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collections_user ON collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collections_item ON collections(item_type, item_id);

-- Competitor Watch table
CREATE TABLE IF NOT EXISTS competitor_watch (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    creator_id BIGINT NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
    watch_name VARCHAR(100),
    alert_threshold INT DEFAULT 20,
    last_alert_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, creator_id)
);

CREATE INDEX IF NOT EXISTS idx_competitor_watch_user ON competitor_watch(user_id);

-- Trend Reports table
CREATE TABLE IF NOT EXISTS trend_reports (
    id BIGSERIAL PRIMARY KEY,
    report_type VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    ai_insights TEXT,
    hot_topics JSONB,
    rising_creators JSONB,
    content_trends JSONB,
    user_interest_shift JSONB,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    related_videos BIGINT[],
    related_creators BIGINT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trend_reports_period ON trend_reports(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_trend_reports_type ON trend_reports(report_type);
