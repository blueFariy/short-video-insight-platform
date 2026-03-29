"""
Database Write Consumer - 数据库写入消费者
从RabbitMQ队列消费数据写入消息，批量写入数据库
"""
import json
import threading
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger

from app.core.config import settings


class DBWriteConsumer:
    """数据库写入消费者 - 批量消费消息并写入数据库"""

    def __init__(self, batch_size: int = 50, flush_interval: float = 2.0):
        """
        Args:
            batch_size: 批量写入大小
            flush_interval: 刷新间隔(秒)
        """
        self._running = False
        self._thread = None
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._message_buffer: List[Dict[str, Any]] = []

    def start(self):
        """启动消费者"""
        if self._running:
            logger.warning("DB write consumer already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()
        logger.info(f"DB write consumer started (batch_size={self._batch_size}, flush_interval={self._flush_interval}s)")

    def stop(self):
        """停止消费者"""
        self._running = False
        # 先刷出剩余消息
        self._flush_buffer()
        logger.info("DB write consumer stopped")

    def _consume_loop(self):
        """消费循环"""
        import time
        from app.core.rabbitmq import DBWriteConnection

        last_flush_time = time.time()

        while self._running:
            try:
                # 每次循环创建新的连接，避免使用已关闭的channel
                connection = DBWriteConnection()
                if not connection.connect():
                    logger.error("Failed to connect to RabbitMQ, retrying in 5s...")
                    time.sleep(5)
                    continue

                # 确保队列存在
                connection._channel.queue_declare(
                    queue=settings.RABBITMQ_DB_QUEUE,
                    durable=True
                )

                # 设置预取数量
                connection._channel.basic_qos(prefetch_count=self._batch_size)

                # 定义消息处理方法
                def on_message(channel, method, properties, body):
                    try:
                        message = json.loads(body)
                        self._message_buffer.append(message)

                        # 检查是否达到批量大小或超时
                        current_time = time.time()
                        if (len(self._message_buffer) >= self._batch_size or
                            current_time - last_flush_time >= self._flush_interval):
                            self._flush_buffer()
                            last_flush_time = current_time

                        # 确认消息
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        logger.error(f"Error processing DB write message: {e}")
                        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

                # 开始消费
                connection._channel.basic_consume(
                    queue=settings.RABBITMQ_DB_QUEUE,
                    on_message_callback=on_message,
                    auto_ack=False
                )

                logger.info(f"Starting to consume DB write messages from {settings.RABBITMQ_DB_QUEUE}")
                connection._channel.start_consuming()

            except Exception as e:
                logger.error(f"DB write consumer error: {e}")
                time.sleep(5)

    def _flush_buffer(self):
        """将缓冲区中的消息批量写入数据库"""
        if not self._message_buffer:
            return

        messages = self._message_buffer.copy()
        self._message_buffer.clear()

        if not messages:
            return

        # 按操作类型分组
        operations: Dict[str, List[dict]] = {}
        for msg in messages:
            op = msg.get("operation", "unknown")
            if op not in operations:
                operations[op] = []
            operations[op].append(msg.get("data", {}))

        logger.info(f"Flushing {len(messages)} messages to database")

        # 执行批量写入
        try:
            asyncio.run(self._write_to_database(operations))
            logger.info(f"Successfully wrote {len(messages)} records to database")
        except Exception as e:
            logger.error(f"Failed to write to database: {e}")
            # 重新放入缓冲区（这里简化处理，实际可能需要重试机制）

    async def _write_to_database(self, operations: Dict[str, List[dict]]):
        """执行数据库写入"""
        from app.models import db_manager
        from sqlalchemy import insert, update
        from app.models.models import Video, Creator

        db_manager.init_db()
        async with db_manager.get_session() as session:
            # 处理视频写入
            if "insert_video" in operations:
                videos = operations["insert_video"]
                for video_data in videos:
                    video = Video(
                        video_id=video_data.get("video_id"),
                        platform=video_data.get("platform"),
                        title=video_data.get("title"),
                        author=video_data.get("author"),
                        author_id=video_data.get("author_id"),
                        publish_time=video_data.get("publish_time"),
                        play_count=video_data.get("play_count", 0),
                        like_count=video_data.get("like_count", 0),
                        comment_count=video_data.get("comment_count", 0),
                        share_count=video_data.get("share_count", 0),
                        collect_count=video_data.get("collect_count", 0),
                        duration=video_data.get("duration"),
                        description=video_data.get("description"),
                        tags=video_data.get("tags"),
                        url=video_data.get("url"),
                        cover_url=video_data.get("cover_url"),
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(video)

            # 处理视频更新
            if "update_video" in operations:
                from app.models.models import Video
                for update_data in operations["update_video"]:
                    video_id = update_data.get("video_id")
                    if video_id:
                        from sqlalchemy import select
                        stmt = select(Video).where(Video.video_id == video_id)
                        result = await session.execute(stmt)
                        video = result.scalar_one_or_none()
                        if video:
                            for key, value in update_data.items():
                                if key != "video_id" and hasattr(video, key):
                                    setattr(video, key, value)
                            video.updated_at = datetime.now()

            # 处理创作者写入
            if "insert_creator" in operations:
                creators = operations["insert_creator"]
                for creator_data in creators:
                    creator = Creator(
                        creator_id=creator_data.get("creator_id"),
                        platform=creator_data.get("platform"),
                        name=creator_data.get("name"),
                        avatar=creator_data.get("avatar"),
                        description=creator_data.get("description"),
                        follower_count=creator_data.get("follower_count", 0),
                        following_count=creator_data.get("following_count", 0),
                        video_count=creator_data.get("video_count", 0),
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(creator)

            await session.commit()


# 全局消费者实例
_db_write_consumer: DBWriteConsumer = None


def get_db_write_consumer() -> DBWriteConsumer:
    """获取数据库写入消费者实例"""
    global _db_write_consumer
    if _db_write_consumer is None:
        _db_write_consumer = DBWriteConsumer(batch_size=50, flush_interval=2.0)
    return _db_write_consumer


def start_db_write_consumer():
    """启动数据库写入消费者"""
    consumer = get_db_write_consumer()
    consumer.start()


def stop_db_write_consumer():
    """停止数据库写入消费者"""
    consumer = get_db_write_consumer()
    consumer.stop()