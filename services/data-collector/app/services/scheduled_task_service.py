"""
Scheduled Task Service - 定时任务服务
管理数据库中的定时任务配置
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from app.models import db_manager, ScheduledTask


class ScheduledTaskService:
    """定时任务服务"""

    async def create_task(
        self,
        task_id: str,
        name: str,
        celery_task_name: str,
        interval_seconds: int,
        description: str = "",
        task_params: dict = None,
        enabled: bool = True
    ) -> ScheduledTask:
        """创建定时任务"""
        db_manager.init_db()

        async with db_manager.get_session() as session:
            # 检查是否已存在
            from sqlalchemy import select
            stmt = select(ScheduledTask).where(ScheduledTask.task_id == task_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                raise ValueError(f"Task {task_id} already exists")

            # 计算下次执行时间
            next_run = datetime.now() + timedelta(seconds=interval_seconds) if enabled else None

            task = ScheduledTask(
                task_id=task_id,
                name=name,
                description=description,
                celery_task_name=celery_task_name,
                task_params=json.dumps(task_params) if task_params else None,
                interval_seconds=interval_seconds,
                enabled=enabled,
                next_run=next_run,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)

            logger.info(f"Created scheduled task: {task_id}, interval: {interval_seconds}s")
            return task

    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取单个任务"""
        db_manager.init_db()

        async with db_manager.get_session() as session:
            from sqlalchemy import select
            stmt = select(ScheduledTask).where(ScheduledTask.task_id == task_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_tasks(self, enabled: Optional[bool] = None) -> List[ScheduledTask]:
        """获取所有任务"""
        db_manager.init_db()

        async with db_manager.get_session() as session:
            from sqlalchemy import select
            if enabled is not None:
                stmt = select(ScheduledTask).where(ScheduledTask.enabled == enabled)
            else:
                stmt = select(ScheduledTask)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        celery_task_name: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        task_params: Optional[dict] = None,
        enabled: Optional[bool] = None
    ) -> Optional[ScheduledTask]:
        """更新任务配置"""
        db_manager.init_db()

        async with db_manager.get_session() as session:
            from sqlalchemy import select
            stmt = select(ScheduledTask).where(ScheduledTask.task_id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                return None

            # 更新字段
            if name is not None:
                task.name = name
            if description is not None:
                task.description = description
            if celery_task_name is not None:
                task.celery_task_name = celery_task_name
            if interval_seconds is not None:
                task.interval_seconds = interval_seconds
            if task_params is not None:
                task.task_params = json.dumps(task_params)
            if enabled is not None:
                task.enabled = enabled

            # 更新下次执行时间
            if enabled and task.interval_seconds:
                task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
            elif not enabled:
                task.next_run = None

            task.updated_at = datetime.now()
            await session.commit()
            await session.refresh(task)

            logger.info(f"Updated scheduled task: {task_id}")
            return task

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        db_manager.init_db()

        async with db_manager.get_session() as session:
            from sqlalchemy import select, delete
            stmt = select(ScheduledTask).where(ScheduledTask.task_id == task_id)
            result = await session.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                return False

            await session.delete(task)
            await session.commit()

            logger.info(f"Deleted scheduled task: {task_id}")
            return True

    async def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        task = await self.update_task(task_id, enabled=True)
        return task is not None

    async def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        task = await self.update_task(task_id, enabled=False)
        return task is not None

    async def trigger_task(self, task_id: str) -> bool:
        """手动触发任务执行"""
        task = await self.get_task(task_id)
        if not task:
            return False

        try:
            # 导入celery app来触发任务
            from app.celery_app import celery_app

            # 解析任务参数
            params = json.loads(task.task_params) if task.task_params else {}

            # 触发Celery任务
            celery_app.send_task(task.celery_task_name, args=[], kwargs=params)

            # 更新最后执行时间
            await self.update_last_run(task_id)

            logger.info(f"Manually triggered task: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger task {task_id}: {e}")
            return False

    async def update_last_run(self, task_id: str) -> None:
        """更新任务最后执行时间"""
        task = await self.get_task(task_id)
        if not task:
            return

        db_manager.init_db()

        async with db_manager.get_session() as session:
            from sqlalchemy import select, update
            stmt = (
                update(ScheduledTask)
                .where(ScheduledTask.task_id == task_id)
                .values(
                    last_run=datetime.now(),
                    next_run=datetime.now() + timedelta(seconds=task.interval_seconds)
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_task_definitions(self) -> List[Dict[str, Any]]:
        """获取可用的任务定义列表"""
        # Celery任务映射表
        definitions = [
            {
                "celery_task_name": "app.tasks.viral_radar.scan_and_detect_viral",
                "name": "爆款雷达扫描",
                "description": "扫描新视频并检测爆款，每15分钟执行"
            },
            {
                "celery_task_name": "app.tasks.hot_scan.scan_all_platforms",
                "name": "全平台热点扫描",
                "description": "扫描各平台热点视频，每30分钟执行"
            },
            {
                "celery_task_name": "app.tasks.competitor_monitor.check_all_watchlists",
                "name": "竞品账号监控",
                "description": "监控竞品账号更新，每15分钟执行"
            },
            {
                "celery_task_name": "app.tasks.video_update.refresh_active_videos",
                "name": "活跃视频指标更新",
                "description": "更新最近24小时内视频指标，每5分钟执行"
            },
            {
                "celery_task_name": "app.tasks.report_generator.generate_daily",
                "name": "每日报告生成",
                "description": "生成每日分析报告，每天23:59执行"
            },
            {
                "celery_task_name": "app.tasks.maintenance.cleanup_old_data",
                "name": "数据清理任务",
                "description": "清理过期数据，每天凌晨3点执行"
            },
            {
                "celery_task_name": "app.tasks.douyin_collector.scan_douyin_hot",
                "name": "抖音热搜采集",
                "description": "采集抖音热搜榜单，每30分钟执行"
            },
            {
                "celery_task_name": "app.tasks.douyin_collector.collect_douyin_by_keywords",
                "name": "抖音关键词采集",
                "description": "按关键词采集视频，每小时执行"
            },
            {
                "celery_task_name": "app.tasks.viral_radar.collect_region_videos",
                "name": "B站分区视频采集",
                "description": "采集B站分区热门视频"
            }
        ]
        return definitions


# 全局实例
_scheduled_task_service = None


def get_scheduled_task_service() -> ScheduledTaskService:
    """获取定时任务服务实例"""
    global _scheduled_task_service
    if _scheduled_task_service is None:
        _scheduled_task_service = ScheduledTaskService()
    return _scheduled_task_service