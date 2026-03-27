"""
Scheduled Task API - 定时任务管理接口
"""
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

from app.services.scheduled_task_service import get_scheduled_task_service

router = APIRouter(tags=["定时任务管理"])


# Pydantic schemas
class ScheduledTaskCreate(BaseModel):
    """创建定时任务请求"""
    task_id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    celery_task_name: str = Field(..., description="Celery任务名")
    interval_seconds: int = Field(..., description="触发间隔(秒)", ge=60)
    description: Optional[str] = Field(None, description="任务描述")
    task_params: Optional[dict] = Field(None, description="任务参数")
    enabled: bool = Field(True, description="是否启用")


class ScheduledTaskUpdate(BaseModel):
    """更新定时任务请求"""
    name: Optional[str] = Field(None, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    celery_task_name: Optional[str] = Field(None, description="Celery任务名")
    interval_seconds: Optional[int] = Field(None, description="触发间隔(秒)", ge=60)
    task_params: Optional[dict] = Field(None, description="任务参数")
    enabled: Optional[bool] = Field(None, description="是否启用")


@router.get("/tasks", summary="获取定时任务列表")
async def get_scheduled_tasks(
    enabled: Optional[bool] = Query(None, description="按启用状态筛选")
):
    """
    获取所有定时任务列表
    """
    service = get_scheduled_task_service()
    tasks = await service.list_tasks(enabled=enabled)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [task.to_dict() for task in tasks],
            "total": len(tasks)
        }
    }


@router.get("/tasks/definitions", summary="获取可用任务定义")
async def get_task_definitions():
    """
    获取可用的Celery任务定义列表
    """
    service = get_scheduled_task_service()
    definitions = await service.get_task_definitions()

    return {
        "code": 200,
        "message": "success",
        "data": definitions
    }


@router.get("/tasks/{task_id}", summary="获取定时任务详情")
async def get_scheduled_task(task_id: str):
    """
    获取指定定时任务详情
    """
    service = get_scheduled_task_service()
    task = await service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    return {
        "code": 200,
        "message": "success",
        "data": task.to_dict()
    }


@router.post("/tasks", summary="创建定时任务")
async def create_scheduled_task(task: ScheduledTaskCreate):
    """
    创建新的定时任务
    """
    service = get_scheduled_task_service()

    try:
        created_task = await service.create_task(
            task_id=task.task_id,
            name=task.name,
            celery_task_name=task.celery_task_name,
            interval_seconds=task.interval_seconds,
            description=task.description or "",
            task_params=task.task_params,
            enabled=task.enabled
        )

        return {
            "code": 200,
            "message": "success",
            "data": created_task.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put("/tasks/{task_id}", summary="更新定时任务")
async def update_scheduled_task(task_id: str, task: ScheduledTaskUpdate):
    """
    更新定时任务配置
    """
    service = get_scheduled_task_service()

    updated_task = await service.update_task(
        task_id=task_id,
        name=task.name,
        description=task.description,
        celery_task_name=task.celery_task_name,
        interval_seconds=task.interval_seconds,
        task_params=task.task_params,
        enabled=task.enabled
    )

    if not updated_task:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    return {
        "code": 200,
        "message": "success",
        "data": updated_task.to_dict()
    }


@router.delete("/tasks/{task_id}", summary="删除定时任务")
async def delete_scheduled_task(task_id: str):
    """
    删除定时任务
    """
    service = get_scheduled_task_service()

    success = await service.delete_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    return {
        "code": 200,
        "message": "success"
    }


@router.post("/tasks/{task_id}/enable", summary="启用定时任务")
async def enable_scheduled_task(task_id: str):
    """
    启用指定定时任务
    """
    service = get_scheduled_task_service()

    success = await service.enable_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    return {
        "code": 200,
        "message": "success"
    }


@router.post("/tasks/{task_id}/disable", summary="禁用定时任务")
async def disable_scheduled_task(task_id: str):
    """
    禁用指定定时任务
    """
    service = get_scheduled_task_service()

    success = await service.disable_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    return {
        "code": 200,
        "message": "success"
    }


@router.post("/tasks/{task_id}/trigger", summary="手动触发定时任务")
async def trigger_scheduled_task(task_id: str):
    """
    手动触发定时任务执行一次
    """
    service = get_scheduled_task_service()

    success = await service.trigger_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="定时任务不存在或触发失败")

    return {
        "code": 200,
        "message": "success"
    }