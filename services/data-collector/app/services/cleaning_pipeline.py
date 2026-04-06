"""
Data Cleaning Pipeline
"""
from typing import Optional, List, Dict
from datetime import datetime
from loguru import logger

from app.schemas import Video


class DataCleaningPipeline:
    """数据清洗管道"""

    def __init__(self):
        self.quality_threshold = 0.5

    def process_video(self, video: Video) -> Optional[Video]:
        """
        处理每个采集到的视频

        Args:
            video: 原始视频数据

        Returns:
            清洗后的视频，如果质量过低则返回None
        """
        # 1. 基本验证
        if not self._basic_validation(video):
            logger.warning(f"Video {video.video_id} failed basic validation")
            return None

        # 2. 字段标准化
        video = self._standardize_fields(video)

        # 3. 异常值处理
        video = self._handle_outliers(video)

        # 4. 数据纯净度评分
        quality_score = self._calculate_quality(video)

        # 5. 只有达到质量阈值的才入库
        if quality_score < self.quality_threshold:
            logger.warning(
                f"Video {video.video_id} quality too low: {quality_score:.2f}"
            )
            return None

        # 添加质量分数到视频对象
        video.viral_factors['quality_score'] = quality_score

        return video

    def _basic_validation(self, video: Video) -> bool:
        """基本验证"""
        # 检查必要字段
        if not video.video_id:
            return False

        if not video.title or len(video.title.strip()) == 0:
            return False

        if not video.platform:
            return False

        # 检查指标是否为负数
        if video.metrics.play_count < 0:
            return False

        return True

    def _standardize_fields(self, video: Video) -> Video:
        """字段标准化"""
        # 标题清理
        if video.title:
            # 移除多余空白
            video.title = ' '.join(video.title.split())
            # 移除特殊字符
            video.title = video.title.strip()

        # 时长标准化（确保是秒）
        if video.duration < 0:
            video.duration = 0

        # 确保发布时间有效
        if video.publish_time and video.publish_time > datetime.now():
            # 如果发布时间是未来，设为当前时间
            video.publish_time = datetime.now()

        return video

    def _handle_outliers(self, video: Video) -> Video:
        """异常值处理"""
        metrics = video.metrics

        # 处理异常高的指标
        # 抖音单视频播放量上限约10亿
        if metrics.play_count > 1_000_000_000:
            logger.warning(f"Video {video.video_id}: Suspicious play count {metrics.play_count}")
            metrics.play_count = 1_000_000_000

        # 处理异常低或负数
        if metrics.like_count < 0:
            metrics.like_count = 0
        if metrics.comment_count < 0:
            metrics.comment_count = 0
        if metrics.share_count < 0:
            metrics.share_count = 0

        # 重新计算比率
        metrics.calculate_ratios()

        return video

    def _calculate_quality(self, video: Video) -> float:
        """
        计算数据纯净度

        Returns:
            质量分数 0-1
        """
        score = 1.0
        metrics = video.metrics

        # 1. 检查播放量
        if metrics.play_count < 100:
            return 0

        # 1. 检查点赞/播放比
        like_ratio = metrics.like_count / metrics.play_count
        if like_ratio > 0.2:  # 异常高
            logger.warning(f"Video {video.video_id}: Suspicious like ratio {like_ratio:.2%}")
            score *= 0.5
        elif like_ratio < 0.0001:  # 异常低但可能是新视频
            score *= 0.9

        # 2. 检查评论/播放比
        comment_ratio = metrics.comment_count / metrics.play_count

        if comment_ratio > 0.1:  # 评论率超过10%
            # 需要进一步检查评论内容
            # 这里简化处理
            score *= 0.7

        # 5. 平台特异性检查
        if video.platform == 'bilibili':
            # B站：硬币率检查
            if metrics.coin_ratio > 0.2:
                score *= 0.6

        elif video.platform == 'xiaohongshu':
            # 小红书：收藏/点赞比检查
            if metrics.collect_ratio > 1.0:
                score *= 0.5

        # 6. 数据完整性
        if not video.cover_url:
            score *= 0.9

        if not video.creator_name:
            score *= 0.8

        return max(0.1, min(1.0, score))

    def process_batch(self, videos: List[Video]) -> List[Video]:
        """
        批量处理视频

        Args:
            videos: 视频列表

        Returns:
            清洗后的视频列表
        """
        cleaned = []

        for video in videos:
            processed = self.process_video(video)
            if processed:
                cleaned.append(processed)

        logger.info(
            f"Batch cleaning completed. "
            f"Input: {len(videos)}, Output: {len(cleaned)}, "
            f"Dropped: {len(videos) - len(cleaned)}"
        )

        return cleaned


# Singleton instance
cleaning_pipeline = DataCleaningPipeline()


def get_cleaning_pipeline() -> DataCleaningPipeline:
    """Get cleaning pipeline instance"""
    return cleaning_pipeline
