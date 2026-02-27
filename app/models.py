from sqlalchemy import CheckConstraint, Column, Date, Integer, String, Text

from .database import Base


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

