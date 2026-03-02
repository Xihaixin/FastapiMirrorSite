from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, conint


class ResourceBase(BaseModel):
    # 责任者（多位）（不为空）
    authors: str = Field(..., min_length=1, max_length=512)
    # 题名（不为空）
    title: str = Field(..., min_length=1, max_length=512)
    # 主题词
    keywords: Optional[str] = Field(None, max_length=512)
    # 出版日期（若仅存年份，用 publish_year）
    publish_date: Optional[date] = None
    # 出版年份
    publish_year: Optional[conint(ge=0, le=2100)] = None
    # 出版者（不为空）
    publisher: str = Field(..., min_length=1, max_length=256)
    # ISBN 号（不为空，长度限制为 10~20，用于 ISBN10/13 及带连字符形式）
    isbn: str = Field(..., min_length=10, max_length=20)
    # 语种
    language: Optional[str] = Field(None, max_length=32)
    # 总页数（正整数）
    page_count: Optional[conint(gt=0)] = None
    # 中图分类号
    cnl_class_no: Optional[str] = Field(None, max_length=64)
    # 摘要
    abstract: Optional[str] = None


class ResourceCreate(ResourceBase):
    pass


class ResourceOut(ResourceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CnlFacetNode(BaseModel):
    code: str
    name: str
    count: int
    children: List["CnlFacetNode"] = Field(default_factory=list)


class SearchFacets(BaseModel):
    cnl: List[CnlFacetNode] = Field(default_factory=list)
    search_points: List["FacetBucket"] = Field(default_factory=list)
    publish_years: List["FacetBucket"] = Field(default_factory=list)
    languages: List["FacetBucket"] = Field(default_factory=list)


class FacetBucket(BaseModel):
    key: str
    count: int


class ResourceSearchOut(BaseModel):
    items: List[ResourceOut]
    total: int
    page: int
    size: int
    facets: SearchFacets


CnlFacetNode.update_forward_refs()
SearchFacets.update_forward_refs()

