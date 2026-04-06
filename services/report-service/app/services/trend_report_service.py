"""
Trend Report Service - 趋势报告服务
提供多维度趋势数据聚合和分析功能
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date

# 添加 data-collector 路径以便导入模型
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "data-collector"))

from sqlalchemy import select, func, and_, text
from sqlalchemy.sql import func as sql_func
from loguru import logger

from app.core.database import db_manager

# 从 data-collector 导入模型
try:
    from app.models.video import Video
    from app.models.viral_alert import ViralAlert
except ImportError:
    # 如果导入失败，使用占位符
    Video = None
    ViralAlert = None


class TrendReportService:
    """趋势报告服务 - 聚合视频数据生成趋势报告"""

    async def get_statistics(
        self,
        days: int = 7,
        platform: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取趋势统计数据

        Args:
            days: 统计天数
            platform: 平台筛选 (douyin/bilibili/xiaohongshu/kuaishou)
            category: 分类筛选

        Returns:
            趋势统计数据
        """
        try:
            async with db_manager.get_session() as session:
                # 计算日期过滤条件
                date_filter = datetime.now() - timedelta(days=days)

                # 构建基础筛选条件
                conditions = [Video.publish_time >= date_filter]

                if platform:
                    conditions.append(Video.platform == platform)
                if category:
                    conditions.append(Video.category == category)

                # 查询视频统计数据
                video_stats_query = select(
                    func.count(Video.id).label("total_videos"),
                    func.sum(Video.play_count).label("total_views"),
                    func.sum(Video.like_count).label("total_likes"),
                    func.sum(Video.comment_count).label("total_comments"),
                    func.sum(Video.share_count).label("total_shares")
                ).where(and_(*conditions))

                result = await session.execute(video_stats_query)
                video_stats = result.one()

                # 查询平台分布
                platform_query = select(
                    Video.platform,
                    func.count(Video.id).label("video_count"),
                    func.sum(Video.play_count).label("total_views")
                ).where(
                    Video.publish_time >= date_filter
                ).group_by(Video.platform)

                platform_result = await session.execute(platform_query)
                platform_stats = [
                    {
                        "platform": row.platform,
                        "video_count": row.video_count,
                        "total_views": row.total_views or 0
                    }
                    for row in platform_result.fetchall()
                ]

                # 查询分类分布
                category_query = select(
                    Video.category,
                    func.count(Video.id).label("video_count")
                ).where(
                    and_(
                        Video.publish_time >= date_filter,
                        Video.category.isnot(None)
                    )
                ).group_by(Video.category).order_by(
                    func.count(Video.id).desc()
                ).limit(10)

                category_result = await session.execute(category_query)
                category_stats = [
                    {"category": row.category, "video_count": row.video_count}
                    for row in category_result.fetchall()
                ]

                # 查询每日趋势数据 - 使用原生 SQL
                daily_query = text(f"""
                    SELECT
                        DATE(publish_time) as date,
                        COUNT(*) as video_count,
                        COALESCE(SUM(play_count), 0) as total_views,
                        COALESCE(SUM(like_count), 0) as total_likes
                    FROM videos
                    WHERE publish_time >= NOW() - INTERVAL '{days} days'
                    GROUP BY DATE(publish_time)
                    ORDER BY date
                """)

                daily_result = await session.execute(daily_query)
                daily_data = [
                    {
                        "date": str(row.date),
                        "video_count": row.video_count,
                        "total_views": row.total_views or 0,
                        "total_likes": row.total_likes or 0
                    }
                    for row in daily_result.fetchall()
                ]

                # 计算趋势变化 (与前一周期对比)
                prev_period_views = 0
                if days >= 7:
                    prev_start = datetime.now() - timedelta(days=days * 2)
                    prev_end = datetime.now() - timedelta(days=days)
                    prev_query = select(
                        func.sum(Video.play_count)
                    ).where(
                        and_(
                            Video.publish_time >= prev_start,
                            Video.publish_time < prev_end
                        )
                    )
                    prev_result = await session.execute(prev_query)
                    prev_period_views = prev_result.scalar() or 0

                current_views = video_stats.total_views or 0
                views_growth = (
                    ((current_views - prev_period_views) / prev_period_views * 100)
                    if prev_period_views > 0 else 0
                )

                return {
                    "period_days": days,
                    "platform_filter": platform,
                    "category_filter": category,
                    "total_videos": video_stats.total_videos or 0,
                    "total_views": current_views,
                    "total_likes": video_stats.total_likes or 0,
                    "total_comments": video_stats.total_comments or 0,
                    "total_shares": video_stats.total_shares or 0,
                    "views_growth": round(views_growth, 2),
                    "platforms": platform_stats,
                    "categories": category_stats,
                    "daily_data": daily_data,
                    "generated_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            # 返回演示数据作为降级方案
            return self._get_demo_statistics(days, platform, category)

    async def get_viral_trends(
        self,
        days: int = 7,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取爆款趋势数据

        Args:
            days: 统计天数
            platform: 平台筛选

        Returns:
            爆款趋势数据
        """
        try:
            async with db_manager.get_session() as session:
                date_filter = datetime.now() - timedelta(days=days)
                conditions = [ViralAlert.created_at >= date_filter]

                if platform:
                    conditions.append(ViralAlert.platform == platform)

                # 查询爆款预警统计
                alert_stats_query = select(
                    func.count(ViralAlert.id).label("total_alerts"),
                    ViralAlert.alert_level,
                    ViralAlert.platform
                ).where(and_(*conditions)).group_by(
                    ViralAlert.alert_level,
                    ViralAlert.platform
                )

                result = await session.execute(alert_stats_query)

                alerts_by_level = {}
                alerts_by_platform = {}
                for row in result.fetchall():
                    level = row.alert_level
                    plat = row.platform
                    count = row.total_alerts

                    alerts_by_level[level] = alerts_by_level.get(level, 0) + count
                    alerts_by_platform[plat] = alerts_by_platform.get(plat, 0) + count

                # 查询近期爆款视频
                viral_videos_query = select(
                    ViralAlert.video_id,
                    ViralAlert.title,
                    ViralAlert.platform,
                    ViralAlert.alert_level,
                    ViralAlert.factors,
                    ViralAlert.created_at
                ).where(
                    and_(*conditions)
                ).order_by(
                    ViralAlert.created_at.desc()
                ).limit(20)

                viral_result = await session.execute(viral_videos_query)
                recent_viral_videos = [
                    {
                        "video_id": row.video_id,
                        "title": row.title,
                        "platform": row.platform,
                        "alert_level": row.alert_level,
                        "factors": row.factors,
                        "detected_at": row.created_at.isoformat() if row.created_at else None
                    }
                    for row in viral_result.fetchall()
                ]

                return {
                    "period_days": days,
                    "total_alerts": sum(alerts_by_level.values()),
                    "alerts_by_level": alerts_by_level,
                    "alerts_by_platform": alerts_by_platform,
                    "recent_viral_videos": recent_viral_videos
                }

        except Exception as e:
            logger.error(f"Error getting viral trends: {e}")
            return self._get_demo_viral_trends(days, platform)

    async def generate_trend_report(
        self,
        report_type: str = "weekly",
        platform: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成趋势报告

        Args:
            report_type: 报告类型 (daily/weekly/monthly)
            platform: 平台筛选
            category: 分类筛选

        Returns:
            生成的报告数据
        """
        # 计算时间范围
        now = datetime.now()
        if report_type == "daily":
            period_start = now.date()
            period_end = now.date()
            days = 1
        elif report_type == "weekly":
            period_start = (now - timedelta(days=7)).date()
            period_end = now.date()
            days = 7
        else:  # monthly
            period_start = (now - timedelta(days=30)).date()
            period_end = now.date()
            days = 30

        # 获取统计数据
        statistics = await self.get_statistics(days, platform, category)
        viral_trends = await self.get_viral_trends(days, platform)

        # 生成报告标题
        title = self._generate_report_title(report_type, period_start, period_end, platform)

        # 构建报告数据
        report = {
            "report_type": report_type,
            "title": title,
            "period_start": str(period_start),
            "period_end": str(period_end),
            "summary": {
                "total_videos": statistics["total_videos"],
                "total_views": statistics["total_views"],
                "views_growth": statistics["views_growth"],
                "total_viral_alerts": viral_trends["total_alerts"]
            },
            "platform_stats": statistics["platforms"],
            "category_stats": statistics["categories"],
            "daily_trends": statistics["daily_data"],
            "viral_trends": {
                "by_level": viral_trends["alerts_by_level"],
                "by_platform": viral_trends["alerts_by_platform"],
                "recent_videos": viral_trends["recent_viral_videos"]
            },
            "hot_topics": self._extract_hot_topics(viral_trends["recent_viral_videos"]),
            "insights": self._generate_insights(statistics, viral_trends),
            "created_at": now.isoformat()
        }

        # 保存报告到数据库
        await self._save_report(report)

        return report

    async def get_report_list(
        self,
        report_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取趋势报告列表

        Args:
            report_type: 报告类型筛选
            limit: 返回数量

        Returns:
            报告列表
        """
        try:
            async with db_manager.get_session() as session:
                from app.services.models import TrendReport as DBTrendReport

                query = select(
                    DBTrendReport.id,
                    DBTrendReport.report_type,
                    DBTrendReport.title,
                    DBTrendReport.summary,
                    DBTrendReport.period_start,
                    DBTrendReport.period_end,
                    DBTrendReport.created_at
                ).order_by(
                    DBTrendReport.created_at.desc()
                )

                if report_type:
                    query = query.where(DBTrendReport.report_type == report_type)

                query = query.limit(limit)

                result = await session.execute(query)

                reports = []
                for row in result.fetchall():
                    reports.append({
                        "id": row.id,
                        "report_type": row.report_type,
                        "title": row.title,
                        "summary": row.summary,
                        "period_start": str(row.period_start) if row.period_start else None,
                        "period_end": str(row.period_end) if row.period_end else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    })

                return reports

        except Exception as e:
            logger.error(f"Error getting report list: {e}")
            return []

    async def get_report_by_id(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取报告详情

        Args:
            report_id: 报告ID

        Returns:
            报告详情
        """
        try:
            async with db_manager.get_session() as session:
                from app.services.models import TrendReport as DBTrendReport

                query = select(
                    DBTrendReport.id,
                    DBTrendReport.report_type,
                    DBTrendReport.title,
                    DBTrendReport.summary,
                    DBTrendReport.hot_topics,
                    DBTrendReport.ai_insights,
                    DBTrendReport.content_trends,
                    DBTrendReport.period_start,
                    DBTrendReport.period_end,
                    DBTrendReport.created_at
                ).where(DBTrendReport.id == report_id)

                result = await session.execute(query)
                row = result.fetchone()

                if not row:
                    return None

                return {
                    "id": row.id,
                    "report_type": row.report_type,
                    "title": row.title,
                    "summary": row.summary,
                    "hot_topics": row.hot_topics,
                    "ai_insights": row.ai_insights,
                    "content_trends": row.content_trends,
                    "period_start": str(row.period_start) if row.period_start else None,
                    "period_end": str(row.period_end) if row.period_end else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }

        except Exception as e:
            logger.error(f"Error getting report by id: {e}")
            return None

    async def _save_report(self, report: Dict[str, Any]) -> int:
        """保存报告到数据库"""
        try:
            async with db_manager.get_session() as session:
                from sqlalchemy import insert
                from app.services.models import TrendReport as DBTrendReport

                insert_stmt = insert(DBTrendReport).values(
                    report_type=report["report_type"],
                    title=report["title"],
                    summary=report["summary"],
                    hot_topics=report["hot_topics"],
                    ai_insights=report.get("insights"),
                    period_start=report["period_start"],
                    period_end=report["period_end"],
                    created_at=datetime.now()
                )

                result = await session.execute(insert_stmt)
                await session.commit()

                return result.inserted_primary_key[0]

        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return 0

    def _generate_report_title(
        self,
        report_type: str,
        period_start: date,
        period_end: date,
        platform: Optional[str]
    ) -> str:
        """生成报告标题"""
        type_map = {
            "daily": "日报",
            "weekly": "周报",
            "monthly": "月报"
        }
        type_name = type_map.get(report_type, "报告")

        platform_name = ""
        if platform:
            platform_map = {
                "douyin": "抖音",
                "bilibili": "B站",
                "xiaohongshu": "小红书",
                "kuaishou": "快手"
            }
            platform_name = f"{platform_map.get(platform, platform)}-"

        return f"{platform_name}{period_end}{type_name} ({period_start} ~ {period_end})"

    def _extract_hot_topics(self, viral_videos: List[Dict]) -> List[str]:
        """从爆款视频中提取热点话题"""
        categories = {}
        for video in viral_videos:
            factors = video.get("factors", {})
            if isinstance(factors, dict):
                category = factors.get("category", "其他")
                categories[category] = categories.get(category, 0) + 1

        hot_topics = sorted(
            categories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return [f"{topic[0]} ({topic[1]}个爆款)" for topic in hot_topics]

    def _generate_insights(
        self,
        statistics: Dict,
        viral_trends: Dict
    ) -> List[str]:
        """生成洞察建议"""
        insights = []

        growth = statistics.get("views_growth", 0)
        if growth > 20:
            insights.append(f"播放量较上周增长 {growth:.1f}%，市场热度上升")
        elif growth < -10:
            insights.append(f"播放量较上周下降 {abs(growth):.1f}%，建议关注内容质量")

        total_alerts = viral_trends.get("total_alerts", 0)
        if total_alerts > 50:
            insights.append(f"本周产生 {total_alerts} 条爆款预警，市场活跃度高")
        elif total_alerts < 10:
            insights.append("爆款预警较少，可关注内容差异化机会")

        platforms = statistics.get("platforms", [])
        if platforms:
            top_platform = max(platforms, key=lambda x: x.get("total_views", 0))
            insights.append(f"{top_platform['platform']} 平台播放量最高")

        categories = statistics.get("categories", [])
        if categories:
            top_category = categories[0]
            insights.append(f"{top_category['category']} 分类视频数量最多")

        return insights

    def _get_demo_statistics(
        self,
        days: int,
        platform: Optional[str],
        category: Optional[str]
    ) -> Dict[str, Any]:
        """返回演示统计数据"""
        return {
            "period_days": days,
            "platform_filter": platform,
            "category_filter": category,
            "total_videos": 1250,
            "total_views": 50000000,
            "total_likes": 2500000,
            "total_comments": 180000,
            "total_shares": 50000,
            "views_growth": 15.2,
            "platforms": [
                {"platform": "douyin", "video_count": 500, "total_views": 20000000},
                {"platform": "bilibili", "video_count": 350, "total_views": 15000000},
                {"platform": "xiaohongshu", "video_count": 250, "total_views": 10000000},
                {"platform": "kuaishou", "video_count": 150, "total_views": 5000000}
            ],
            "categories": [
                {"category": "美食", "video_count": 320},
                {"category": "美妆", "video_count": 280},
                {"category": "知识", "video_count": 220},
                {"category": "科技", "video_count": 180},
                {"category": "搞笑", "video_count": 150}
            ],
            "daily_data": self._generate_demo_daily_data(days),
            "generated_at": datetime.now().isoformat()
        }

    def _get_demo_viral_trends(
        self,
        days: int,
        platform: Optional[str]
    ) -> Dict[str, Any]:
        """返回演示爆款趋势"""
        return {
            "period_days": days,
            "total_alerts": 48,
            "alerts_by_level": {"yellow": 30, "orange": 15, "red": 3},
            "alerts_by_platform": {"douyin": 20, "bilibili": 15, "xiaohongshu": 10, "kuaishou": 3},
            "recent_viral_videos": [
                {"video_id": "1", "title": "探店北京网红餐厅", "platform": "douyin", "alert_level": "red", "factors": {"category": "美食"}, "detected_at": datetime.now().isoformat()},
                {"video_id": "2", "title": "新手化妆教程", "platform": "xiaohongshu", "alert_level": "orange", "factors": {"category": "美妆"}, "detected_at": datetime.now().isoformat()},
                {"video_id": "3", "title": "AI如何改变生活", "platform": "bilibili", "alert_level": "yellow", "factors": {"category": "科技"}, "detected_at": datetime.now().isoformat()}
            ]
        }

    def _generate_demo_daily_data(self, days: int) -> List[Dict]:
        """生成演示每日数据"""
        data = []
        for i in range(days - 1, -1, -1):
            d = datetime.now() - timedelta(days=i)
            data.append({
                "date": d.strftime("%Y-%m-%d"),
                "video_count": 30 + (i % 10) * 2,
                "total_views": 1500000 + (i * 50000),
                "total_likes": 75000 + (i * 2500)
            })
        return data


# Singleton instance
trend_report_service = TrendReportService()
