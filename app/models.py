from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    # 题名（必填）
    title = Column(String(512), index=True, nullable=False)
    # 责任者（多位，必填；以分号等分隔）
    authors = Column(String(512), index=True, nullable=False)
    # 主题词（可选，多个可用分号或逗号分隔）
    keywords = Column(String(512), nullable=True)
    # 出版日期（精确到日，若仅有年份则使用 publish_year）
    publish_date = Column(Date, nullable=True)
    # 出版年份（仅有年份时使用）
    publish_year = Column(Integer, nullable=True)
    # 出版者（必填）
    publisher = Column(String(256), nullable=False, index=True)
    # ISBN 号（必填、唯一）
    isbn = Column(String(32), nullable=False, unique=True, index=True)
    # 语种（如 "zh-CN"、"en"）
    language = Column(String(32), nullable=True, index=True)
    # 总页数（必须为正数）
    page_count = Column(Integer, nullable=True)
    # 中图分类号
    cnl_class_no = Column(String(64), nullable=True, index=True)
    # 摘要
    abstract = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "page_count IS NULL OR page_count > 0",
            name="ck_resources_page_count_positive",
        ),
    )

    class_mappings = relationship(
        "ResourceClassMap",
        back_populates="resource",
        cascade="all, delete-orphan",
    )


class CnlClass(Base):
    __tablename__ = "cnl_classes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    parent_id = Column(Integer, ForeignKey("cnl_classes.id"), nullable=True, index=True)
    level = Column(Integer, nullable=False, default=1)
    path = Column(String(256), nullable=True)

    parent = relationship("CnlClass", remote_side=[id], backref="children")
    resource_mappings = relationship(
        "ResourceClassMap",
        back_populates="cnl_class",
        cascade="all, delete-orphan",
    )


class ResourceClassMap(Base):
    __tablename__ = "resource_class_map"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("cnl_classes.id"), nullable=False, index=True)
    is_primary = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("resource_id", "class_id", name="uq_resource_class_map_unique"),
    )

    resource = relationship("Resource", back_populates="class_mappings")
    cnl_class = relationship("CnlClass", back_populates="resource_mappings")

