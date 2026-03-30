"""
Test script for Bilibili collector tasks

参考 douyin_collector_test.py 编写的 B站 数据采集测试
"""
import asyncio
import sys
import time

sys.path.insert(0, '.')

from app.adapters.bilibili_adapter import BilibiliAdapter
from app.services.cleaning_pipeline import cleaning_pipeline
from app.services.viral_detector import viral_detector

adapter = BilibiliAdapter(cookie="../../cookies/cookies_bilibili.txt")


async def scan_bilibili_hot():
    """测试B站热搜/排行榜采集"""
    print("=" * 50)
    print("Testing Bilibili Hot/Ranking Scan")
    print("=" * 50)

    # 测试全站排行榜
    hot_videos = await adapter.get_trending_videos(limit=10)

    print(f"\nFetched {len(hot_videos)} trending videos from Bilibili")
    print("\n--- Sample Data ---")
    for video in hot_videos[:3]:
        print(f"\nTitle: {video.title}")
        print(f"BVID: {video.video_id}")
        print(f"Play Count: {video.metrics.play_count}")
        print(f"Like Count: {video.metrics.like_count}")
        print(f"Danmaku Count: {video.metrics.danmaku_count}")
        print(f"Engagement Rate: {video.metrics.engagement_rate:.4f}")

    return scan_bilibili_hot


async def scan_bilibili_category():
    """测试B站分区排行榜采集"""
    print("\n" + "=" * 50)
    print("Testing Bilibili Category Ranking")
    print("=" * 50)

    # 测试动画分区
    hot_videos = await adapter.get_region_videos(rid=1)

    print(f"\nFetched {len(hot_videos)} videos from 动画分区")
    print("\n--- Sample Data ---")
    for video in hot_videos[:3]:
        print(f"\nTitle: {video.title}")
        print(f"Category: {video.metrics.danmaku_count}")  # 借用字段显示分区
        print(f"Play Count: {video.metrics.play_count}")

    return len(hot_videos)


async def search_videos():
    """测试关键词搜索"""
    print("\n" + "=" * 50)
    print("Testing Bilibili Video Search")
    print("=" * 50)

    videos = await adapter.search_videos(
        keyword="美食",
        limit=5
    )

    print(f"\nFound {len(videos)} videos for keyword: 美食")
    print("\n--- Sample Data ---")
    for video in videos[:3]:
        print(f"\nTitle: {video.title[:50]}...")
        print(f"BVID: {video.video_id}")
        print(f"Creator: {video.creator_name}")
        print(f"Play Count: {video.metrics.play_count}")
        print(f"Like Count: {video.metrics.like_count}")
        print(f"Engagement Rate: {video.metrics.engagement_rate:.4f}")

    return len(videos)


async def get_video_detail():
    """测试获取视频详情"""
    print("\n" + "=" * 50)
    print("Testing Bilibili Video Detail")
    print("=" * 50)

    # 使用一个已知的B站视频BV号测试
    # BV1Eg411v7a1 是文档中的示例视频
    video = await adapter.get_video_detail('BV1cwpnekEmG')

    if video:
        print(f"\nTitle: {video.title}")
        print(f"BVID: {video.video_id}")
        print(f"AID: {video.bvid}")
        print(f"Description: {video.description[:100]}...")
        print(f"Play Count: {video.metrics.play_count}")
        print(f"Like Count: {video.metrics.like_count}")
        print(f"Comment Count: {video.metrics.comment_count}")
        print(f"Danmaku Count: {video.metrics.danmaku_count}")
        print(f"Share Count: {video.metrics.share_count}")
        print(f"Favorite Count: {video.metrics.favorite_count}")
        print(f"Coin Count: {video.metrics.coin_count}")
        print(f"Creator: {video.creator_name} (mid: {video.creator_id})")
        print(f"Publish Time: {video.publish_time}")

        result = True
    else:
        print("Failed to get video detail")
        result = False

    return video


async def get_creator_info():
    """测试获取创作者信息"""
    print("\n" + "=" * 50)
    print("Testing Bilibili Creator Info")
    print("=" * 50)

    creator = await adapter.get_creator_info('168598')

    if creator:
        print(f"\nName: {creator.name}")
        print(f"Creator ID: {creator.creator_id}")
        print(f"Avatar: {creator.avatar_url}")
        print(f"Description: {creator.description}")
        print(f"Follower Count: {creator.follower_count}")
        print(f"Video Count: {creator.video_count}")
        result = True
    else:
        print("Failed to get creator info")
        result = False

    return result

async def get_creator_info_id(creator_id):
    """测试获取创作者信息"""
    print("\n" + "=" * 50)
    print("Testing Bilibili Creator Info")
    print("=" * 50)

    creator = await adapter.get_creator_info(creator_id)

    if creator:
        print(f"\nName: {creator.name}")
        print(f"Creator ID: {creator.creator_id}")
        print(f"Avatar: {creator.avatar_url}")
        print(f"Description: {creator.description}")
        print(f"Follower Count: {creator.follower_count}")
        print(f"Video Count: {creator.video_count}")
        result = True
    else:
        print("Failed to get creator info")
        result = False

    return creator

