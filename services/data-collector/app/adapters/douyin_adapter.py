"""
Douyin (TikTok China) Data Adapter
基于 DouK-Downloader API 服务 (http://127.0.0.1:5555)
"""
import asyncio
import json
import os
from http.cookiejar import MozillaCookieJar
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
import aiohttp

from app.adapters.base import PlatformAdapter, DataSourceFallbackMixin
from app.schemas import Creator, Video, VideoMetrics
from app.core.config import settings


class DouKAPI:
    """DouK-Downloader API 客户端"""

    def __init__(self, base_url: str = "http://127.0.0.1:5555", token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.douyin.com/",
            "Origin": "https://www.douyin.com",
        }
        if token:
            self.headers["token"] = token

    async def _get(self, url: str, params: Dict = None, cookies: dict = None) -> Dict:
        """发送GET请求"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers, cookies=cookies,
                                       timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    text = await resp.text()
                    try:
                        return json.loads(text)
                    except:
                        return {"raw": text, "status": resp.status}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {}

    async def _post(self, endpoint: str, data: Dict = None) -> Dict:
        """发送POST请求"""
        url = f"{self.base_url}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=self.headers,
                                        timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    result = await resp.json()

                    if '成功' in result.get("message"):
                        return result.get("data", {})
                    else:
                        logger.error(f"API error: {result}")
                        return {}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {}

    async def get_hot_search_list(self) -> List[Dict]:
        """
        获取抖音热搜列表
        直接调用抖音API: https://www.douyin.com/aweme/v1/web/hot/search/list/
        返回: 热搜标题、热度值、label
        """
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"

        try:
            data = await self._get(url)

            if not data or "raw" in data:
                logger.error("Failed to fetch hot search list")
                return []

            status_code = data.get('status_code', 0)
            if status_code != 0:
                logger.error(f"API error: {status_code}")
                return []

            word_list = data.get('data', {}).get('word_list', [])

            # 只返回热搜标题、热度值、label
            hot_list = []
            for item in word_list:
                hot_list.append({
                    "title": item.get('word', ''),
                    "hot_value": item.get('hot_value', 0),
                    "label": item.get('label', 0),  # 0=普通, 1=热搜, 2=上升, 3=爆
                    "position": item.get('position', 0),
                    "video_count": item.get('video_count', 0)
                })

            logger.info(f"Fetched {len(hot_list)} hot search words")
            return hot_list

        except Exception as e:
            logger.error(f"Failed to get hot search list: {e}")
            return []

    """
        DouK免费接口（失效）
    """
    # async def search_videos(
    #         self,
    #         keyword: str,
    #         cookie: str = None,
    #         proxy: str = None,
    #         pages: int = 1,
    #         sort_type: int = 0,  # 0=综合, 1=最多点赞, 2=最新
    #         publish_time: int = 0,  # 0=全部, 1=一天内, 7=一周内, 180=半年内
    #         duration: int = 0  # 0=全部, 1=1分钟以下, 2=1-5分钟, 3=5分钟以上
    # ) -> List[Dict]:
    #     """
    #     获取视频搜索数据
    #     POST /douyin/search/video
    #     """
    #     data = {
    #         "keyword": keyword,
    #         "cookie": cookie or "",
    #         "proxy": proxy or "",
    #         "pages": pages,
    #         "sort_type": sort_type,
    #         "publish_time": publish_time,
    #         "duration": duration,
    #         "search_range": 0,  # 0=全部
    #         "channel": 1  # 视频搜索
    #     }
    #     result = await self._post("/douyin/search/video", data)
    #
    #     if isinstance(result, list):
    #         return result
    #     elif isinstance(result, dict):
    #         return result.get("list", [])
    #     return []

    """
        网页端/移动端接口（失效）
    """
    async def search_videos(
            self,
            keyword: str,
            cookie: dict = None,
            count: int = 20,
            cursor: int = 0,
            sort_type: int = 0,
            publish_time: int = 0,
            duration: int = 0
    ) -> List[Dict]:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            cookie: cookie
            count: 返回数量（默认20，最大50）
            cursor: 分页游标（默认0）
            sort_type: 排序类型
                0: 综合排序
                1: 最新发布
                2: 最多点赞
            publish_time: 发布时间
                0: 全部
                1: 一天内
                7: 一周内
                180: 半年内
            duration: 视频时长
                0: 全部
                1: 1分钟以下
                2: 1-5分钟
                3: 5分钟以上

        Returns:
            搜索结果字典
        """
        url = f"https://www.douyin.com/aweme/v1/web/search/item/"

        data = {
            # 网页端接口 https://www.douyin.com/aweme/v1/web/search/item/
            "device_platform": "webapp",
            "aid": "6383",
            "keyword": keyword,
            "count": count,
            "cursor": cursor,
            "sort_type": sort_type,
            "publish_time": publish_time,
            "duration": duration,
            "search_source": "search_sug",
            "search_id": "",
            "query_correct_type": 1,
            # 移动端接口 https://aweme.snssdk.com/aweme/v1/search/item/
            # "keyword": keyword,
            # "count": count,
            # "cursor": cursor,
            # "search_source": "search_sug",
            # "type": 1,  # 0=综合, 1=视频
            # "hot_search": sort_type,
            # "version_code": "260300",
            # "device_platform": "android",
        }

        result = await self._get(url, data, cookies=cookie)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("data", [])
        return []

    async def search_users(
            self,
            keyword: str,
            cookie: str = None,
            proxy: str = None,
            pages: int = 1
    ) -> List[Dict]:
        """
        获取用户搜索数据
        POST /douyin/search/user
        """
        data = {
            "keyword": keyword,
            "cookie": cookie or "",
            "proxy": proxy or "",
            "pages": pages,
            "channel": 2  # 用户搜索
        }
        result = await self._post("/douyin/search/user", data)

        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("list", [])
        return []

    async def search_live(
            self,
            keyword: str,
            cookie: str = None,
            proxy: str = None,
            pages: int = 1
    ) -> List[Dict]:
        """
        获取直播搜索数据
        POST /douyin/search/live

        Args:
            keyword: 关键词
            cookie: 抖音Cookie
            proxy: 代理
            pages: 总页数
        """
        data = {
            "cookie": cookie or "",
            "proxy": proxy or "",
            "keyword": keyword,
            "pages": pages,
            "channel": 3  # 直播搜索
        }
        result = await self._post("/douyin/search/live", data)

        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("list", [])
        return []

    async def get_video_detail(self, video_id: str, cookie: str = None, proxy: str = None) -> Dict:
        """
        获取单个作品数据
        POST /douyin/detail
        """
        data = {
            "detail_id": video_id,
            "cookie": cookie or "",
            "proxy": proxy or ""
        }
        return await self._post("/douyin/detail", data)

    async def get_mix_videos(
            self,
            mix_id: str = None,
            detail_id: str = None,
            cookie: str = None,
            proxy: str = None,
            cursor: int = 0,
            count: int = 12
    ) -> List[Dict]:
        """
        获取合集作品数据
        POST /douyin/mix
        
        mix_id 和 detail_id 二选一，只需传入其中之一即可
        
        Args:
            mix_id: 抖音合集ID
            detail_id: 属于合集的抖音作品ID
            cookie: 抖音Cookie
            proxy: 代理
            cursor: 分页游标
            count: 每页数量
        """
        data = {
            "cookie": cookie or "",
            "proxy": proxy or "",
            "mix_id": mix_id,
            "detail_id": detail_id,
            "cursor": cursor,
            "count": count
        }
        result = await self._post("/douyin/mix", data)

        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("list", [])
        return []

    async def get_live_data(
            self,
            web_rid: str,
            cookie: str = None,
            proxy: str = None
    ) -> Dict:
        """
        获取直播数据
        POST /douyin/live

        Args:
            web_rid: 抖音直播 web_rid
            cookie: 抖音Cookie
            proxy: 代理
        """
        data = {
            "cookie": cookie or "",
            "proxy": proxy or "",
            "web_rid": web_rid
        }
        return await self._post("/douyin/live", data)

    async def get_comments(
            self,
            video_id: str,
            cookie: str = None,
            proxy: str = None,
            pages: int = 1,
            count_reply: int = 3
    ) -> List[Dict]:
        """
        获取作品评论数据
        POST /douyin/comment
        """
        data = {
            "detail_id": video_id,
            "cookie": cookie or "",
            "proxy": proxy or "",
            "pages": pages,
            "count": 20,
            "cursor": 0,
            "count_reply": count_reply,
            "reply": False
        }
        result = await self._post("/douyin/comment", data)

        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("list", [])
        return []

    async def get_comment_replies(
            self,
            video_id: str,
            comment_id: str,
            cookie: str = None,
            proxy: str = None,
            pages: int = 1,
            cursor: int = 0,
            count: int = 3
    ) -> List[Dict]:
        """
        获取评论回复数据
        POST /douyin/reply
        
        Args:
            video_id: 抖音作品ID
            comment_id: 评论ID
            cookie: 抖音Cookie
            proxy: 代理
            pages: 最大请求次数
            cursor: 分页游标
            count: 每页数量
        """
        data = {
            "cookie": cookie or "",
            "proxy": proxy or "",
            "detail_id": video_id,
            "comment_id": comment_id,
            "pages": pages,
            "cursor": cursor,
            "count": count
        }
        result = await self._post("/douyin/reply", data)

        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("list", [])
        return []

    async def get_creator_info(
            self,
            sec_user_id: str,
            cookie: str = None,
    ) -> List[Dict]:
        """
        获取账号详细信息
        POST /aweme/v1/web/user/profile/other/
        """
        url = "https://www.douyin.com//aweme/v1/web/user/profile/other/"

        data = {
            "sec_user_id": sec_user_id,
            "aid": "6383",
            "device_platform": "webapp",
            "version_code": "210800",
            "version_name": "21.8.0",
        }
        result = await self._get(url, data, cookies=cookie)

        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("user", [])
        return []

    async def get_creator_videos(
            self,
            sec_user_id: str,
            cookie: str = None,
            proxy: str = None,
            tab: str = "post",
            pages: int = 1
    ) -> List[Dict]:
        """
        获取账号作品数据
        POST /douyin/account
        """
        data = {
            "sec_user_id": sec_user_id,
            "cookie": cookie or "",
            "proxy": proxy or "",
            "tab": tab,
            "pages": pages,
            "count": 20
        }
        result = await self._post("/douyin/account", data)

        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("list", [])
        return []

    async def get_share_url(self, text: str, proxy: str = None) -> Optional[str]:
        """
        获取分享链接重定向的完整链接
        POST /douyin/share

        Args:
            text: 包含分享链接的字符串
            proxy: 代理
        """
        data = {
            "text": text,
            "proxy": proxy or ""
        }
        result = await self._post("/douyin/share", data)

        if result and result.get("url"):
            return result.get("url")
        return None


class DouyinAdapter(PlatformAdapter, DataSourceFallbackMixin):
    """抖音数据适配器 - 基于 DouK-Downloader API"""

    # 支持的排序方式
    SORT_OPTIONS = {
        "comprehensive": 0,  # 综合
        "most_liked": 1,  # 最多点赞
        "latest": 2  # 最新
    }

    # 发布时间选项
    PUBLISH_TIME_OPTIONS = {
        "all": 0,
        "day": 1,
        "week": 7,
        "half_year": 180
    }

    # 时长选项
    DURATION_OPTIONS = {
        "all": 0,
        "under_1min": 1,
        "1_to_5min": 2,
        "over_5min": 3
    }

    def __init__(
            self,
            douk_url: str = "http://127.0.0.1:5555",
            token: str = None,
            cookie: str = None,
            proxy: str = None
    ):
        super().__init__()
        self.platform = "douyin"

        # DouK API 配置
        self.douk_url = douk_url
        self.token = token
        self.cookie = None
        self.cookie_dict = None
        self.proxy = proxy
        # 加载cookies（如果没有提供则使用默认路径）
        if cookie:
            self._load_cookies(cookie)

        # 初始化API客户端
        self.api = DouKAPI(base_url=douk_url, token=token)
        self.default_cookie = self.cookie
        self.default_proxy = proxy

    async def get_trending_videos(
            self,
            limit: int = 100,
            count: int = 5,
    ) -> List[Video]:
        """
        获取抖音热搜列表
        
        直接调用抖音热搜API: https://www.douyin.com/aweme/v1/web/hot/search/list/
        返回热榜标题、热度值、label
        
        Args:
            limit: 返回热搜数量限制
            count: 返回每个热搜相关视频数量
            
        Returns:
            热搜列表，每项包含: word, hot_value, label
        """
        logger.info(f"Fetching trending hot words from Douyin, limit: {limit}， count: {count}")

        try:
            # 调用热搜API
            hot_list = await self.api.get_hot_search_list()

            if not hot_list:
                logger.warning("No hot search data fetched")
                return []

            tasks = []
            for item in hot_list[:limit]:
                title = item.get('title', '')
                task = self.search_videos(keyword=title, limit=count, sort_by="hot")
                tasks.append(task)

                # ✅ 并发执行所有搜索
            videos = await asyncio.gather(*tasks, return_exceptions=True)
            return videos

        except Exception as e:
            logger.error(f"Failed to get trending videos: {e}")
        return []


    async def search_videos(
            self,
            keyword: str,
            limit: int = 20,
            sort_by: str = "hot",
            publish_time: str = "all",
            duration: str = "all",
    ) -> List[Video]:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            sort_by: 排序方式 (comprehensive/hot/latest)
            publish_time: 发布时间 (all/day/week/half_year)
            duration: 视频时长 = "all/under_1min/1_to_5min/over_5min",
        """
        logger.info(f"Searching videos: {keyword}, sort: {sort_by}, time: {publish_time}")

        try:
            # 转换排序参数
            sort_type_map = {
                "hot": self.SORT_OPTIONS["most_liked"],
                "comprehensive": self.SORT_OPTIONS["comprehensive"],
                "latest": self.SORT_OPTIONS["latest"]
            }
            sort_type = sort_type_map.get(sort_by, 0)

            # 转换时间参数
            time_map = {
                "all": self.PUBLISH_TIME_OPTIONS["all"],
                "day": self.PUBLISH_TIME_OPTIONS["day"],
                "week": self.PUBLISH_TIME_OPTIONS["week"],
                "half_year": self.PUBLISH_TIME_OPTIONS["half_year"]
            }
            publish = time_map.get(publish_time, 0)

            duration_map = {
                "all": self.DURATION_OPTIONS["all"],
                "under_1min": self.DURATION_OPTIONS["under_1min"],
                "1_to_5min": self.DURATION_OPTIONS["1_to_5min"],
                "over_5min": self.DURATION_OPTIONS["over_5min"]
            }
            duration = duration_map.get(duration, 0)

            videos_data = await self.api.search_videos(
                keyword=keyword,
                cookie=self.cookie_dict,
                # cookie=self.default_cookie,
                # proxy=self.default_proxy,
                # pages=1,
                sort_type=sort_type,
                publish_time=publish,
                duration=duration,
            )

            videos = []
            for item in videos_data[:limit]:
                try:
                    aweme_info = item.get("aweme_info", {})
                    if aweme_info:
                        aweme_info = {
                            "id": aweme_info.get("aweme_id"),
                            "desc": aweme_info.get("desc"),
                            "creator_id": aweme_info.get("author").get("sec_uid"),
                            "sec_uid": aweme_info.get("author").get("sec_uid"),
                            "nickname": aweme_info.get("author").get("nickname"),
                            "play_count": aweme_info.get("statistics").get("play_count"),
                            "digg_count": aweme_info.get("statistics").get("digg_count"),
                            "comment_count": aweme_info.get("statistics").get("comment_count"),
                            "share_count": aweme_info.get("statistics").get("share_count"),
                            "collect_count": aweme_info.get("statistics").get("collect_count"),
                            "dynamic_cover": aweme_info.get("video").get("dynamic_cover").get("url_list")[0],
                            "duration": aweme_info.get("video").get("duration"),
                            "create_time": aweme_info.get("create_time"),
                        }
                    video = self._parse_video_data(aweme_info)
                    if video.title:
                        videos.append(video)
                except Exception as e:
                    logger.error(f"Failed to parse video: {e}")
                    continue

            logger.info(f"Found {len(videos)} videos for keyword: {keyword}")
            return videos

        except Exception as e:
            logger.error(f"Failed to search videos: {e}")
            return []


    async def get_video_detail(self, video_id: str) -> Optional[Video]:
        """
        获取视频详情

        Args:
            video_id: 抖音视频ID (aweme_id)
        """
        logger.info(f"Fetching video detail: {video_id}")

        try:
            data = await self.api.get_video_detail(
                video_id=video_id,
                cookie=self.default_cookie,
                proxy=self.default_proxy
            )

            if data:
                return self._parse_video_data(data)

            return None

        except Exception as e:
            logger.error(f"Failed to get video detail: {e}")
            return None


    async def get_video_comments(
            self,
            video_id: str,
            limit: int = 20,
            count_reply: int = 3
    ) -> List[Dict]:
        """
        获取视频评论

        Args:
            video_id: 视频ID
            limit: 返回评论数量
            count_reply: 评论回复数量
        """
        logger.info(f"Fetching comments for video: {video_id}")

        try:
            comments_data = await self.api.get_comments(
                video_id=video_id,
                cookie=self.default_cookie,
                proxy=self.default_proxy,
                pages=1,
                count_reply=count_reply,
            )

            return comments_data[:limit]

        except Exception as e:
            logger.error(f"Failed to get comments: {e}")
            return []


    async def get_creator_info(self, sec_uid: str) -> Optional[Creator]:
        """
        获取创作者信息

        Args:
            sec_uid: 创作者 sec_uid
        """
        logger.info(f"Fetching creator info: {sec_uid}")

        try:
            # 尝试获取账号作品来获取作者信息
            account_info = await self.api.get_creator_info(
                sec_user_id=sec_uid,
                cookie=self.cookie_dict,
            )

            if account_info:
                return Creator(
                    creator_id=account_info.get("sec_uid", ""),
                    platform="douyin",
                    name=account_info.get("nickname", ""),
                    url=f'https://www.douyin.com/user/{account_info.get("sec_uid", "")}',
                    avatar_url=account_info.get("avatar_larger", {}).get("url_list", [""])[0] if isinstance(
                        account_info.get("avatar_larger"), dict) else "",
                    follower_count=account_info.get("follower_count", 0),
                    video_count=account_info.get("aweme_count", 0)
                )
            return None

        except Exception as e:
            logger.error(f"Failed to get creator info: {e}")
            return None


    async def get_creator_videos(
            self,
            sec_uid: str,
            limit: int = 50
    ) -> List[Video]:
        """
        获取创作者视频列表

        Args:
            sec_uid: 创作者 sec_uid
            limit: 返回数量
        """
        logger.info(f"Fetching videos for creator: {sec_uid}")

        try:
            videos_data = await self.api.get_creator_videos(
                sec_user_id=sec_uid,
                cookie=self.default_cookie,
                proxy=self.default_proxy,
                tab="post",
                pages=1
            )

            videos = []
            for item in videos_data[:limit]:
                try:
                    video = self._parse_video_data(item)
                    if video.title:
                        videos.append(video)
                except Exception as e:
                    logger.error(f"Failed to parse video: {e}")
                    continue

            logger.info(f"Fetched {len(videos)} videos for creator: {sec_uid}")
            return videos

        except Exception as e:
            logger.error(f"Failed to get creator videos: {e}")
            return []


    def _load_cookies(self, cookie_file: str) -> None:
        """
        从Netscape格式的cookies.txt文件加载cookies
        """
        # 创建MozillaCookieJar实例
        cookie_jar = MozillaCookieJar(cookie_file)

        # 加载cookies（ignore_discard=True 保留所有cookies，包括过期的）
        # ignore_expires=True 忽略过期时间检查
        cookie_jar.load(ignore_discard=True, ignore_expires=True)

        # 转换为字典格式（aiohttp需要的格式）
        cookies_dict = {}
        for cookie in cookie_jar:
            cookies_dict[cookie.name] = cookie.value

        logger.info(f"Successfully loaded {len(cookies_dict)} cookies")
        self.cookie_dict = cookies_dict
        self.cookie = '; '.join([f"{k}={v}" for k, v in cookies_dict.items()])


    def _parse_video_data(self, data: Dict[str, Any]) -> Video:
        """解析DouK返回的视频数据"""
        # 创建指标对象
        metrics = VideoMetrics(
            video_id=data.get("id", ""),
            platform="douyin",
            play_count=data.get("play_count", -1),
            like_count=data.get("digg_count", 0),
            comment_count=data.get("comment_count", 0),
            share_count=data.get("share_count", 0),
            favorite_count=data.get("collect_count", 0)
        )
        metrics.calculate_ratios()

        # 检测爆款特征
        viral_factors = self._detect_viral_patterns(data, metrics)

        # 封面图
        cover_url = data.get("dynamic_cover", "")

        # 时长
        duration = data.get("duration", "00:00:00")
        if not isinstance(duration, int):
            hour, minute, second = duration.split(':')
            duration = int(hour) * 60 * 60 + int(minute) * 60 + int(second)

        # 发布时间
        publish_time = data.get("create_time", None)

        video = Video(
            video_id=data.get("id", ""),
            platform="douyin",
            title=data.get("desc", ""),
            description=data.get("desc", ""),
            url=f"https://www.douyin.com/video/{data.get('id', '')}",
            creator_id=data.get("sec_uid", ""),
            creator_name=data.get("nickname", ""),
            cover_url=cover_url,
            duration=duration,
            metrics=metrics,
            publish_time=publish_time,
            viral_factors=viral_factors
        )

        return video


    def _detect_viral_patterns(self, data: Dict, metrics: VideoMetrics) -> Dict[str, Any]:
        """检测抖音爆款特征"""
        patterns = {}

        # 高互动率
        if metrics.engagement_rate > 0.15:
            patterns['high_engagement'] = True

        # 高分享率
        if metrics.share_ratio > 0.2:
            patterns['high_sharing'] = True

        # 高收藏率
        if metrics.engagement_rate > 0.1:
            patterns['high_collect_ratio'] = True

        return patterns


def get_douyin_adapter(
        douk_url: str = "http://127.0.0.1:5555",
        token: str = None,
        cookie: str = None,
        proxy: str = None
) -> DouyinAdapter:
    """
    获取抖音适配器实例
    
    Args:
        douk_url: DouK-Downloader 服务地址
        token: API令牌（可选）
        cookie: 抖音Cookie（可选，用于获取更多数据）
        proxy: 代理服务器（可选）
    """
    return DouyinAdapter(
        douk_url=douk_url,
        token=token,
        cookie=cookie,
        proxy=proxy
    )
