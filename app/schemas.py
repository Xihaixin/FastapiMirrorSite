from typing import Optional

from pydantic import BaseModel


class ResourceBase(BaseModel):
    title: str
    authors: Optional[str] = None
    year: Optional[int] = None
    source_db: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[str] = None


class ResourceCreate(ResourceBase):
    pass


class ResourceOut(ResourceBase):
    id: int

    class Config:
        orm_mode = True