async def get_creator_videos():
    """测试获取创作者视频列表"""
    print("\n" + "=" * 50)
    print("Testing Bilibili Creator Videos")
    print("=" * 50)

    # 获取碧诗的视频列表
    videos = await adapter.get_creator_videos(creator_id='168598',pn=2463, limit=1)

    print(f"\nFetched {len(videos)} videos from creator")
    print("\n--- Sample Data ---")
    for video in videos[-3:]:
        print(f"\nTitle: {video.title}")
        print(f"BVID: {video.video_id}")
        print(f"Play Count: {video.metrics.play_count}")
        print(f"Publish Time: {video.publish_time}")

    result = len(videos) > 0

    return result


async def get_comments():
    """测试获取视频评论"""
    print("\n" + "=" * 50)
    print("Testing Bilibili Video Comments")
    print("=" * 50)

    # 获取视频评论
    comments = await adapter.get_comments('BV1Zf4y1W7BS', limit=5)

    print(f"\nFetched {len(comments)} comments")
    print("\n--- Sample Data ---")
    for comment in comments[:3]:
        print(f"\nUser: {comment.get('uname')}")
        print(f"Content: {comment.get('content', '')[:50]}...")
        print(f"Likes: {comment.get('like')}")

    result = len(comments) > 0

    return result

async def scan_bilibili_hot_with_creator():
    """测试B站热搜/排行榜采集"""
    print("=" * 50)
    print("Testing Bilibili Hot/Ranking Scan")
    print("=" * 50)

    # 测试全站排行榜
    hot_videos = await adapter.get_trending_videos(limit=10)

    print(f"\nFetched {len(hot_videos)} trending videos from Bilibili")
    print("\n--- Sample Data ---")
    for video in hot_videos:
        creator = await get_creator_info_id(video.creator_id)
        result = await viral_detector.detect(video, creator)
        time.sleep(3)
        print(f"\nTitle: {video.title}")
        print(f"BVID: {video.video_id}")
        print(f"Play Count: {video.metrics.play_count}")
        print(f"Like Count: {video.metrics.like_count}")
        print(f"Danmaku Count: {video.metrics.danmaku_count}")
        print(f"Engagement Rate: {video.metrics.engagement_rate:.4f}")

    return hot_videos

async def scan_bilibili_regions():
    """测试B站热搜/排行榜采集"""
    print("=" * 50)
    print("Testing Bilibili Hot/Ranking Scan")
    print("=" * 50)

    # 测试全站排行榜
    hot_videos = await adapter.get_region_videos(1)

    print(f"\nFetched {len(hot_videos)} trending videos from Bilibili")
    print("\n--- Sample Data ---")
    # for video in hot_videos:
    #     creator = await get_creator_info_id(video.creator_id)
    #     time.sleep(3)
    #     print(f"\nTitle: {video.title}")
    #     print(f"BVID: {video.video_id}")
    #     print(f"Play Count: {video.metrics.play_count}")
    #     print(f"Like Count: {video.metrics.like_count}")
    #     print(f"Danmaku Count: {video.metrics.danmaku_count}")
    #     print(f"Engagement Rate: {video.metrics.engagement_rate:.4f}")

    return hot_videos

async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("BILIBILI COLLECTOR TEST SUITE")
    print("=" * 60)

    results = {}

    # 1. 测试全站排行榜
    # try:
    #     # results['hot_scan'] = await scan_bilibili_hot()
    #     results['hot_scan'] = await scan_bilibili_hot_with_creator()
    # except Exception as e:
    #     print(f"ERROR in hot_scan: {e}")
    #     results['hot_scan'] = []

    # # 2. 测试分区排行榜
    # try:
    #     results['category_scan'] = await scan_bilibili_category()
    # except Exception as e:
    #     print(f"ERROR in category_scan: {e}")
    #     results['category_scan'] = 0
    #
    # # 3. 测试关键词搜索
    # try:
    #     results['search'] = await search_videos()
    # except Exception as e:
    #     print(f"ERROR in search: {e}")
    #     results['search'] = 0
    #
    # # 4. 测试视频详情
    try:
        results['detail'] = await get_video_detail()
    except Exception as e:
        print(f"ERROR in detail: {e}")
        results['detail'] = False
    video = results['detail']

    # 5. 测试创作者信息
    try:
        results['creator'] = await get_creator_info_id(video.creator_id)
    except Exception as e:
        print(f"ERROR in creator: {e}")
        results['creator'] = False
    creator = results['creator']

    result = await scan_bilibili_regions()
    # # 6. 测试创作者视频列表
    # try:
    #     results['creator_videos'] = await get_creator_videos()
    # except Exception as e:
    #     print(f"ERROR in creator_videos: {e}")
    #     results['creator_videos'] = False

    # # 7. 测试评论获取
    # try:
    #     results['comments'] = await get_comments()
    # except Exception as e:
    #     print(f"ERROR in comments: {e}")
    #     results['comments'] = False
    print("````````````````````````````````````")
    print(result)

    # 汇总结果
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    for test, result in results.items():
        status = "PASS" if (isinstance(result, bool) and result) or (isinstance(result, int) and result > 0) else "FAIL"
        print(f"{test}: {status} - {result}")


if __name__ == "__main__":
    asyncio.run(main())
