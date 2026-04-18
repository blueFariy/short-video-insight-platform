"""
Viral Alert API - 预警查询接口
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body
from pydantic import BaseModel
from loguru import logger

from app.services.user_interest_service import get_alert_record_service, get_user_interest_service
from app.services.metric_snapshot_service import get_metric_snapshot_service
from app.core.security import decode_access_token
from app.adapters.api.bilibili_api import VIDEO_ZONES, VIDEO_MAIN_ZONES


router = APIRouter(tags=["爆款雷达"])


async def get_current_user_id(authorization: str = Header(None)) -> int:
    """从Authorization header获取当前用户ID"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # 提取token (Bearer <token>)
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return int(user_id)


class UserInterestUpdate(BaseModel):
    """用户兴趣更新请求"""
    category_weights: Dict[str, float] = {}
    interest_keywords: List[str] = []
    platforms: List[str] = ["douyin", "bilibili", "xiaohongshu"]
    alert_levels: List[str] = ["yellow", "orange", "red"]
    notification_channels: List[str] = ["app"]


@router.get("/alerts", summary="获取用户预警列表")
async def get_alerts(
    alert_level: Optional[str] = Query(None, description="预警级别筛选"),
    is_read: Optional[bool] = Query(None, description="已读状态筛选"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索(标题)"),
    categories: Optional[str] = Query(None, description="分类筛选列表(逗号分隔)"),
    start_time: Optional[str] = Query(None, description="开始时间筛选 (格式: YYYY-MM-DD)"),
    end_time: Optional[str] = Query(None, description="结束时间筛选 (格式: YYYY-MM-DD)"),
    sort_order: str = Query("asc", description="排序方式：asc最旧优先，desc最新优先"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user = Depends(get_current_user_id)
):
    """
    获取当前用户的预警列表
    """
    # 处理逗号分隔的分类字符串
    categories_list = None
    if categories:
        categories_list = [c.strip() for c in categories.split(',') if c.strip()]

    service = get_alert_record_service()
    result = await service.get_user_alerts(
        user_id=current_user,
        alert_level=alert_level,
        is_read=is_read,
        platform=platform,
        keyword=keyword,
        categories=categories_list,
        start_time=start_time,
        end_time=end_time,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    return {
        "code": 200,
        "message": "success",
        "data": result
    }


@router.get("/alerts/unread-count", summary="获取未读预警数量")
async def get_unread_count(
    current_user = Depends(get_current_user_id)
):
    """
    获取用户未读预警数量
    """
    service = get_alert_record_service()
    count = await service.get_unread_count(current_user)
    return {
        "code": 200,
        "message": "success",
        "data": {"count": count}
    }


@router.post("/alerts/{alert_id}/read", summary="标记预警为已读")
async def mark_alert_read(
    alert_id: int,
    current_user = Depends(get_current_user_id)
):
    """
    标记指定预警为已读
    """
    service = get_alert_record_service()
    success = await service.mark_as_read(alert_id, current_user)

    if not success:
        raise HTTPException(status_code=404, detail="预警记录不存在")

    return {
        "code": 200,
        "message": "success"
    }


@router.post("/alerts/read-all", summary="标记所有预警为已读")
async def mark_all_alerts_read(
    current_user = Depends(get_current_user_id)
):
    """
    标记所有预警为已读
    """
    service = get_alert_record_service()
    result = await service.get_user_alerts(
        user_id=current_user,
        is_read=False,
        page=1,
        page_size=1000
    )

    for alert in result.get("items", []):
        await service.mark_as_read(alert["id"], current_user)

    return {
        "code": 200,
        "message": "success",
        "data": {"marked_count": len(result.get("items", []))}
    }


@router.get("/alerts/{alert_id}", summary="获取预警详情")
async def get_alert_detail(
    alert_id: int,
    current_user = Depends(get_current_user_id)
):
    """
    获取预警详情
    """
    service = get_alert_record_service()
    result = await service.get_user_alerts(
        user_id=current_user,
        page=1,
        page_size=1
    )

    for alert in result.get("items", []):
        if alert["id"] == alert_id:
            return {
                "code": 200,
                "message": "success",
                "data": alert
            }

    raise HTTPException(status_code=404, detail="预警记录不存在")


@router.get("/user/interest", summary="获取用户兴趣配置")
async def get_user_interest(
    current_user = Depends(get_current_user_id)
):
    """
    获取当前用户的兴趣配置
    """
    service = get_user_interest_service()
    interest = await service.get_user_interest(current_user)

    if not interest:
        # 返回默认配置
        return {
            "code": 200,
            "message": "success",
            "data": {
                "category_weights": {
                    "美食": 0.8,
                    "美妆": 0.8,
                    "搞笑": 0.8,
                    "知识": 0.8,
                    "生活": 0.8
                },
                "interest_keywords": [],
                "platforms": ["douyin", "bilibili", "xiaohongshu"],
                "alert_levels": ["yellow", "orange", "red"],
                "notification_channels": ["app"]
            }
        }

    return {
        "code": 200,
        "message": "success",
        "data": {
            "category_weights": interest.category_weights,
            "interest_keywords": interest.interest_keywords,
            "platforms": interest.platforms,
            "alert_levels": interest.alert_levels,
            "notification_channels": interest.notification_channels
        }
    }


@router.post("/user/interest", summary="更新用户兴趣配置")
async def update_user_interest(
    interest_data: UserInterestUpdate = Body(...),
    current_user = Depends(get_current_user_id)
):
    """
    更新当前用户的兴趣配置
    """
    service = get_user_interest_service()
    interest = await service.create_or_update_interest(
        user_id=current_user,
        category_weights=interest_data.category_weights,
        interest_keywords=interest_data.interest_keywords,
        platforms=interest_data.platforms,
        alert_levels=interest_data.alert_levels,
        notification_channels=interest_data.notification_channels
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "category_weights": interest.category_weights,
            "interest_keywords": interest.interest_keywords,
            "platforms": interest.platforms,
            "alert_levels": interest.alert_levels,
            "notification_channels": interest.notification_channels
        }
    }


@router.get("/categories", summary="获取分类树")
async def get_categories():
    """
    获取分类树结构（主分类+子分类）
    """
    # 构建分类树
    category_tree = []
    for main_name, main_id in VIDEO_MAIN_ZONES.items():
        if main_id <= 0:  # 跳过全站和VLOG
            continue
        sub_categories = []
        if main_id in VIDEO_ZONES:
            for sub_name, sub_id in VIDEO_ZONES[main_id].items():
                sub_categories.append({
                    "label": sub_name,
                    "value": sub_name
                })
        category_tree.append({
            "label": main_name,
            "value": main_name,
            "children": sub_categories
        })

    return {
        "code": 200,
        "message": "success",
        "data": category_tree
    }
