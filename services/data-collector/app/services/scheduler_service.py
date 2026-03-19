"""
Scheduler Service - Scheduled task management
"""
import asyncio
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
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
        next_run: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.func = func
        self.interval = interval
        self.enabled = enabled
        self.last_run = last_run
        self.next_run = next_run

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "interval": self.interval,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None
        }


class SchedulerService:
    """Scheduler service for periodic tasks"""

    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._task_handle: Optional[asyncio.Task] = None

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
        """Main scheduler loop"""
        logger.info("Scheduler started")
        while self.running:
            try:
                now = datetime.now()

                for task in self.tasks.values():
                    if not task.enabled:
                        continue

                    # Check if it's time to run
                    if task.next_run and now >= task.next_run:
                        logger.info(f"Running scheduled task: {task.name}")
                        try:
                            if asyncio.iscoroutinefunction(task.func):
                                await task.func()
                            else:
                                task.func()

                            task.last_run = now
                            task.next_run = datetime.now()
                        except Exception as e:
                            logger.error(f"Task {task.name} failed: {e}")
                            task.next_run = datetime.now()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(10)

        logger.info("Scheduler stopped")

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
