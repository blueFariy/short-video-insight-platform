"""
RabbitMQ Task Consumer - RabbitMQ任务消费者
从RabbitMQ队列消费任务消息并转发给Celery执行
"""
import json
import threading
from datetime import datetime
from loguru import logger

from app.core.rabbitmq import get_rabbitmq_connection
from app.core.config import settings


class TaskConsumer:
    """任务消费者 - 从RabbitMQ消费消息并转发给Celery"""

    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        """在后台线程启动消费者"""
        if self._running:
            logger.warning("Task consumer already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()
        logger.info("Task consumer started in background")

    def stop(self):
        """停止消费者"""
        self._running = False
        connection = get_rabbitmq_connection()
        if connection.is_connected():
            connection.stop_consuming()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Task consumer stopped")

    def _consume_loop(self):
        """消费循环"""
        import time
        from app.core.rabbitmq import RabbitMQConnection

        while self._running:
            try:
                # 每次循环创建新的连接，避免使用已关闭的channel
                connection = RabbitMQConnection()
                if not connection.connect():
                    logger.error("Failed to connect to RabbitMQ, retrying in 5s...")
                    time.sleep(5)
                    continue

                # 使用阻塞方式消费消息
                connection.consume(
                    callback=self._handle_message,
                    auto_ack=False,
                    prefetch_count=1
                )

            except KeyboardInterrupt:
                logger.info("Consumer interrupted by user")
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                time.sleep(5)

    def _handle_message(self, message: dict):
        """
        处理接收到的消息，转发给Celery

        Args:
            message: 消息内容，包含 task_name 和 params
        """
        try:
            task_name = message.get("task_name")
            params = message.get("params", {})

            if not task_name:
                logger.warning("Received message without task_name")
                return

            # 转发给Celery
            from app.celery_app import celery_app

            celery_app.send_task(task_name, args=[], kwargs=params)
            logger.info(f"Forwarded task to Celery: {task_name}")

        except Exception as e:
            logger.error(f"Failed to forward task to Celery: {e}")


# 全局消费者实例
_task_consumer: TaskConsumer = None


def get_task_consumer() -> TaskConsumer:
    """获取任务消费者实例"""
    global _task_consumer
    if _task_consumer is None:
        _task_consumer = TaskConsumer()
    return _task_consumer


def start_task_consumer():
    """启动任务消费者"""
    consumer = get_task_consumer()
    consumer.start()


def stop_task_consumer():
    """停止任务消费者"""
    consumer = get_task_consumer()
    consumer.stop()
