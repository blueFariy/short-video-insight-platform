"""
Security Module - Token 验证
从 user-service 复制的 token 解码逻辑
"""
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings


ALGORITHM = "HS256"


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码 JWT token

    Args:
        token: JWT token 字符串

    Returns:
        解码后的 payload 或 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    创建 JWT token

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt