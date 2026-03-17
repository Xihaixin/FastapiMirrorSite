import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 打包后（PyInstaller）将数据库放在可执行文件所在目录的 db 下；否则使用当前目录
if getattr(sys, "frozen", False):
    _base_dir = os.path.dirname(sys.executable)
else:
    _base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_db_path = os.path.join(_base_dir, "db", "app.db")
# SQLAlchemy SQLite URL 需要正斜杠（Windows 下 os.path 可能为反斜杠）
SQLALCHEMY_DATABASE_URL = "sqlite:///" + _db_path.replace("\\", "/")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

