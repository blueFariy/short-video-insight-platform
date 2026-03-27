"""
Scheduled Task Model - 定时任务数据库模型
"""
from sqlalchemy import String, Boolean, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.models import Base


class ScheduledTask(Base):
    """定时任务配置表"""
    __tablename__ = "scheduled_tasks"

    # 任务ID (唯一标识)
    task_id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # 任务名称
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 任务描述
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Celery任务名称 (格式: app.tasks.module.function)
    celery_task_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 任务参数 (JSON格式)
    task_params: Mapped[str] = mapped_column(Text, nullable=True)

    # 触发间隔 (秒)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=3600)

    # 是否启用
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 上次执行时间
    last_run: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 下次执行时间
    next_run: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "celery_task_name": self.celery_task_name,
            "task_params": self.task_params,
            "interval_seconds": self.interval_seconds,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }