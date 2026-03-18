"""
Redis Connection
"""
import json
from typing import Any, Optional, Union
from redis.asyncio import Redis, ConnectionPool
from loguru import logger

from app.core.config import settings


class RedisManager:
    """Redis管理器"""

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None

    async def init_redis(self, redis_url: Optional[str] = None) -> None:
        """初始化Redis连接"""
        url = redis_url or settings.REDIS_URL
        logger.info(f"Initializing Redis: {url}")

        # 创建连接池
        self._pool = ConnectionPool.from_url(
            url,
            max_connections=20,
            decode_responses=True
        )

        # 创建Redis客户端
        self._redis = Redis(connection_pool=self._pool)

        # 测试连接
        await self._redis.ping()
        logger.info("Redis connected successfully")

    async def close(self) -> None:
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis connection closed")

    # 基础操作
    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        return await self._redis.get(key)

    async def set(
        self,
        key: str,
        value: Union[str, int, float, bool],
        expire: Optional[int] = None
    ) -> bool:
        """设置值"""
        if expire:
            return await self._redis.setex(key, expire, value)
        return await self._redis.set(key, value)

    async def delete(self, key: str) -> int:
        """删除键"""
        return await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self._redis.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        return await self._redis.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        return await self._redis.ttl(key)

    # JSON操作
    async def get_json(self, key: str) -> Optional[Any]:
        """获取JSON值"""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """设置JSON值"""
        return await self.set(key, json.dumps(value), expire)

    # 哈希操作
    async def hget(self, key: str, field: str) -> Optional[str]:
        """获取哈希字段值"""
        return await self._redis.hget(key, field)

    async def hset(self, key: str, field: str, value: str) -> int:
        """设置哈希字段值"""
        return await self._redis.hset(key, field, value)

    async def hgetall(self, key: str) -> dict:
        """获取所有哈希字段"""
        return await self._redis.hgetall(key)

    async def hdel(self, key: str, *fields: str) -> int:
        """删除哈希字段"""
        return await self._redis.hdel(key, *fields)

    # 列表操作
    async def lpush(self, key: str, *values: str) -> int:
        """左侧入队"""
        return await self._redis.lpush(key, *values)

    async def rpush(self, key: str, *values: str) -> int:
        """右侧入队"""
        return await self._redis.rpush(key, *values)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """获取列表范围"""
        return await self._redis.lrange(key, start, end)

    # 集合操作
    async def sadd(self, key: str, *members: str) -> int:
        """添加集合成员"""
        return await self._redis.sadd(key, *members)

    async def smembers(self, key: str) -> set:
        """获取集合所有成员"""
        return await self._redis.smembers(key)

    async def sismember(self, key: str, member: str) -> bool:
        """检查是否为集合成员"""
        return await self._redis.sismember(key, member)

    # 自增操作
    async def incr(self, key: str, amount: int = 1) -> int:
        """自增"""
        return await self._redis.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """自减"""
        return await self._redis.decrby(key, amount)


# 全局Redis管理器实例
redis_manager = RedisManager()


# 依赖注入函数
async def get_redis() -> Redis:
    """FastAPI依赖注入 - 获取Redis客户端"""
    return redis_manager._redis
