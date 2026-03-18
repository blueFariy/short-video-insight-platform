"""
User Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============ Request Schemas ============

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    company: Optional[str] = Field(None, max_length=100, description="公司")
    job_title: Optional[str] = Field(None, max_length=50, description="职位")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class UserPreferencesRequest(BaseModel):
    """用户偏好设置请求"""
    theme: Optional[str] = Field(None, description="主题")
    language: Optional[str] = Field(None, description="语言")
    notification_enabled: Optional[bool] = Field(None, description="通知开关")
    dashboard_layout: Optional[dict] = Field(None, description="仪表盘布局")
    default_analysis_options: Optional[dict] = Field(None, description="默认分析选项")


# ============ Response Schemas ============

class UserBaseResponse(BaseModel):
    """用户基本信息响应"""
    id: int
    username: str
    email: str
    avatar_url: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    role: str
    subscription_tier: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """用户完整信息响应"""
    id: int
    username: str
    email: str
    avatar_url: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    role: str
    preferences: Optional[dict] = None
    subscription_tier: str
    subscription_expires: Optional[datetime] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """用户列表响应"""
    id: int
    username: str
    email: str
    avatar_url: Optional[str] = None
    role: str
    subscription_tier: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserBaseResponse


class TokenRefreshResponse(BaseModel):
    """Token刷新响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ============ Subscription Schemas ============

class SubscriptionInfoResponse(BaseModel):
    """订阅信息响应"""
    tier: str
    expires_at: Optional[datetime] = None
    features: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class SubscriptionUpgradeRequest(BaseModel):
    """订阅升级请求"""
    tier: str = Field(..., description="订阅等级: free, basic, pro, enterprise")
    payment_method: Optional[str] = Field(None, description="支付方式")
