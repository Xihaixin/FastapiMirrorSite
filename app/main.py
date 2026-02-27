from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        crud.create_sample_data(db)
        yield
    finally:
        db.close()


app = FastAPI(
    title="Mirror Site Demo",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="frontend",
)

# 兼容迁移：临时挂载 first_batch_mirror 的静态资源，便于复用页面素材（图片/CSS 等）
app.mount(
    "/mirror",
    StaticFiles(directory="first_batch_mirror/WebFile"),
    name="mirror",
)


@app.get("/", include_in_schema=False)
def read_index():
    return FileResponse("frontend/index.html")


@app.get("/resources/search", response_model=List[schemas.ResourceOut])
def search_resources(
    q: Optional[str] = Query(
        None, description="Keyword to search in title/abstract/keywords"
    ),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    resources = crud.search_resources(db, q=q, skip=skip, limit=size)
    return resources


@app.get("/resources/{resource_id}", response_model=schemas.ResourceOut)
def read_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = crud.get_resource(db, resource_id=resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

