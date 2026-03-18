"""
User Endpoints
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import (
    get_db,
    success_response,
    error_response,
    page_response,
    ResponseModel,
    NotFoundException,
    UnauthorizedException
)
from app.core.config import settings
from app.core.security import decode_access_token
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserUpdateRequest,
    ChangePasswordRequest,
    UserPreferencesRequest,
    UserResponse,
    UserBaseResponse,
    LoginResponse,
    SubscriptionInfoResponse,
    SubscriptionUpgradeRequest
)
from app.services.user_service import user_service


router = APIRouter(prefix="/users", tags=["用户管理"])

# OAuth2 依赖
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """获取当前用户ID"""
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(message="Invalid token payload")
    return int(user_id)


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """获取当前用户"""
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException(message="User not found")
    return user


# ============ 认证接口 ============

@router.post(
    "/register",
    response_model=ResponseModel[UserBaseResponse],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册"
)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册接口

    - **username**: 用户名 (3-50字符)
    - **email**: 邮箱
    - **password**: 密码 (至少6位)
    """
    user = await user_service.register(
        db,
        username=request.username,
        email=request.email,
        password=request.password
    )
    return success_response(
        data=UserBaseResponse.model_validate(user),
        message="User registered successfully"
    )


@router.post(
    "/login",
    response_model=ResponseModel[LoginResponse],
    summary="用户登录"
)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录接口

    - **username**: 用户名
    - **password**: 密码

    返回访问令牌，用于后续请求的认证
    """
    user, access_token = await user_service.authenticate(
        db,
        username=request.username,
        password=request.password
    )

    return success_response(
        data=LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserBaseResponse.model_validate(user)
        ),
        message="Login successful"
    )


# ============ 用户信息接口 ============

@router.get(
    "/me",
    response_model=ResponseModel[UserResponse],
    summary="获取当前用户信息"
)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    """获取当前登录用户的详细信息"""
    return success_response(data=current_user)


@router.put(
    "/me",
    response_model=ResponseModel[UserResponse],
    summary="更新当前用户信息"
)
async def update_current_user(
    request: UserUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户信息

    - **email**: 邮箱 (可选)
    - **avatar_url**: 头像URL (可选)
    - **company**: 公司 (可选)
    - **job_title**: 职位 (可选)
    """
    user = await user_service.update_user(
        db,
        user_id=current_user.id,
        email=request.email,
        avatar_url=request.avatar_url,
        company=request.company,
        job_title=request.job_title
    )
    return success_response(
        data=UserResponse.model_validate(user),
        message="User updated successfully"
    )


@router.post(
    "/me/change-password",
    response_model=ResponseModel,
    summary="修改密码"
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密码

    - **old_password**: 旧密码
    - **new_password**: 新密码 (至少6位)
    """
    await user_service.change_password(
        db,
        user_id=current_user.id,
        old_password=request.old_password,
        new_password=request.new_password
    )
    return success_response(message="Password changed successfully")


# ============ 偏好设置接口 ============

@router.get(
    "/me/preferences",
    response_model=ResponseModel[dict],
    summary="获取用户偏好设置"
)
async def get_preferences(
    current_user: UserResponse = Depends(get_current_user)
):
    """获取用户偏好设置"""
    return success_response(data=current_user.preferences or {})


@router.put(
    "/me/preferences",
    response_model=ResponseModel[UserResponse],
    summary="更新用户偏好设置"
)
async def update_preferences(
    request: UserPreferencesRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户偏好设置

    - **theme**: 主题 (light/dark)
    - **language**: 语言 (zh/en)
    - **notification_enabled**: 通知开关
    - **dashboard_layout**: 仪表盘布局
    - **default_analysis_options**: 默认分析选项
    """
    # 过滤掉None值
    prefs = request.model_dump(exclude_none=True)
    user = await user_service.update_preferences(db, current_user.id, prefs)
    return success_response(
        data=UserResponse.model_validate(user),
        message="Preferences updated successfully"
    )


# ============ 订阅管理接口 ============

@router.get(
    "/me/subscription",
    response_model=ResponseModel[SubscriptionInfoResponse],
    summary="获取订阅信息"
)
async def get_subscription(
    current_user: UserResponse = Depends(get_current_user)
):
    """获取当前用户的订阅信息"""
    info = await user_service.get_subscription_info(current_user)
    return success_response(
        data=SubscriptionInfoResponse(
            tier=info["tier"],
            expires_at=info["expires_at"],
            features=info["features"]
        )
    )


@router.post(
    "/me/subscription/upgrade",
    response_model=ResponseModel[UserResponse],
    summary="升级订阅"
)
async def upgrade_subscription(
    request: SubscriptionUpgradeRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    升级用户订阅

    - **tier**: 订阅等级 (free/basic/pro/enterprise)
    """
    user = await user_service.upgrade_subscription(
        db,
        user_id=current_user.id,
        tier=request.tier
    )
    return success_response(
        data=UserResponse.model_validate(user),
        message="Subscription upgraded successfully"
    )


# ============ 公共接口 ============

@router.get(
    "/{user_id}",
    response_model=ResponseModel[UserBaseResponse],
    summary="获取用户信息"
)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """根据ID获取用户公开信息"""
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException(message="User not found")
    return success_response(data=UserBaseResponse.model_validate(user))
