from sqlalchemy import Column, Integer, String, Text

from .database import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), index=True, nullable=False)
    authors = Column(String(512), index=True, nullable=True)
    year = Column(Integer, nullable=True)
    source_db = Column(String(128), index=True, nullable=True)
    abstract = Column(Text, nullable=True)
    keywords = Column(String(512), nullable=True)

