"""
RabbitMQ Connection Manager - RabbitMQ连接管理模块
提供RabbitMQ连接池和基本操作
"""
import pika
import json
from typing import Optional, Callable, Any
from loguru import logger

from app.core.config import settings


class RabbitMQConnection:
    """RabbitMQ连接管理器"""

    def __init__(self):
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.channel.Channel] = None

    def _get_connection_params(self) -> pika.ConnectionParameters:
        """获取RabbitMQ连接参数"""
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASSWORD
        )
        return pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            virtual_host=settings.RABBITMQ_VHOST,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )

    def connect(self) -> bool:
        """建立RabbitMQ连接"""
        try:
            if self._connection is None or self._connection.is_closed:
                self._connection = pika.BlockingConnection(
                    self._get_connection_params()
                )
                self._channel = self._connection.channel()
                # 声明队列
                self._channel.queue_declare(
                    queue=settings.RABBITMQ_QUEUE,
                    durable=True  # 队列持久化
                )
                logger.info(f"Connected to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    def close(self):
        """关闭连接"""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("RabbitMQ connection closed")

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connection is not None and not self._connection.is_closed

    def publish(
        self,
        message: dict,
        exchange: str = "",
        routing_key: str = "",
        delivery_mode: int = 2  # 持久化消息
    ) -> bool:
        """
        发布消息到队列

        Args:
            message: 消息内容(dict会自动转为JSON)
            exchange: 交换机名称
            routing_key: 路由键(使用队列名)
            delivery_mode: 投递模式(2=持久化)

        Returns:
            bool: 发布是否成功
        """
        try:
            if not self.is_connected():
                self.connect()

            # 确保队列存在
            self._channel.queue_declare(
                queue=settings.RABBITMQ_QUEUE,
                durable=True
            )

            # 序列化消息
            body = json.dumps(message, ensure_ascii=False)

            # 发布消息
            self._channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key or settings.RABBITMQ_QUEUE,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=delivery_mode,
                    content_type='application/json',
                )
            )
            logger.debug(f"Published message to {settings.RABBITMQ_QUEUE}: {message.get('task_name', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False

    def consume(
        self,
        callback: Callable[[dict], None],
        auto_ack: bool = False,
        prefetch_count: int = 1
    ):
        """
        消费队列消息

        Args:
            callback: 消息处理回调函数，接收dict参数
            auto_ack: 是否自动确认消息
            prefetch_count: 预取数量
        """
        if not self.is_connected():
            self.connect()

        # 设置预取数量
        self._channel.basic_qos(prefetch_count=prefetch_count)

        # 定义消息处理方法
        def on_message(channel, method, properties, body):
            try:
                message = json.loads(body)
                callback(message)
                # 确认消息
                if not auto_ack:
                    channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # 拒绝消息并重新入队
                if not auto_ack:
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        # 开始消费
        self._channel.basic_consume(
            queue=settings.RABBITMQ_QUEUE,
            on_message_callback=on_message,
            auto_ack=auto_ack
        )

        logger.info(f"Starting to consume messages from {settings.RABBITMQ_QUEUE}")
        self._channel.start_consuming()

    def stop_consuming(self):
        """停止消费"""
        if self._channel:
            self._channel.stop_consuming()


# 全局连接实例
_rabbitmq_connection: Optional[RabbitMQConnection] = None


def get_rabbitmq_connection() -> RabbitMQConnection:
    """获取RabbitMQ连接实例"""
    global _rabbitmq_connection
    if _rabbitmq_connection is None:
        _rabbitmq_connection = RabbitMQConnection()
    return _rabbitmq_connection


def publish_task_trigger(task_name: str, params: Optional[dict] = None) -> bool:
    """
    发布任务触发消息

    Args:
        task_name: Celery任务名
        params: 任务参数

    Returns:
        bool: 发布是否成功
    """
    message = {
        "task_name": task_name,
        "params": params or {},
        "timestamp": None  # 可以在消费者端添加时间戳
    }
    connection = get_rabbitmq_connection()
    return connection.publish(message)


def publish_db_write(operation: str, data: dict) -> bool:
    """
    发布数据库写入消息

    Args:
        operation: 操作类型 (insert_video, update_video, insert_creator等)
        data: 要写入的数据

    Returns:
        bool: 发布是否成功
    """
    message = {
        "operation": operation,
        "data": data,
        "timestamp": None
    }
    # 使用数据库写入专用连接
    connection = get_db_write_connection()
    return connection.publish_to_queue(message, settings.RABBITMQ_DB_QUEUE)


class DBWriteConnection(RabbitMQConnection):
    """数据库写入专用连接"""

    def connect(self) -> bool:
        """建立RabbitMQ连接"""
        try:
            if self._connection is None or self._connection.is_closed:
                self._connection = pika.BlockingConnection(
                    self._get_connection_params()
                )
                self._channel = self._connection.channel()
                # 声明数据库写入队列
                self._channel.queue_declare(
                    queue=settings.RABBITMQ_DB_QUEUE,
                    durable=True
                )
                logger.info(f"Connected to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    def publish_to_queue(
        self,
        message: dict,
        queue_name: str,
        exchange: str = "",
        routing_key: str = "",
        delivery_mode: int = 2
    ) -> bool:
        """发布消息到指定队列"""
        try:
            if not self.is_connected():
                self.connect()

            # 确保队列存在
            self._channel.queue_declare(
                queue=queue_name,
                durable=True
            )

            # 序列化消息
            body = json.dumps(message, ensure_ascii=False)

            # 发布消息
            self._channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key or queue_name,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=delivery_mode,
                    content_type='application/json',
                )
            )
            logger.debug(f"Published to {queue_name}: {message.get('operation', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish to {queue_name}: {e}")
            return False


# 数据库写入专用连接
_db_write_connection: Optional[DBWriteConnection] = None


def get_db_write_connection() -> DBWriteConnection:
    """获取数据库写入连接实例"""
    global _db_write_connection
    if _db_write_connection is None:
        _db_write_connection = DBWriteConnection()
    return _db_write_connection
