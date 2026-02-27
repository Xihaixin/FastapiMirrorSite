from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import models


def get_resource(db: Session, resource_id: int) -> Optional[models.Resource]:
    return db.query(models.Resource).filter(models.Resource.id == resource_id).first()


def search_resources(
    db: Session,
    q: Optional[str],
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(models.Resource)

    if q:
        like_pattern = f"%{q}%"
        query = query.filter(
            or_(
                models.Resource.title.ilike(like_pattern),
                models.Resource.authors.ilike(like_pattern),
                models.Resource.abstract.ilike(like_pattern),
                models.Resource.keywords.ilike(like_pattern),
            )
        )

    return query.offset(skip).limit(limit).all()


def create_sample_data(db: Session) -> None:
    """Insert a few demo records if table is empty."""
    if db.query(models.Resource).first():
        return

    samples = [
        models.Resource(
            title="Machine Learning Basics",
            authors="Tom; Jerry",
            keywords="machine learning; introduction",
            publish_year=2020,
            publisher="Demo Press",
            isbn="9780000000001",
            language="en",
            page_count=320,
            cnl_class_no="TP181",
            abstract="An introduction to machine learning concepts.",
        ),
        models.Resource(
            title="Deep Learning in Practice",
            authors="Alice; Bob",
            keywords="deep learning; case study",
            publish_year=2022,
            publisher="Demo Press",
            isbn="9780000000002",
            language="en",
            page_count=420,
            cnl_class_no="TP181.1",
            abstract="Practical deep learning techniques and case studies.",
        ),
        models.Resource(
            title="Data Mining for Academic Libraries",
            authors="Carol",
            keywords="data mining; library",
            publish_year=2018,
            publisher="Library Press",
            isbn="9780000000003",
            language="en",
            page_count=250,
            cnl_class_no="G252.7",
            abstract="Explores data mining methods in academic library systems.",
        ),
    ]

    db.add_all(samples)
    db.commit()

