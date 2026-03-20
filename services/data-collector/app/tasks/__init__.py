"""
Celery Tasks
"""
from app.tasks.hot_scan import scan_all_platforms, analyze_video_for_viral
from app.tasks.competitor_monitor import check_all_watchlists, send_competitor_alert
from app.tasks.video_update import refresh_active_videos, send_viral_alert
from app.tasks.report_generator import generate_daily
from app.tasks.maintenance import cleanup_old_data, health_check

__all__ = [
    'scan_all_platforms',
    'analyze_video_for_viral',
    'check_all_watchlists',
    'send_competitor_alert',
    'refresh_active_videos',
    'send_viral_alert',
    'generate_daily',
    'cleanup_old_data',
    'health_check'
]
