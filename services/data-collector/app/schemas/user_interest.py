from typing import List, Dict, Optional
from pydantic import BaseModel


class UserInterestUpdate(BaseModel):
    """用户兴趣更新请求"""
    category_weights: Dict[str, float] = {}
    interest_keywords: List[str] = []
    platforms: List[str] = ["douyin", "bilibili", "xiaohongshu"]
    alert_levels: List[str] = ["yellow", "orange", "red"]
    notification_channels: List[str] = ["app"]


class UserInterestResponse(BaseModel):
    """用户兴趣响应"""
    category_weights: Dict[str, float]
    interest_keywords: List[str]
    platforms: List[str]
    alert_levels: List[str]
    notification_channels: List[str]