import os
import uvicorn
import ipaddress
from typing import List, Optional
from contextlib import asynccontextmanager

from pathlib import Path
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import sys


# ========== 修复后的路径函数（支持多参数/多级路径） ==========
def _resource_path(*relative_parts) -> str:
    """
    获取资源文件/目录的绝对路径，适配 PyInstaller 打包后的环境
    :param relative_parts: 路径片段（可传多个，如 "frontend", "index.html"）
    :return: 拼接后的绝对路径字符串
    """
    # 1. 确定基础路径（开发/打包环境）
    if getattr(sys, "frozen", False):
        # 打包后：exe 所在目录（dist/main/）
        base_path = Path(sys._MEIPASS).parent
    else:
        # 开发环境：项目根目录（frontend 与 app 同级）
        base_path = Path(__file__).parent.parent  # 从 app/main.py 向上找根目录
    
    # 2. 拼接所有路径片段（支持多级，如 "frontend" + "index.html"）
    # *relative_parts 接收多个参数，自动拼接成完整路径
    full_path = base_path.joinpath(*relative_parts)
    
    # 3. 解析绝对路径并转为字符串（适配 FastAPI 接口要求）
    resolved_path = full_path.resolve()
    
    # 可选：打印路径调试（开发/打包时排查问题）
    print(f"📁 资源路径解析：{'/'.join(relative_parts)} → {resolved_path}")
    
    return str(resolved_path)


from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import engine, get_db


def _build_allowlist():
    """
    IP_ALLOWLIST 支持格式（逗号分隔）：
    - 单个 IP：192.168.10.31
    - 网段 CIDR：192.168.10.0/24
    留空表示不启用白名单（放行所有）。
    """
    raw = (os.getenv("IP_ALLOWLIST") or "").strip()
    if not raw:
        return []

    items = []
    for token in raw.split(","):
        t = token.strip()
        if not t:
            continue
        try:
            if "/" in t:
                items.append(ipaddress.ip_network(t, strict=False))
            else:
                items.append(ipaddress.ip_address(t))
        except ValueError:
            # 忽略非法配置项，避免启动失败
            continue
    return items


_ALLOWLIST = _build_allowlist()


def _ip_allowed(ip: str) -> bool:
    # 始终允许本机访问
    if ip in {"127.0.0.1", "::1"}:
        return True
    # 未配置白名单：不启用限制
    if not _ALLOWLIST:
        return True

    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False

    for item in _ALLOWLIST:
        if isinstance(item, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
            if ip_obj in item:
                return True
        else:
            if ip_obj == item:
                return True
    return False


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     Base.metadata.create_all(bind=engine)
#     db = next(get_db())
#     try:
#         target_count = int(os.getenv("SEED_TARGET_COUNT", "500"))
#         seed_data.seed_resources(db, target_count=target_count)
#         yield
#     finally:
#         db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ 应用启动中，开始初始化核心资源")
    
    try:
        # 同步引擎不能用 async with！改用普通 with
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))  # 同步执行，无警告
            row = result.scalar()
            if row != 1:
                raise RuntimeError("数据库连接测试失败")
        print("✅ 数据库连接正常")
    except OperationalError as e:
        print(f"❌ 数据库连接失败：{e}")
        raise e
    
    yield
    
    print("🔌 应用开始关闭，释放核心资源")
    engine.dispose()  # 关闭同步引擎
    print("🔌 所有资源已释放，应用正常关闭")


app = FastAPI(
    title="Mirror Site Demo",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def ip_allowlist_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else ""
    if not _ip_allowed(client_ip):
        return JSONResponse(
            status_code=403,
            content={"detail": "IP not allowed", "client_ip": client_ip},
        )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=_resource_path("frontend")),
    name="frontend",
)

app.mount(
    "/pdfs",
    StaticFiles(directory="pdfs"),
    name="pdfs",
)

app.mount(
    "/software",
    StaticFiles(directory="software"),
    name="software",
)


@app.get("/", include_in_schema=False)
def read_index():
    # use _resource_path to locate the index file inside the bundle
    return FileResponse(_resource_path("frontend", "index.html"))


@app.get("/resources/search", response_model=schemas.ResourceSearchOut)
def search_resources(
    q: Optional[str] = Query(
        None, description="Keyword to search in title/abstract/keywords"
    ),
    class_code: Optional[str] = Query(
        None, description="CNL class code prefix filter (e.g. TP, TP181)"
    ),
    search_point: Optional[str] = Query(
        None, description="Search hit field filter: title/authors/abstract"
    ),
    publish_year: Optional[int] = Query(
        None, description="Publish year facet filter"
    ),
    language: Optional[str] = Query(
        None, description="Language facet filter, e.g. en/zh-CN"
    ),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    result = crud.search_resources(
        db,
        q=q,
        skip=skip,
        limit=size,
        class_code=class_code,
        search_point=search_point,
        publish_year=publish_year,
        language=language,
    )
    result["page"] = page
    result["size"] = size
    return result


@app.get("/resources/home", response_model=List[schemas.ResourceOut])
def list_home_resources(
    size: int = Query(16, ge=1, le=60),
    db: Session = Depends(get_db),
):
    return crud.list_home_resources(db, limit=size)


@app.get("/resources/{resource_id}", response_model=schemas.ResourceOut)
def read_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = crud.get_resource(db, resource_id=resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

# ========== 修复启动逻辑（关键！直接传 app 实例） ==========
def main():
    """打包后/开发时的统一启动入口"""
    # 核心修改：不再用 "app.main:app" 字符串，直接传 app 实例
    uvicorn_config = uvicorn.Config(
        app=app,  # 直接传递 app 实例，绕开模块导入
        host="0.0.0.0",
        port=8000,
        reload=False,  # 打包后必须关闭 reload
        log_level="info",
    )
    server = uvicorn.Server(uvicorn_config)
    print("🚀 FastAPI 服务启动中：http://127.0.0.1:8000")
    server.run()

# ========== 程序入口（确保打包后能执行） ==========
if __name__ == "__main__":
    # 修复 Python 路径，确保内部模块能导入
    if getattr(sys, "frozen", False):
        # 把打包后的资源目录加入 Python 路径
        sys.path.insert(0, str(Path(sys._MEIPASS)))
    # 启动服务
    main()