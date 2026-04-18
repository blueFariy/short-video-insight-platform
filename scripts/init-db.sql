-- Database Initialization Script
-- Video Insight Platform

-- Users table
DROP TABLE IF EXISTS users;
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

DROP TABLE IF EXISTS creators;
-- Creators table - 主键为 (platform, creator_id)
CREATE TABLE IF NOT EXISTS creators (
    platform VARCHAR(20) NOT NULL,
    creator_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    url TEXT,
    avatar_url TEXT,
    bio TEXT,
    follower_count BIGINT DEFAULT 0,
    following_count BIGINT DEFAULT 0,
    total_likes BIGINT DEFAULT 0,
    video_count BIGINT DEFAULT 0,
    avg_play_count BIGINT DEFAULT 0,
    avg_interaction_rate FLOAT,
    main_category VARCHAR(50),
    last_video_date TIMESTAMPTZ DEFAULT null,
    first_video_date TIMESTAMPTZ DEFAULT null,
    stats_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_monitored BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (platform, creator_id)
);

CREATE INDEX IF NOT EXISTS idx_creators_follower ON creators(follower_count DESC);
CREATE INDEX IF NOT EXISTS idx_creators_monitored ON creators(is_monitored);

DROP TABLE IF EXISTS videos;
-- Videos table - creator_id 改为 VARCHAR(100) 存储平台的 creator_id
CREATE TABLE IF NOT EXISTS videos (
    id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    video_id VARCHAR(100) UNIQUE NOT NULL,
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
    danmaku_count BIGINT DEFAULT 0,
    coin_count BIGINT DEFAULT 0,
    collect_count BIGINT DEFAULT 0,
    creator_id VARCHAR(100),
    creator_name VARCHAR(500),
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

DROP TABLE IF EXISTS video_scripts;
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

DROP TABLE IF EXISTS video_insights;
-- Video Insights table
CREATE TABLE IF NOT EXISTS video_insights (
    id BIGSERIAL PRIMARY KEY,
    video_id VARCHAR(100) NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
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
    improvements TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_video_insights_video ON video_insights(video_id);
CREATE INDEX IF NOT EXISTS idx_video_insights_hook_type ON video_insights(hook_type);
CREATE INDEX IF NOT EXISTS idx_video_insights_structure ON video_insights(structure_type);

DROP TABLE IF EXISTS collections;
-- Collections table
CREATE TABLE IF NOT EXISTS collections (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_type VARCHAR(20) NOT NULL,
    item_id VARCHAR(100) NOT NULL,
    notes TEXT,
    tags TEXT[],
    folder VARCHAR(100),
    is_analysis BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collections_user ON collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collections_item ON collections(item_type, item_id);

DROP TABLE IF EXISTS competitor_watch;
-- Competitor Watch table
CREATE TABLE IF NOT EXISTS competitor_watch (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    creator_id VARCHAR(100) NOT NULL,
    watch_name VARCHAR(100),
    alert_threshold INT DEFAULT 20,
    last_alert_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, platform, creator_id)
);

CREATE INDEX IF NOT EXISTS idx_competitor_watch_user ON competitor_watch(user_id);

DROP TABLE IF EXISTS trend_reports;
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

-- ===========================================
-- 爆款雷达相关表 (新增)
-- ===========================================

DROP TABLE IF EXISTS video_metric_snapshots;
-- Video Metric Snapshots - 视频指标时序快照
CREATE TABLE IF NOT EXISTS video_metric_snapshots (
    id BIGSERIAL PRIMARY KEY,
    video_id VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    play_count BIGINT DEFAULT 0,
    like_count BIGINT DEFAULT 0,
    comment_count BIGINT DEFAULT 0,
    share_count BIGINT DEFAULT 0,
    danmaku_count BIGINT DEFAULT 0,
    coin_count BIGINT DEFAULT 0,
    collect_count BIGINT DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    like_ratio FLOAT DEFAULT 0.0,
    comment_ratio FLOAT DEFAULT 0.0,
    share_ratio FLOAT DEFAULT 0.0,
    snapshot_time TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_video ON video_metric_snapshots(video_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_time ON video_metric_snapshots(snapshot_time);
CREATE INDEX IF NOT EXISTS idx_snapshot_video_time ON video_metric_snapshots(video_id, snapshot_time);

DROP TABLE IF EXISTS user_interests;
-- User Interests - 用户兴趣配置
CREATE TABLE IF NOT EXISTS user_interests (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    category_weights JSONB DEFAULT '{}',
    interest_keywords TEXT[],
    platforms TEXT[] DEFAULT ARRAY['douyin', 'bilibili', 'xiaohongshu'],
    alert_levels TEXT[] DEFAULT ARRAY['yellow', 'orange', 'red'],
    notification_channels TEXT[] DEFAULT ARRAY['app'],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_interests_user ON user_interests(user_id);

DROP TABLE IF EXISTS viral_alerts;
-- Viral Alerts - 爆款预警记录
CREATE TABLE IF NOT EXISTS viral_alerts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    video_id VARCHAR(100) NOT NULL,
    platform VARCHAR(20),
    category VARCHAR(20),
    title VARCHAR(500),
    cover_url TEXT,
    video_url TEXT,
    alert_level VARCHAR(20) NOT NULL,
    message TEXT,
    factors JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_viral_alerts_user ON viral_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_viral_alerts_video ON viral_alerts(video_id);
CREATE INDEX IF NOT EXISTS idx_alert_user_read ON viral_alerts(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_alert_user_time ON viral_alerts(user_id, created_at);

DROP TABLE IF EXISTS category_benchmarks;
-- Category Benchmarks - 分类基准数据
CREATE TABLE IF NOT EXISTS category_benchmarks (
    id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    platform_factor FLOAT DEFAULT 1.0,
    category_factor FLOAT DEFAULT 1.0,
    creator_follower_factor FLOAT DEFAULT 0.0,
    creator_avg_play_count_factor FLOAT DEFAULT 0.0,
    creator_update_interval_hours INT,
    video_like_ratio FLOAT DEFAULT 0.0,
    video_collect_ratio FLOAT DEFAULT 0.0,
    video_comment_ratio FLOAT DEFAULT 0.0,
    video_publish_hours INT,
    video_duration_seconds_min INT,
    video_duration_seconds_max INT,
    decay_period FLOAT DEFAULT 60,
    viral_threshold FLOAT[] DEFAULT ARRAY[3.00,8.00,20.00],
    alert_level TEXT[] DEFAULT ARRAY['yellow','orange','red'],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(platform, category)
);

CREATE INDEX IF NOT EXISTS idx_benchmark_platform_cat ON category_benchmarks(platform, category);

-- ===========================================
-- 定时任务管理表 (新增)
-- ===========================================

DROP TABLE IF EXISTS scheduled_tasks;
-- Scheduled Tasks - 定时任务配置
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    celery_task_name VARCHAR(200) NOT NULL,
    task_params TEXT,
    interval_seconds INTEGER NOT NULL DEFAULT 3600,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_run TIMESTAMPTZ,
    next_run TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_enabled ON scheduled_tasks(enabled);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run);
