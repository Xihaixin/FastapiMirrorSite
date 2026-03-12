import os
import ipaddress
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import sys


def _resource_path(*paths: str) -> str:
    """Return the absolute path to a resource.

    When the application is running in a PyInstaller bundle (``sys.frozen`` is
    True), resources are extracted to ``sys._MEIPASS``.  Otherwise we resolve
    relative to the current module directory.  This helper lets us refer to
    ``frontend`` files without relying on the working directory.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, *paths)


from sqlalchemy.orm import Session

from . import crud, models, schemas
from . import seed_data_updated as seed_data
from .database import Base, engine, get_db


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        target_count = int(os.getenv("SEED_TARGET_COUNT", "500"))
        seed_data.seed_resources(db, target_count=target_count)
        yield
    finally:
        db.close()


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

