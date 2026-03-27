"""
B站(Bilibili)平台数据适配器
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

from app.adapters.api.bilibili_api import BilibiliAPI
from app.schemas import Creator, Video, VideoMetrics
from app.adapters.base import PlatformAdapter


class BilibiliAdapter(PlatformAdapter):
    """
    B站平台适配器
    
    负责将B站API数据转换为统一的Video和Creator格式
    异步版本，支持WBI签名和Cookie认证
    """

    PLATFORM_NAME = "bilibili"

    def __init__(self, cookie: str):
        super().__init__()
        self.platform_name = self.PLATFORM_NAME

        self.api = BilibiliAPI(
            timeout=30,
            cookie_file=cookie
        )

    async def close(self):
        await self.api.close()

    async def get_region_videos(self, rid: int, pn: int = 1, ps: int = 14) -> List[Video]:
        """
        获取视频分区列表
        """
        try:
            results = await self.api.get_region_videos(rid, pn, ps)
            videos = []
            for result in results['archives']:
                videos.append(self._parse_video_data(result))
            return videos
        except Exception as e:
            logger.warning(f"获取视频分区列表失败: {e}")
            return []

    async def get_trending_videos(self, category: Optional[str] = None, limit: int = 100) -> List[Video]:
        """
        获取热门视频列表
        
        参数:
            category: 分区名称 (如 "动画", "游戏" 等)
            limit: 返回数量
        """
        videos = []
        try:
            # 根据category获取分区tid
            rid = 0  # 默认全站
            if category:
                pass

            # 调用排行榜API
            data = await self.api.get_ranking(rid=rid)
            for item in data[:limit]:
                videos.append(self._parse_video_data(item))

        except Exception as e:
            logger.warning(f"获取热门视频失败: {e}")

        return videos

    async def search_videos(self, keyword: str, limit: int = 20) -> List[Video]:
        """搜索视频"""
        videos = []
        try:
            data = await self.api.search(
                search_type="video",
                keyword=keyword,
                page_size=limit
            )

            result_list = data.get("result", [])
            for item in result_list:
                # 搜索结果格式需要适配
                item["owner"] = {
                    "mid": item.get("mid"),
                    "name": item.get("author", ""),
                    "face": item.get("face", "")
                }
                videos.append(self._parse_video_data(item))

        except Exception as e:
            logger.warning(f"搜索视频失败: {e}")

        return videos

    async def get_video_detail(self, video_id: str) -> Optional[Video]:
        """
        获取单个视频信息

        支持通过bvid或avid获取
        """
        try:
            # 判断是bvid还是avid
            if video_id.startswith("BV"):
                data = await self.api.get_video_info(bvid=video_id)
            elif video_id.startswith("AV") or video_id.isdigit():
                aid = int(video_id.replace("AV", ""))
                data = await self.api.get_video_info(aid=aid)
            else:
                # 尝试作为bvid处理
                data = await self.api.get_video_info(bvid=video_id)

            return self._parse_video_data(data)
        except Exception as e:
            logger.warning(f"获取视频信息失败: {e}")
            return None

    async def get_comments(self, video_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取视频评论"""
        comments = []
        try:
            # 先获取视频aid
            video = await self.get_video_detail(video_id)
            if not video:
                return comments

            data = await self.api.get_comments(oid=video.bvid, ps=limit)
            replies = data.get("replies", [])

            for reply in replies:
                comments.append({
                    "rpid": reply.get("rpid"),
                    "mid": reply.get("mid"),
                    "uname": reply.get("member", {}).get("uname", ""),
                    "content": reply.get("content").get("message", ""),
                    "like": reply.get("like", 0),
                    "ctime": reply.get("ctime"),
                })

        except Exception as e:
            logger.warning(f"获取评论失败: {e}")

        return comments

    async def search_creators(self, keyword: str, limit: int = 20) -> List[Creator]:
        """搜索创作者"""
        creators = []
        try:
            data = await self.api.search(
                search_type="bili_user",
                keyword=keyword,
                page_size=limit
            )

            result_list = data.get("result", [])
            for item in result_list:
                # 转换为创作者格式
                creators.append(Creator(
                    platform=self.PLATFORM_NAME,
                    creator_id=str(item.get("mid", "")),
                    name=item.get("uname", ""),
                    avatar_url=item.get("upic", ""),
                    description=item.get("usign", ""),
                    follower_count=item.get("fans", 0),
                ))

        except Exception as e:
            logger.warning(f"搜索创作者失败: {e}")

        return creators

    async def get_creator_videos(self, creator_id: str, pn: int = 1, limit: int = 50) -> List[Video]:
        """获取创作者的视频列表"""
        videos = []
        try:
            mid = int(creator_id)
            # 获取用户视频列表
            data = await self.api.get_user_videos(mid=mid, pn=pn, ps=limit)

            list_data = data.get("archives", [])

            for item in list_data:
                # 用户视频列表格式略有不同，需要适配
                item["owner"] = item.get("author", {})
                parse_video = self._parse_video_data(item)
                parse_video.count = data.get("page", {}).get("count", 0)
                videos.append(parse_video)

        except Exception as e:
            logger.warning(f"获取创作者视频列表失败: {e}")

        return videos

    async def get_creator_info(self, creator_id: str) -> Optional[Creator]:
        """获取创作者信息"""
        try:
            mid = int(creator_id)
            data = await self.api.get_user_info(mid)
            data_stat = await self.api.get_user_archive(mid)
            creator_videos = await self.api.get_user_videos(creator_id, ps=1)
            creator_first_video = await self.api.get_user_videos(creator_id, pn=creator_videos.get('page').get('count'),ps=1)
            data = data | data_stat
            data['last_video_date'] = creator_videos.get('archives', [])[0].get('pubdate', None)
            data['first_video_date'] = creator_first_video.get('archives', [])[0].get('pubdate', None)
            return self._parse_creator_data(data)
        except Exception as e:
            logger.warning(f"获取创作者信息失败: {e}")
            return None

    def _create_video_metrics(self, data: Dict[str, Any]) -> VideoMetrics:
        """创建视频指标对象"""
        stat = data.get("stat", {})

        if isinstance(stat, dict):
            view_count = stat.get("view", 0)
            danmaku_count = stat.get("danmaku", 0)
            reply_count = stat.get("reply", 0)
            favorite_count = stat.get("favorite", 0)
            coin_count = stat.get("coin", 0)
            share_count = stat.get("share", 0)
            like_count = stat.get("like", 0)
            collect_count = stat.get("favorite", 0)
        else:
            view_count = danmaku_count = reply_count = 0
            favorite_count = coin_count = share_count = like_count = collect_count = 0

        # 创建metrics对象
        metrics = VideoMetrics(
            video_id=data.get("bvid", ""),
            platform=self.PLATFORM_NAME,
            play_count=view_count,
            danmaku_count=danmaku_count,
            comment_count=reply_count,
            favorite_count=favorite_count,
            coin_count=coin_count,
            share_count=share_count,
            like_count=like_count,
            collect_count=collect_count,
        )
        metrics.calculate_ratios()

        return metrics

    def _parse_video_data(self, data: Dict[str, Any]) -> Video:
        """解析视频数据"""
        owner = data.get("owner", {})

        # 获取视频tid（分区ID）
        tid = data.get("tid", 0)

        # 根据tid获取主分区名称
        category = BilibiliAPI.get_main_category_name(tid)

        # 创建metrics
        metrics = self._create_video_metrics(data)

        return Video(
            platform=self.PLATFORM_NAME,
            video_id=data.get("bvid", ""),
            title=data.get("title", ""),
            description=data.get("desc", ""),
            url=f"https://www.bilibili.com/video/{data.get('bvid', '')}",
            cover_url=data.get("pic", ""),
            publish_time=datetime.fromtimestamp(data.get("pubdate", 0)) if data.get("pubdate") else None,
            duration=data.get("duration", 0),
            metrics=metrics,
            category=category,
            # B站特有字段
            bvid=data.get("bvid", ""),
            creator_id=str(owner.get("mid", "")),
            creator_name=owner.get("name", ""),
        )

    def _parse_creator_data(self, data: Dict[str, Any]) -> Creator:
        """解析创作者数据"""
        # 处理可能的字段差异
        if "card" in data:
            # 用户名片格式
            card = data["card"]
            user_data = {
                "mid": int(card.get("mid", 0)),
                "name": card.get("name", ""),
                "face": card.get("face", ""),
                "sign": card.get("sign", ""),
                "fans": card.get("fans", 0),
                "friend": card.get("friend", 0),
            }

            return Creator(
                platform=self.PLATFORM_NAME,
                creator_id=str(user_data.get("mid", "")),
                name=user_data.get("name", ""),
                url=f"https://space.bilibili.com/{user_data.get('mid', '')}",
                avatar_url=user_data.get("face", ""),
                description=user_data.get("sign", ""),
                follower_count=data.get("follower", 0),
                following_count=card.get("attention", 0),
                total_likes=data.get("like_num", 0),
                video_count=data.get("archive_count", 0),
                avg_play_count=(data.get("archive").get("view") // data.get("archive_count", 0)) if data.get(
                    "archive_count", 0) else 0,
                last_video_date=datetime.fromtimestamp(data.get("last_video_date", 0)),
                first_video_date=datetime.fromtimestamp(data.get("first_video_date", 0)),
            )
        return None


# 便捷函数
def get_bilibili_adapter(cookie: str = None) -> BilibiliAdapter:
    """创建B站适配器实例"""
    return BilibiliAdapter(cookie)
