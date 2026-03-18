"""
User Service
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from app.core.exceptions import (
    ValidationException,
    UnauthorizedException,
    NotFoundException,
    ConflictException
)
from app.core.config import settings


# 订阅等级配置
SUBSCRIPTION_TIERS = {
    "free": {
        "name": "免费版",
        "features": [
            "每日分析3个视频",
            "查看基础数据",
            "5个收藏夹",
            "基础报告"
        ],
        "limits": {
            "daily_analysis": 3,
            "collections": 5
        }
    },
    "basic": {
        "name": "基础版",
        "features": [
            "每日分析20个视频",
            "查看详细数据",
            "50个收藏夹",
            "高级报告",
            "竞品监控"
        ],
        "limits": {
            "daily_analysis": 20,
            "collections": 50
        }
    },
    "pro": {
        "name": "专业版",
        "features": [
            "每日分析100个视频",
            "完整数据访问",
            "无限收藏夹",
            "AI洞察",
            "趋势报告",
            "优先支持"
        ],
        "limits": {
            "daily_analysis": 100,
            "collections": -1  # unlimited
        }
    },
    "enterprise": {
        "name": "企业版",
        "features": [
            "无限分析",
            "完整数据访问",
            "无限收藏夹",
            "AI洞察",
            "定制报告",
            "专属客服",
            "API访问"
        ],
        "limits": {
            "daily_analysis": -1,
            "collections": -1
        }
    }
}


class UserService:
    """用户服务"""

    @staticmethod
    async def register(
        db: AsyncSession,
        username: str,
        email: str,
        password: str
    ) -> User:
        """
        用户注册

        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱
            password: 密码

        Returns:
            用户对象

        Raises:
            ConflictException: 用户名或邮箱已存在
        """
        # 检查用户名是否存在
        result = await db.execute(
            select(User).where(User.username == username)
        )
        if result.scalar_one_or_none():
            raise ConflictException(message="Username already exists")

        # 检查邮箱是否存在
        result = await db.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            raise ConflictException(message="Email already exists")

        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role="user",
            subscription_tier="free"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"New user registered: {username}")
        return user

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        username: str,
        password: str
    ) -> tuple[User, str]:
        """
        用户认证

        Args:
            db: 数据库会话
            username: 用户名
            password: 密码

        Returns:
            (用户对象, 访问令牌)

        Raises:
            UnauthorizedException: 用户名或密码错误
        """
        # 查找用户
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException(message="Invalid username or password")

        if not user.is_active:
            raise UnauthorizedException(message="Account is disabled")

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        await db.commit()

        # 生成令牌
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )

        logger.info(f"User logged in: {username}")
        return user, access_token

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
        company: Optional[str] = None,
        job_title: Optional[str] = None
    ) -> User:
        """更新用户信息"""
        # 检查邮箱是否被占用
        if email:
            result = await db.execute(
                select(User).where(
                    User.email == email,
                    User.id != user_id
                )
            )
            if result.scalar_one_or_none():
                raise ConflictException(message="Email already exists")

        # 更新用户
        update_data = {}
        if email is not None:
            update_data["email"] = email
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url
        if company is not None:
            update_data["company"] = company
        if job_title is not None:
            update_data["job_title"] = job_title

        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await db.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
            await db.commit()

        # 获取更新后的用户
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()
        logger.info(f"User updated: {user.username}")
        return user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """修改密码"""
        # 获取用户
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()

        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            raise UnauthorizedException(message="Invalid old password")

        # 更新密码
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        await db.commit()

        logger.info(f"User changed password: {user.username}")
        return True

    @staticmethod
    async def update_preferences(
        db: AsyncSession,
        user_id: int,
        preferences: dict
    ) -> User:
        """更新用户偏好设置"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()

        # 合并偏好设置
        current_prefs = user.preferences or {}
        current_prefs.update(preferences)
        user.preferences = current_prefs
        user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        logger.info(f"User preferences updated: {user.username}")
        return user

    @staticmethod
    async def get_subscription_info(user: User) -> dict:
        """获取订阅信息"""
        tier_info = SUBSCRIPTION_TIERS.get(user.subscription_tier, SUBSCRIPTION_TIERS["free"])

        return {
            "tier": user.subscription_tier,
            "tier_name": tier_info["name"],
            "features": tier_info["features"],
            "limits": tier_info["limits"],
            "expires_at": user.subscription_expires
        }

    @staticmethod
    async def upgrade_subscription(
        db: AsyncSession,
        user_id: int,
        tier: str
    ) -> User:
        """升级订阅"""
        if tier not in SUBSCRIPTION_TIERS:
            raise ValidationException(message=f"Invalid subscription tier: {tier}")

        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()

        user.subscription_tier = tier
        # 默认订阅30天
        user.subscription_expires = datetime.utcnow() + timedelta(days=30)
        user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        logger.info(f"User {user.username} upgraded to {tier}")
        return user


user_service = UserService()
