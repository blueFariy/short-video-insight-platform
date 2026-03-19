"""
Statistics Service
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class StatisticsService:
    """Statistics service for data analysis"""

    def __init__(self):
        self.demo_data = self._init_demo_data()

    def _init_demo_data(self):
        """Initialize demo statistics data"""
        return {
            "total_videos": 1250,
            "total_accounts": 45,
            "total_views": 50000000,
            "total_likes": 2500000,
            "total_comments": 180000,
            "platforms": {
                "douyin": {"videos": 500, "views": 20000000},
                "bilibili": {"videos": 350, "views": 15000000},
                "xiaohongshu": {"videos": 250, "views": 10000000},
                "kuaishou": {"videos": 150, "views": 5000000}
            },
            "categories": {
                "搞笑": 350,
                "知识": 280,
                "生活": 220,
                "科技": 180,
                "美食": 120,
                "其他": 100
            }
        }

    async def get_overview(self) -> Dict[str, Any]:
        """Get overall statistics"""
        return {
            "total_videos": self.demo_data["total_videos"],
            "total_accounts": self.demo_data["total_accounts"],
            "total_views": self.demo_data["total_views"],
            "total_likes": self.demo_data["total_likes"],
            "total_comments": self.demo_data["total_comments"],
            "avg_engagement": self.demo_data["total_likes"] / self.demo_data["total_views"],
            "updated_at": datetime.now().isoformat()
        }

    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get platform statistics"""
        platforms = []
        for name, data in self.demo_data["platforms"].items():
            platforms.append({
                "name": name,
                "videos": data["videos"],
                "views": data["views"],
                "percentage": data["views"] / self.demo_data["total_views"] * 100
            })

        platforms.sort(key=lambda x: x["views"], reverse=True)
        return {"platforms": platforms}

    async def get_category_stats(self) -> Dict[str, Any]:
        """Get category statistics"""
        categories = []
        for name, count in self.demo_data["categories"].items():
            categories.append({
                "name": name,
                "videos": count,
                "percentage": count / self.demo_data["total_videos"] * 100
            })

        categories.sort(key=lambda x: x["videos"], reverse=True)
        return {"categories": categories}

    async def get_time_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get time-based statistics"""
        # Generate demo daily data
        daily_data = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i - 1)
            daily_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "videos": 30 + (i % 10),
                "views": 1500000 + (i * 10000),
                "likes": 75000 + (i * 500),
                "comments": 5000 + (i * 50)
            })

        # Calculate trends
        recent = daily_data[-7:]
        prev = daily_data[-14:-7] if len(daily_data) >= 14 else daily_data[:7]

        views_trend = (sum(d["views"] for d in recent) / sum(d["views"] for d in prev) - 1) * 100 if sum(d["views"] for d in prev) > 0 else 0
        likes_trend = (sum(d["likes"] for d in recent) / sum(d["likes"] for d in prev) - 1) * 100 if sum(d["likes"] for d in prev) > 0 else 0

        return {
            "days": days,
            "daily_data": daily_data,
            "trends": {
                "views_change": views_trend,
                "likes_change": likes_trend
            }
        }

    async def get_top_content(
        self,
        metric: str = "views",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get top content by metric"""
        # Demo top videos
        videos = []
        for i in range(limit):
            videos.append({
                "rank": i + 1,
                "video_id": f"video_{i+1}",
                "title": f"热门视频标题 {i+1}",
                "platform": ["douyin", "bilibili", "xiaohongshu", "kuaishou"][i % 4],
                "views": 1000000 - i * 50000,
                "likes": 50000 - i * 2500,
                "comments": 3000 - i * 150
            })

        return {"top_videos": videos, "metric": metric}

    async def get_engagement_stats(self) -> Dict[str, Any]:
        """Get engagement statistics"""
        return {
            "avg_likes_per_video": self.demo_data["total_likes"] / self.demo_data["total_videos"],
            "avg_comments_per_video": self.demo_data["total_comments"] / self.demo_data["total_videos"],
            "engagement_rate": self.demo_data["total_likes"] / self.demo_data["total_views"],
            "by_platform": {
                "douyin": 0.045,
                "bilibili": 0.065,
                "xiaohongshu": 0.055,
                "kuaishou": 0.035
            }
        }


statistics_service = StatisticsService()
