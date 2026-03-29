"""
User Interest Service - 用户兴趣匹配服务
根据用户关注的领域匹配爆款预警
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy import select, and_

from app.models import db_manager, UserInterest, Video, ViralAlert
from app.schemas import Video, VideoMetrics, ViralSignal


class UserInterestService:
    """用户兴趣匹配服务"""

    async def get_user_interest(self, user_id: int) -> Optional[UserInterest]:
        """获取用户兴趣配置"""
        async with db_manager.get_session() as session:
            stmt = select(UserInterest).where(
                UserInterest.user_id == user_id,
                UserInterest.is_active == True
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_or_update_interest(
        self,
        user_id: int,
        category_weights: Dict[str, float],
        interest_keywords: List[str] = None,
        platforms: List[str] = None,
        alert_levels: List[str] = None,
        notification_channels: List[str] = None
    ) -> UserInterest:
        """创建或更新用户兴趣配置"""
        async with db_manager.get_session() as session:
            # 查询是否已存在
            stmt = select(UserInterest).where(UserInterest.user_id == user_id)
            result = await session.execute(stmt)
            interest = result.scalar_one_or_none()

            if interest:
                # 更新
                interest.category_weights = category_weights
                if interest_keywords is not None:
                    interest.interest_keywords = interest_keywords
                if platforms is not None:
                    interest.platforms = platforms
                if alert_levels is not None:
                    interest.alert_levels = alert_levels
                if notification_channels is not None:
                    interest.notification_channels = notification_channels
                interest.updated_at = datetime.now()
            else:
                # 创建
                interest = UserInterest(
                    user_id=user_id,
                    category_weights=category_weights,
                    interest_keywords=interest_keywords or [],
                    platforms=platforms or ['douyin', 'bilibili', 'xiaohongshu'],
                    alert_levels=alert_levels or ['yellow', 'orange', 'red'],
                    notification_channels=notification_channels or ['app']
                )
                session.add(interest)

            await session.flush()
            logger.info(f"Updated user interest for user {user_id}")
            return interest

    async def match_users_for_video(
        self,
        video: Video,
        alert_level: str
    ) -> List[UserInterest]:
        """
        根据视频信息匹配感兴趣的用户

        Args:
            video: 视频信息
            alert_level: 预警级别

        Returns:
            匹配的用户兴趣列表
        """
        async with db_manager.get_session() as session:
            # 获取所有活跃用户
            stmt = select(UserInterest).where(UserInterest.is_active == True)
            result = await session.execute(stmt)
            all_interests = list(result.scalars().all())

            matched_users = []

            for interest in all_interests:
                # 1. 检查平台是否匹配
                if video.platform not in interest.platforms:
                    continue

                # 2. 检查预警级别是否在用户关注范围内
                if alert_level not in interest.alert_levels:
                    continue

                # 3. 检查视频类别是否在用户关注范围内
                if video.category:
                    category_weights = interest.category_weights or {}
                    if video.category in category_weights:
                        # 用户关注这个类别，匹配
                        matched_users.append(interest)
                else:
                    # 没有类别信息的视频，默认不匹配（避免过度推送）
                    pass

            logger.info(f"Matched {len(matched_users)} users for video {video.video_id} with alert level {alert_level}")
            return matched_users

    async def get_all_active_users(self) -> List[UserInterest]:
        """获取所有活跃用户"""
        async with db_manager.get_session() as session:
            stmt = select(UserInterest).where(UserInterest.is_active == True)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def ensure_default_interest(self, user_id: int) -> UserInterest:
        """确保用户有默认的兴趣配置"""
        interest = await self.get_user_interest(user_id)
        if not interest:
            # 创建默认配置：关注所有类别，接收所有级别预警
            interest = await self.create_or_update_interest(
                user_id=user_id,
                category_weights={
                    "美食": 0.8,
                    "美妆": 0.8,
                    "搞笑": 0.8,
                    "知识": 0.8,
                    "生活": 0.8
                },
                interest_keywords=[],
                platforms=['douyin', 'bilibili', 'xiaohongshu'],
                alert_levels=['yellow', 'orange', 'red'],
                notification_channels=['app']
            )
        return interest


class AlertRecordService:
    """预警记录服务"""

    async def save_alert(
        self,
        user_id: int,
        video: Video,
        signal: ViralSignal,
        alert_level: str
    ) -> ViralAlert:
        """保存预警记录"""
        async with db_manager.get_session() as session:
            alert = ViralAlert(
                user_id=user_id,
                video_id=video.video_id,
                platform=video.platform,
                title=video.title or "未知",
                cover_url=video.cover_url or "",
                video_url=video.url or "",
                alert_level=alert_level,
                message=signal.message,
                factors=signal.vs_benchmark.get('factors', []) if signal.vs_benchmark else []
            )
            session.add(alert)
            await session.flush()
            logger.info(f"Saved alert for user {user_id}, video {video.video_id}, level {alert_level}")
            return alert

    async def get_user_alerts(
        self,
        user_id: int,
        alert_level: Optional[str] = None,
        is_read: Optional[bool] = None,
        platform: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取用户的预警列表"""
        async with db_manager.get_session() as session:
            stmt = select(ViralAlert).where(ViralAlert.user_id == user_id)

            if alert_level:
                stmt = stmt.where(ViralAlert.alert_level == alert_level)
            if is_read is not None:
                stmt = stmt.where(ViralAlert.is_read == is_read)
            if platform:
                stmt = stmt.where(ViralAlert.platform == platform)
            if keyword:
                stmt = stmt.where(ViralAlert.title.ilike(f"%{keyword}%"))

            stmt = stmt.order_by(ViralAlert.created_at.desc())

            # 分页
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            result = await session.execute(stmt)
            alerts = list(result.scalars().all())

            # 获取总数
            count_stmt = select(ViralAlert).where(ViralAlert.user_id == user_id)
            if alert_level:
                count_stmt = count_stmt.where(ViralAlert.alert_level == alert_level)
            if is_read is not None:
                count_stmt = count_stmt.where(ViralAlert.is_read == is_read)
            if platform:
                count_stmt = count_stmt.where(ViralAlert.platform == platform)
            if keyword:
                count_stmt = count_stmt.where(ViralAlert.title.ilike(f"%{keyword}%"))

            total_result = await session.execute(count_stmt)
            total = len(list(total_result.scalars().all()))

            return {
                "items": [self._alert_to_dict(a) for a in alerts],
                "total": total,
                "page": page,
                "page_size": page_size
            }

    async def mark_as_read(self, alert_id: int, user_id: int) -> bool:
        """标记预警为已读"""
        async with db_manager.get_session() as session:
            stmt = select(ViralAlert).where(
                and_(
                    ViralAlert.id == alert_id,
                    ViralAlert.user_id == user_id
                )
            )
            result = await session.execute(stmt)
            alert = result.scalar_one_or_none()

            if alert:
                alert.is_read = True
                await session.flush()
                return True
            return False

    async def get_unread_count(self, user_id: int) -> int:
        """获取未读预警数量"""
        async with db_manager.get_session() as session:
            stmt = select(ViralAlert).where(
                and_(
                    ViralAlert.user_id == user_id,
                    ViralAlert.is_read == False
                )
            )
            result = await session.execute(stmt)
            return len(list(result.scalars().all()))

    def _alert_to_dict(self, alert: ViralAlert) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": alert.id,
            "video_id": alert.video_id,
            "platform": alert.platform,
            "title": alert.title,
            "cover_url": alert.cover_url,
            "video_url": alert.video_url,
            "alert_level": alert.alert_level,
            "message": alert.message,
            "factors": alert.factors,
            "is_read": alert.is_read,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        }


# Singleton instances
user_interest_service = UserInterestService()
alert_record_service = AlertRecordService()


def get_user_interest_service() -> UserInterestService:
    return user_interest_service


def get_alert_record_service() -> AlertRecordService:
    return alert_record_service