"""
Test script for Douyin collector tasks
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.adapters import get_platform_adapter
from app.adapters.douyin_adapter import  get_douyin_adapter
from app.services.cleaning_pipeline import cleaning_pipeline
from app.services.viral_detector import viral_detector

adapter = get_douyin_adapter(cookie="../../cookies/cookies_douyin.txt")

async def scan_douyin_hot():
    """测试抖音热搜采集"""
    print("=" * 50)
    print("Testing Douyin Hot Search Scan")
    print("=" * 50)

    hot_videos = await adapter.get_trending_videos(limit=10)

    print(f"\nFetched {len(hot_videos)} hot search items")
    print("\n--- Sample Data ---")
    for video in hot_videos[:3]:
        if video:
            print(f"\nTitle: {video.title}")
            print(f"Video ID: {video.video_id}")
            print(f"Hot Value: {video.metrics.play_count}")
            print(f"Viral Factors: {video.viral_factors}")

            # 清洗数据
            cleaned = cleaning_pipeline.process_video(video)
            if cleaned:
                print(f"Cleaned: OK, Quality Score: {cleaned.viral_factors.get('quality_score', 'N/A')}")

                # 爆款检测（viral_detector.detect 是异步方法）
                signal = await viral_detector.detect(cleaned)
                print(
                    f"Viral Signal - Stage: {signal.growth_stage}, Alert: {signal.should_alert}, Level: {signal.alert_level}")

    return len(hot_videos)


async def search_videos():
    """测试关键词搜索"""
    print("\n" + "=" * 50)
    print("Testing Douyin Video Search")
    print("=" * 50)

    videos = await adapter.search_videos(
        keyword="美食",
        limit=5,
        sort_by="hot",
        publish_time="week"
    )

    print(f"\nFound {len(videos)} videos for keyword: 美食")
    print("\n--- Sample Data ---")
    for video in videos[:3]:
        print(f"\nTitle: {video.title[:50]}...")
        print(f"Video ID: {video.video_id}")
        print(f"Creator: {video.creator_name}")
        print(f"Play Count: {video.metrics.play_count}")
        print(f"Like Count: {video.metrics.like_count}")
        print(f"Engagement Rate: {video.metrics.engagement_rate:.4f}")

    return len(videos)


async def get_video_detail():
    """测试获取视频详情"""
    print("\n" + "=" * 50)
    print("Testing Douyin Video Detail")
    print("=" * 50)

    # 先搜索一个视频获取ID
    video = await adapter.get_video_detail('7614451308724014370')
    if video:
        print(f"\nTitle: {video.title}")
        print(f"Play Count: {video.metrics.play_count}")
        print(f"Like Count: {video.metrics.like_count}")
        print(f"Comment Count: {video.metrics.comment_count}")
        print(f"Share Count: {video.metrics.share_count}")
        print(f"Creator: {video.creator_name}")
        return True


async def get_creator_info():
    """测试获取创作者信息"""
    print("\n" + "=" * 50)
    print("Testing Douyin Creator Info")
    print("=" * 50)

    # 先搜索视频获取创作者ID
    videos = await adapter.search_videos(keyword="美食", limit=1)

    if videos:
        sec_uid = videos[0].creator_id
        if sec_uid:
            print(f"\nFetching creator info for: {sec_uid}")
            creator = await adapter.get_creator_info(sec_uid)

            if creator:
                print(f"\nName: {creator.name}")
                print(f"Creator ID: {creator.creator_id}")
                print(f"Follower Count: {creator.follower_count}")
                print(f"Video Count: {creator.video_count}")
                return True

    print("No creator found")
    return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("DOUYIN COLLECTOR TEST SUITE")
    print("=" * 60)

    results = {}

    # 1. 测试热搜采集
    try:
        results['hot_scan'] = await scan_douyin_hot()
    except Exception as e:
        print(f"ERROR in hot_scan: {e}")
        results['hot_scan'] = 0

    # 2. 测试关键词搜索
    # try:
    #     results['search'] = await search_videos()
    # except Exception as e:
    #     print(f"ERROR in search: {e}")
    #     results['search'] = 0

    # 3. 测试视频详情
    try:
        results['detail'] = await get_video_detail()
    except Exception as e:
        print(f"ERROR in detail: {e}")
        results['detail'] = False

    # 4. 测试创作者信息
    try:
        results['creator'] = await get_creator_info()
    except Exception as e:
        print(f"ERROR in creator: {e}")
        results['creator'] = False

    # 汇总结果
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    for test, result in results.items():
        status = "PASS" if (isinstance(result, bool) and result) or (isinstance(result, int) and result > 0) else "FAIL"
        print(f"{test}: {status} - {result}")


if __name__ == "__main__":
    asyncio.run(main())
