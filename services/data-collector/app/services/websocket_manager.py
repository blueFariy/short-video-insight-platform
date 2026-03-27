"""
WebSocket Manager - 用于实时推送预警消息
"""
from typing import Dict, List
from fastapi import WebSocket
from loguru import logger
import json


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 活跃的连接
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")

    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_viral_alert(self, alert_data: dict):
        """广播爆款预警消息"""
        message = {
            "type": "viral_alert",
            "data": alert_data
        }
        await self.broadcast(message)


# 全局连接管理器
manager = ConnectionManager()


async def get_websocket_manager() -> ConnectionManager:
    """获取WebSocket管理器实例"""
    return manager
