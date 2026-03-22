from http.cookiejar import MozillaCookieJar
from typing import Dict, Any, List

import httpx
from loguru import logger


class BilibiliAPI:
    """B站API端点"""

    # 分区视频API
    ZION_INFO = "https://api.bilibili.com/x/web-interface/dynamic/region"

    # 视频信息API
    VIEW_INFO = "https://api.bilibili.com/x/web-interface/view"
    VIEW_DETAIL = "https://api.bilibili.com/x/web-interface/view/detail"

    # 排行榜API
    RANKING_V2 = "https://api.bilibili.com/x/web-interface/ranking/v2"

    # 用户信息API
    USER_INFO = "https://api.bilibili.com/x/web-interface/card"

    # 用户状态
    USER_ARCHIVE = "https://api.bilibili.com/x/space/upstat"

    # 用户视频列表API
    USER_VIDEO_LIST = "https://api.bilibili.com/x/space/arc/list"

    # 搜索API
    SEARCH = "https://api.bilibili.com/x/web-interface/search/type"
    SEARCH_SUGGEST = "https://s.search.bilibili.com/main/suggest"

    # 评论API
    COMMENT_LIST = "https://api.bilibili.com/x/v2/reply"
    COMMENT_PIN = "https://api.bilibili.com/x/v2/reply/pin"

    # 视频主分区
    VIDEO_MAIN_ZONES = {
        "动画": 1,
        "音乐": 3,
        "游戏": 4,
        "娱乐": 5,
        "电视剧": 11,
        "番剧": 13,
        "电影": 23,
        "知识": 36,
        "舞蹈": 129,
        "时尚": 155,
        "生活": 160,
        "国创": 167,
        "纪录片": 177,
        "影视": 181,
        "科技": 188,
        "资讯": 202,
        "美食": 211,
        "动物圈": 217,
        "鬼畜": 219,
        "汽车": 223,
        "运动": 234,
        "VLOG": -1,
    }

    # 视频分区
    VIDEO_ZONES = {
        # 杂项
        -1: {
        },
        # 动画
        1: {
            "MAD·AMV": 24,
            "MMD·3D": 25,
            "同人·手书": 47,
            "配音": 257,
            "手办·模玩": 210,
            "特摄": 86,
            "动漫杂谈": 253,
            "综合": 27,
        },
        # 音乐
        3: {
            "原创音乐": 28,
            "音乐现场": 29,
            "翻唱": 31,
            "演奏": 59,
            "乐评盘点": 243,
            "VOCALOID·UTAU": 30,
            "MV": 193,
            "音乐粉丝饭拍": 266,
            "AI音乐": 265,
            "电台": 267,
            "音乐教学": 244,
            "音乐综合·UTAU": 130,
        },
        # 游戏
        4: {
            "单机游戏": 17,
            "电子竞技": 171,
            "手机游戏": 172,
            "网络游戏": 65,
            "桌游棋牌": 173,
            "GMV": 121,
            "音游": 136,
            "Mugen": 19,
        },
        # 娱乐
        5: {
            "娱乐杂谈": 241,
            "CP安利": 262,
            "颜值安利": 263,
            "娱乐粉丝创作": 242,
            "娱乐资讯": 264,
            "明星综合": 137,
            "综艺": 71,
        },
        # 电视剧
        11: {
            "国产剧": 185,
            "海外剧": 187,
        },
        # 番剧
        13: {
            "资讯": 51,
            "官方延伸": 152,
            "完结动画": 32,
            "连载动画": 33,
        },
        # 电影
        23: {
            "华语电影": 147,
            "欧美电影": 145,
            "日本电影": 146,
            "其他国家": 83,
        },
        # 知识
        36: {
            "科学科普": 201,
            "社科·法律·心理": 124,
            "人文历史": 228,
            "财经商业": 207,
            "校园学习": 208,
            "职业职场": 209,
            "设计·创意": 229,
            "野生技术协会": 122,
        },
        # 舞蹈
        129: {
            "宅舞": 20,
            "街舞": 198,
            "明星舞蹈": 199,
            "国风舞蹈": 200,
            "颜值·网红舞": 255,
            "舞蹈综合": 154,
        },
        # 时尚
        155: {
            "美妆护肤": 157,
            "仿妆cos": 252,
            "穿搭": 158,
            "时尚潮流": 159,
        },
        # 生活
        160: {
            "搞笑": 138,
            "亲子": 254,
            "出行": 250,
            "三农": 251,
            "家居房产": 239,
            "手工": 161,
            "绘画": 162,
            "日常": 21,
        },
        # 国创
        167: {
            "国产动画": 155,
            "国产原创相关": 168,
            "布袋戏": 169,
            "资讯": 170,
            "动态漫·广播剧": 195,
        },
        # 纪录片
        177: {
            "人文·历史": 37,
            "科学·探索·自然": 178,
            "军事": 179,
            "社会·美食·旅行": 180,
        },
        # 影视
        181: {
            "影视杂谈": 182,
            "影视剪辑": 183,
            "影视整活": 260,
            "AI影像": 259,
            "预告·资讯": 184,
            "小剧场": 85,
            "短片": 256,
            "影视综合": 261,
        },
        # 科技
        188: {
            "数码": 95,
            "软件应用": 230,
            "计算机技术": 231,
            "科工机械": 232,
            "极客DIY": 233,
        },
        # 资讯
        202: {
            "热点": 203,
            "环球": 204,
            "社会": 205,
            "综合": 206,
        },
        # 美食
        211: {
            "美食制作": 76,
            "美食侦探": 212,
            "美食测评": 213,
            "田园美食": 214,
            "美食记录": 215,
        },
        # 动物圈
        217: {
            "喵星人": 218,
            "汪星人": 219,
            "小宠异宠": 222,
            "野生动物": 221,
            "动物二创": 220,
            "动物综合": 75,
        },
        # 鬼畜
        219: {
            "鬼畜调教": 22,
            "音MAD": 26,
            "人力VOCALOID": 126,
            "鬼畜剧场": 216,
            "教程演示": 127,
        },
        # 汽车
        223: {
            "汽车知识科普": 258,
            "购车攻略": 227,
            "新能源车": 247,
            "赛车": 245,
            "改装玩车": 246,
            "摩托车": 240,
            "房车": 248,
            "汽车生活": 176,
        },
        # 运动
        234: {
            "篮球": 235,
            "足球": 249,
            "健身": 164,
            "竞技体育": 236,
            "运动文化": 237,
            "运动综合": 238,
        },
    }

    def _load_cookies(self, cookie_file: str) -> str:
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
        return '; '.join([f"{k}={v}" for k, v in cookies_dict.items()])

    def __init__(self, timeout: int = 30, cookie_file: str = None):
        self.client = httpx.AsyncClient(timeout=timeout)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bilibili.com"
        }

        self.headers["Cookie"] = self._load_cookies(cookie_file)

    async def close(self):
        await self.client.aclose()

    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发送请求并处理响应"""
        kwargs.setdefault("headers", self.headers)
        response = await self.client.request(method, url, **kwargs)
        data = response.json()

        if data.get("code") != 0:
            raise Exception(f"API Error: {data.get('message', 'Unknown error')}")

        return data.get("data", {})

    async def get_region_videos(self, rid: int, pn: int = 1, ps: int = 14) -> Dict[str, Any]:
        """
        获取分区视频

        API: https://api.bilibili.com/x/web-interface/dynamic/region
        参数:
            rid: 分区tid (0=全站)
            pn: 页码
            ps: 每页条数
        """
        params = {
            "rid": rid,
            "pn": pn,
            "ps": ps,
        }

        return await self._request("GET", BilibiliAPI.ZION_INFO, params=params)

    async def get_video_info(self, bvid: str = None, aid: int = None) -> Dict[str, Any]:
        """
        获取视频详细信息

        API: https://api.bilibili.com/x/web-interface/view
        参数: bvid 或 aid (二选一)
        """
        params = {}
        if bvid:
            params["bvid"] = bvid
        elif aid:
            params["aid"] = aid
        else:
            raise ValueError("必须提供 bvid 或 aid")

        return await self._request("GET", BilibiliAPI.VIEW_INFO, params=params)

    async def get_video_detail(self, bvid: str = None, aid: int = None) -> Dict[str, Any]:
        """
        获取视频详细信息(包含推荐等)

        API: https://api.bilibili.com/x/web-interface/view/detail
        """
        params = {}
        if bvid:
            params["bvid"] = bvid
        elif aid:
            params["aid"] = aid
        else:
            raise ValueError("必须提供 bvid 或 aid")

        return await self._request("GET", BilibiliAPI.VIEW_DETAIL, params=params)

    async def get_ranking(self, rid: int = 0, type_: str = "all",
                          web_location: str = "333.934") -> List[Dict[str, Any]]:
        """
        获取分区视频排行榜

        API: https://api.bilibili.com/x/web-interface/ranking/v2

        参数:
            rid: 分区tid (0=全站)
            type_: 排行榜类型 (all/rokkie/origin)
            web_location: 位置标识
        """
        params = {
            "rid": rid,
            "type": type_,
            "web_location": web_location
        }
        data = await self._request("GET", BilibiliAPI.RANKING_V2, params=params)
        return data.get("list", [])

    async def get_user_info(self, mid: int) -> Dict[str, Any]:
        """
        获取用户空间详细信息

        API: https://api.bilibili.com/x/web-interface/card

        WBI版本参数：signed_params = await self.wbi_signer.get_signed_params(params)
        """
        params = {"mid": mid}
        return await self._request("GET", BilibiliAPI.USER_INFO, params=params)

    async def get_user_archive(self, mid: int) -> Dict[str, Any]:
        """
        获取用户视频总播放量

        API: https://api.bilibili.com/x/space/upstat

        """
        params = {"mid": mid}
        return await self._request("GET", BilibiliAPI.USER_ARCHIVE, params=params)

    async def get_user_videos(self, mid: int, pn: int = 1, ps: int = 30) -> Dict[str, Any]:
        """
        获取用户视频列表

        API: https://api.bilibili.com/x/space/arc/list

        参数:
            mid: 用户mid
            pn: 页码
            ps: 每页数量(最大50)
        """
        params = {"mid": mid, "pn": pn, "ps": ps}
        return await self._request("GET", BilibiliAPI.USER_VIDEO_LIST, params=params)

    async def search(self, search_type: str = "video", keyword: str = "",
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        搜索

        API: https://api.bilibili.com/x/web-interface/search/type

        参数:
            search_type: video/user/bangumi/live
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
        """
        params = {
            "search_type": search_type,
            "keyword": keyword,
            "page": page,
            "pagesize": page_size
        }
        return await self._request("GET", BilibiliAPI.SEARCH, params=params)

    async def get_comments(self, oid: int, pn: int = 1, ps: int = 20,
                           type_: int = 1) -> Dict[str, Any]:
        """
        获取视频评论

        API: https://api.bilibili.com/x/v2/reply

        参数:
            oid: 稿件avid
            pn: 页码
            ps: 每页数量
            type_: 1=视频 2=话题
        """
        params = {
            "oid": oid,
            "pn": pn,
            "ps": ps,
            "type": type_
        }
        return await self._request("GET", BilibiliAPI.COMMENT_LIST, params=params)
