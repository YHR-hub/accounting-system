"""SQLAlchemy 数据层抽象。

通过环境变量 DATABASE_URL 在 SQLite（默认，指向现有 accounting.db）与
PostgreSQL 之间切换，例如：
    set DATABASE_URL=postgresql+psycopg://user:pwd@localhost/accounting

本模块为阶段2引入的并行数据层，不影响现有基于 sqlite3 的代码路径。
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .database import get_db_path


def get_database_url() -> str:
    """返回数据库连接串：优先取 DATABASE_URL，否则默认本地 SQLite。"""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    path = get_db_path().replace(os.sep, "/")
    return f"sqlite:///{path}"


class Base(DeclarativeBase):
    """所有 ORM 模型的声明基类。"""


def make_engine(url: str | None = None, echo: bool = False):
    """构建 SQLAlchemy Engine；SQLite 下自动开启外键约束。"""
    url = url or get_database_url()
    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(url, echo=echo, future=True, connect_args=connect_args)

    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _record):  # noqa: ANN001
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
