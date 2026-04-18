# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Short Video Insight Platform is a microservices-based AI platform for short video creators to discover viral trends and generate creative insights. The platform analyzes短视频 content from platforms like Douyin, Bilibili, and Xiaohongshu.

## Architecture

```
short-video-insight-platform/
├── services/                    # Microservices (Python FastAPI)
│   ├── user-service/           # Authentication & user management
│   ├── data-collector/          # Video data collection & viral detection
│   ├── video-service/           # Video processing, ASR, OCR
│   ├── content-analysis/       # Multi-modal content analysis
│   ├── insight-generator/       # AI-powered insight generation
│   ├── competitor-monitor/      # Competitor tracking
│   └── report-service/          # Report generation
├── frontend/                    # Vue 3 + Element Plus + ECharts
├── deploy/docker/              # Docker Compose configuration
└── common/                     # Shared libraries
```

## Common Commands

### Backend Services
```bash
# Build and run a specific service
docker-compose -f deploy/docker/docker-compose.yml build data-collector
docker-compose -f deploy/docker/docker-compose.yml up -d data-collector

# View logs
docker logs short-video-data-collector
docker logs short-video-frontend

# Restart service
docker restart short-video-data-collector
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Development
npm run build    # Production build
```

### Database
```bash
# Connect to PostgreSQL
docker exec -it short-video-postgres psql -U postgres -d short_video_insight

# Run SQL queries
docker exec short-video-postgres psql -U postgres -d short_video_insight -c "SELECT * FROM videos LIMIT 5;"
```

### Infrastructure
```bash
# All services use docker-compose at deploy/docker/docker-compose.yml
cd deploy/docker
docker-compose up -d     # Start all
docker-compose ps       # Status
docker-compose logs -f  # Follow logs
```

## Key Technical Details

### API Communication
- Frontend calls backend via REST APIs defined in `frontend/src/api/index.ts`
- Services communicate via internal network (e.g., data-collector:8004, user-service:8001)
- JWT authentication required for most endpoints

### Database
- PostgreSQL with async SQLAlchemy
- Models defined in `services/*/app/models/`
- Primary tables: users, videos, viral_alerts, user_interests, video_insights

### Key API Endpoints (data-collector service)
- `GET /api/v1/collector/alerts` - Get viral alerts with filters (alert_level, is_read, platform, keyword)
- `POST /api/v1/collector/alerts/{id}/read` - Mark alert as read
- `GET /api/v1/collector/viral-videos` - Get viral videos

### Frontend Structure
- Vue 3 Composition API with `<script setup>`
- Element Plus for UI components
- Views in `frontend/src/views/`
- API calls in `frontend/src/api/`

## Important Patterns

### Adding New Filters to Alerts API
1. Add query parameter in `services/data-collector/app/api/v1/endpoints/viral_alert.py`
2. Add filter logic in `services/data-collector/app/services/user_interest_service.py` (AlertRecordService.get_user_alerts)
3. Add frontend filter in `frontend/src/views/dashboard/Dashboard.vue` and pass to API

### Vue Component Styling with Element Plus
- Use `:deep()` selector to style child components from scoped styles
- Example: `:deep(.el-dialog__body) { ... }`

## Development Notes from AGENTS.md

- Git flow: main, develop, feature/*, release/*, hotfix/*
- Python: Black formatter (88 char line width), type annotations required
- Vue: Composition API, PascalCase component names
- All API endpoints require JWT authentication (except login/register)
- Environment variables for secrets, no hardcoded credentials