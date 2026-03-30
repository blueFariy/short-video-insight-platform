"""
Scheduler Service - Scheduled task management
从数据库加载任务配置，并通过 Celery 触发执行
"""
import asyncio
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime, timedelta
from datetime import timezone
from loguru import logger
import time


class ScheduledTask:
    """Scheduled task model"""

    def __init__(
            self,
            id: str,
            name: str,
            func: Callable,
            interval: int,  # seconds
            enabled: bool = True,
            last_run: Optional[datetime] = None,
            next_run: Optional[datetime] = None,
            celery_task_name: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.func = func
        self.interval = interval
        self.enabled = enabled
        self.last_run = last_run
        self.next_run = next_run
        self.celery_task_name = celery_task_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "interval": self.interval,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "celery_task_name": self.celery_task_name
        }


class SchedulerService:
    """Scheduler service for periodic tasks"""

    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._task_handle: Optional[asyncio.Task] = None
        self._db_tasks_cache: Dict[str, Any] = {}  # 缓存数据库任务配置

    async def _load_tasks_from_db(self) -> Dict[str, ScheduledTask]:
        """从数据库加载任务配置（只首次加载或任务配置变更时更新）"""
        tasks = {}
        try:
            from app.models import db_manager, ScheduledTask as DBTask
            from sqlalchemy import select

            db_manager.init_db()
            async with db_manager.get_session() as session:
                stmt = select(DBTask).where(DBTask.enabled == True)
                result = await session.execute(stmt)
                db_tasks = result.scalars().all()

                # 获取当前 UTC 时间用于比较
                now_utc = datetime.now(timezone.utc)

                for db_task in db_tasks:
                    # 处理 last_run 的时区问题
                    # 数据库返回的是带时区的 UTC 时间，我们需要转换为 naive datetime 进行计算
                    last_run = db_task.last_run
                    if last_run:
                        # 移除时区信息，转为 naive datetime 进行计算
                        if last_run.tzinfo is not None:
                            last_run = last_run.replace(tzinfo=None)

                    # 使用 naive datetime 作为缓存 key
                    cache_key = db_task.task_id
                    last_run_str = last_run.isoformat() if last_run else None
                    cached = self._db_tasks_cache.get(cache_key)

                    # 如果缓存存在且 last_run 相同，使用内存中的任务（保持 next_run 不变）
                    if cached and cached.get('last_run') == last_run_str:
                        existing_task = self.tasks.get(db_task.task_id)
                        if existing_task:
                            tasks[db_task.task_id] = existing_task
                            continue

                    # 使用 naive datetime 计算
                    now_naive = datetime.now()  # 本地时间 naive datetime
                    if last_run:
                        next_run = last_run + timedelta(seconds=db_task.interval_seconds)
                        # 如果下次执行时间已经过期，立即执行
                        if next_run < now_naive:
                            next_run = now_naive
                    else:
                        next_run = now_naive

                    # 内存中的任务对象使用 naive datetime
                    task = ScheduledTask(
                        id=db_task.task_id,
                        name=db_task.name,
                        func=None,
                        interval=db_task.interval_seconds,
                        enabled=db_task.enabled,
                        last_run=last_run,
                        next_run=next_run,
                        celery_task_name=db_task.celery_task_name
                    )
                    tasks[db_task.task_id] = task

                    # 更新缓存（使用 ISO 字符串）
                    self._db_tasks_cache[cache_key] = {
                        'last_run': last_run_str,
                        'interval_seconds': db_task.interval_seconds
                    }

                logger.info(f"Loaded {len(tasks)} tasks from database")

        except Exception as e:
            logger.error(f"Failed to load tasks from database: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return tasks

    async def add_task(
            self,
            task_id: str,
            name: str,
            func: Callable,
            interval: int,
            enabled: bool = True
    ) -> ScheduledTask:
        """Add a scheduled task"""
        task = ScheduledTask(
            id=task_id,
            name=name,
            func=func,
            interval=interval,
            enabled=enabled,
            next_run=datetime.now()
        )
        self.tasks[task_id] = task
        logger.info(f"Added scheduled task: {name} (interval: {interval}s)")
        return task

    async def remove_task(self, task_id: str) -> bool:
        """Remove a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    async def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        task = self.tasks.get(task_id)
        if task:
            task.enabled = True
            return True
        return False

    async def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        task = self.tasks.get(task_id)
        if task:
            task.enabled = False
            return True
        return False

    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    async def list_tasks(self) -> List[ScheduledTask]:
        """List all tasks"""
        return list(self.tasks.values())

    async def run_task_now(self, task_id: str) -> bool:
        """Manually run a task immediately"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        try:
            logger.info(f"Manually running task: {task.name}")
            if asyncio.iscoroutinefunction(task.func):
                await task.func()
            else:
                task.func()

            task.last_run = datetime.now()
            task.next_run = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Failed to run task {task.name}: {e}")
            return False

    async def _run_scheduler(self):
        """Main scheduler loop - 从数据库加载任务并通过 Celery 触发执行"""
        logger.info("Scheduler started")
        while self.running:
            try:
                # 使用本地 naive datetime
                now = datetime.now()

                # 从数据库加载所有启用的任务
                db_tasks = await self._load_tasks_from_db()
                self.tasks = db_tasks

                for task in self.tasks.values():
                    if not task.enabled:
                        continue

                    # 检查是否到执行时间
                    logger.info(f"Checking task {task.name}: next_run={task.next_run}, now={now}, enabled={task.enabled}")
                    if task.next_run and now >= task.next_run:
                        logger.info(f"Running scheduled task: {task.name}")
                        try:
                            # 通过 Celery 触发任务执行
                            await self._trigger_celery_task(task)

                            task.last_run = now
                            task.next_run = datetime.now() + timedelta(seconds=task.interval)
                        except Exception as e:
                            logger.error(f"Task {task.name} failed: {e}")
                            # 失败后仍按 interval 计算下次执行时间
                            task.next_run = datetime.now() + timedelta(seconds=task.interval)

                await asyncio.sleep(10)  # 每 10 秒检查一次

            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(10)

        logger.info("Scheduler stopped")

    async def _trigger_celery_task(self, task: ScheduledTask) -> None:
        """通过 Celery 触发任务执行"""
        if not task.celery_task_name:
            logger.warning(f"Task {task.name} has no celery_task_name, skipping")
            return

        try:
            from app.celery_app import celery_app

            # 发送任务到 Celery
            celery_app.send_task(task.celery_task_name, args=[], kwargs={})
            logger.info(f"Triggered Celery task: {task.celery_task_name}")

            # 更新数据库中的 last_run
            await self._update_task_last_run(task.id)

        except Exception as e:
            logger.error(f"Failed to trigger Celery task {task.celery_task_name}: {e}")
            raise

    async def _update_task_last_run(self, task_id: str) -> None:
        """更新数据库中任务的 last_run"""
        try:
            from app.models import db_manager, ScheduledTask as DBTask
            from sqlalchemy import update

            db_manager.init_db()
            # 使用本地 naive datetime
            now = datetime.now()

            async with db_manager.get_session() as session:
                stmt = (
                    update(DBTask)
                    .where(DBTask.task_id == task_id)
                    .values(last_run=now, next_run=now)
                )
                await session.execute(stmt)
                await session.commit()

            # 同时更新缓存
            self._db_tasks_cache[task_id] = {
                'last_run': now.isoformat(),
                'interval_seconds': self._db_tasks_cache.get(task_id, {}).get('interval_seconds', 3600)
            }

            logger.info(f"Updated last_run for task {task_id}")

        except Exception as e:
            logger.error(f"Failed to update last_run for task {task_id}: {e}")

    async def start(self):
        """Start the scheduler"""
        if not self.running:
            self.running = True
            self._task_handle = asyncio.create_task(self._run_scheduler())
            logger.info("Scheduler service started")

    async def stop(self):
        """Stop the scheduler"""
        if self.running:
            self.running = False
            if self._task_handle:
                self._task_handle.cancel()
                try:
                    await self._task_handle
                except asyncio.CancelledError:
                    pass
            logger.info("Scheduler service stopped")

    async def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "running": self.running,
            "total_tasks": len(self.tasks),
            "enabled_tasks": len([t for t in self.tasks.values() if t.enabled]),
            "tasks": [t.to_dict() for t in self.tasks.values()]
        }


# Demo task functions
async def demo_collect_task():
    """Demo collection task"""
    logger.info("Running demo collection task...")
    from app.services.collector_service import collector_service
    await collector_service.collect_all_active()


async def demo_cleanup_task():
    """Demo cleanup task"""
    logger.info("Running demo cleanup task...")


# Create scheduler instance
scheduler_service = SchedulerService()
