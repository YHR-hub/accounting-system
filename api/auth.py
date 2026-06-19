"""API 鉴权：JWT 签发/校验与角色权限依赖。

口令沿用现有 SHA-256 方案；用户经 SQLAlchemy ORM 读取。
密钥经环境变量 JWT_SECRET 配置（生产环境务必设置）。
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from accsys.db import SessionLocal
from accsys.models import User

SECRET_KEY = os.environ.get("JWT_SECRET", "dev-secret-change-me-in-production-please-32b")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "480"))

bearer = HTTPBearer(auto_error=False)


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(username: str, password: str) -> Optional[dict]:
    """校验用户名/口令，成功返回用户信息字典，失败返回 None。"""
    db = SessionLocal()
    try:
        user = db.execute(
            select(User).where(User.username == username, User.is_active == 1)
        ).scalar_one_or_none()
    finally:
        db.close()
    if user and user.password_hash == _hash(password):
        return {"username": user.username, "role": user.role, "display_name": user.display_name}
    return None


def create_access_token(user: dict) -> str:
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "name": user["display_name"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> dict:
    if cred is None:
        raise HTTPException(status_code=401, detail="未提供认证令牌",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(cred.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="令牌无效或已过期",
                            headers={"WWW-Authenticate": "Bearer"})
    return {
        "username": payload.get("sub"),
        "role": payload.get("role"),
        "display_name": payload.get("name"),
    }


def require_roles(*roles: str):
    """返回一个依赖，要求当前用户角色在 roles 之内，否则 403。"""
    def dependency(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user
    return dependency
