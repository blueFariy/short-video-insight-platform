"""
Report Generation Service
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
from pathlib import Path

from app.core.config import settings


@dataclass
class Report:
    """Report model"""
    id: str
    name: str
    type: str
    description: str
    data: Dict[str, Any]
    created_at: datetime
    created_by: str = "system"
    file_path: Optional[str] = None


@dataclass
class ReportTemplate:
    """Report template"""
    id: str
    name: str
    type: str
    description: str
    fields: List[str]


class ReportService:
    """Report service"""

    def __init__(self):
        self.reports: Dict[str, Report] = {}
        self.report_dir = Path(settings.REPORT_DIR)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self._init_templates()

    def _init_templates(self):
        """Initialize report templates"""
        self.templates = {
            "video_analysis": ReportTemplate(
                id="video_analysis",
                name="视频分析报表",
                type="analysis",
                description="视频内容分析报表",
                fields=["video_id", "title", "platform", "likes", "comments", "views", "score"]
            ),
            "competitor_overview": ReportTemplate(
                id="competitor_overview",
                name="竞品概览报表",
                type="competitor",
                description="竞品账号数据概览",
                fields=["account_id", "account_name", "platform", "followers", "likes", "views"]
            ),
            "trend_report": ReportTemplate(
                id="trend_report",
                name="趋势分析报表",
                type="trend",
                description="数据趋势分析",
                fields=["date", "platform", "total_views", "total_likes", "avg_engagement"]
            ),
            "insight_summary": ReportTemplate(
                id="insight_summary",
                name="洞察摘要报表",
                type="insight",
                description="AI洞察摘要",
                fields=["video_id", "hook_score", "structure_score", "sentiment", "recommendations"]
            )
        }

    async def create_report(
        self,
        name: str,
        report_type: str,
        data: Dict[str, Any],
        description: str = "",
        created_by: str = "system"
    ) -> Report:
        """Create a new report"""
        import uuid
        report = Report(
            id=f"report_{uuid.uuid4().hex[:12]}",
            name=name,
            type=report_type,
            description=description,
            data=data,
            created_at=datetime.now(),
            created_by=created_by
        )
        self.reports[report.id] = report
        logger.info(f"Created report: {report.name} ({report.id})")
        return report

    async def get_report(self, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        return self.reports.get(report_id)

    async def list_reports(
        self,
        report_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Report]:
        """List reports"""
        reports = list(self.reports.values())
        if report_type:
            reports = [r for r in reports if r.type == report_type]
        reports.sort(key=lambda x: x.created_at, reverse=True)
        return reports[:limit]

    async def delete_report(self, report_id: str) -> bool:
        """Delete a report"""
        if report_id in self.reports:
            del self.reports[report_id]
            return True
        return False

    async def generate_video_report(
        self,
        videos: List[Dict[str, Any]]
    ) -> Report:
        """Generate video analysis report"""
        # Calculate statistics
        total_videos = len(videos)
        total_likes = sum(v.get("likes", 0) for v in videos)
        total_comments = sum(v.get("comments", 0) for v in videos)
        total_views = sum(v.get("views", 0) for v in videos)

        avg_likes = total_likes / total_videos if total_videos > 0 else 0
        avg_comments = total_comments / total_videos if total_videos > 0 else 0
        avg_views = total_views / total_videos if total_videos > 0 else 0

        # Top videos
        top_liked = sorted(videos, key=lambda x: x.get("likes", 0), reverse=True)[:10]
        top_viewed = sorted(videos, key=lambda x: x.get("views", 0), reverse=True)[:10]

        data = {
            "summary": {
                "total_videos": total_videos,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_views": total_views,
                "avg_likes": avg_likes,
                "avg_comments": avg_comments,
                "avg_views": avg_views
            },
            "top_liked": top_liked,
            "top_viewed": top_viewed,
            "videos": videos
        }

        return await self.create_report(
            name=f"视频分析报表_{datetime.now().strftime('%Y%m%d')}",
            report_type="video_analysis",
            data=data,
            description=f"包含 {total_videos} 个视频的分析报表"
        )

    async def generate_competitor_report(
        self,
        accounts: List[Dict[str, Any]]
    ) -> Report:
        """Generate competitor overview report"""
        # Group by platform
        platforms = {}
        for acc in accounts:
            platform = acc.get("platform", "unknown")
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(acc)

        # Calculate totals
        total_followers = sum(a.get("followers", 0) for a in accounts)
        total_likes = sum(a.get("likes", 0) for a in accounts)
        total_views = sum(a.get("views", 0) for a in accounts)

        # Top accounts
        top_followers = sorted(accounts, key=lambda x: x.get("followers", 0), reverse=True)[:10]

        data = {
            "summary": {
                "total_accounts": len(accounts),
                "total_followers": total_followers,
                "total_likes": total_likes,
                "total_views": total_views,
                "platforms": list(platforms.keys())
            },
            "by_platform": platforms,
            "top_followers": top_followers,
            "accounts": accounts
        }

        return await self.create_report(
            name=f"竞品概览报表_{datetime.now().strftime('%Y%m%d')}",
            report_type="competitor_overview",
            data=data,
            description=f"包含 {len(accounts)} 个竞品账号的报表"
        )

    async def generate_trend_report(
        self,
        days: int = 30
    ) -> Report:
        """Generate trend report"""
        # Generate demo trend data
        trend_data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i - 1)
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "total_views": 1000000 + i * 50000,
                "total_likes": 50000 + i * 2500,
                "avg_engagement": 0.05 + (i * 0.001)
            })

        # Calculate trends
        if len(trend_data) >= 7:
            recent_week = trend_data[-7:]
            prev_week = trend_data[-14:-7] if len(trend_data) >= 14 else trend_data[:7]

            views_trend = sum(d["total_views"] for d in recent_week) / sum(d["total_views"] for d in prev_week) - 1
            likes_trend = sum(d["total_likes"] for d in recent_week) / sum(d["total_likes"] for d in prev_week) - 1
        else:
            views_trend = 0
            likes_trend = 0

        data = {
            "days": days,
            "trend_data": trend_data,
            "trends": {
                "views_change": views_trend * 100,
                "likes_change": likes_trend * 100
            }
        }

        return await self.create_report(
            name=f"趋势分析报表_{datetime.now().strftime('%Y%m%d')}",
            report_type="trend_report",
            data=data,
            description=f"最近 {days} 天数据趋势"
        )

    def get_templates(self) -> List[ReportTemplate]:
        """Get all report templates"""
        return list(self.templates.values())

    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)


report_service = ReportService()
