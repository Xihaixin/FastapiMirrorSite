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
            year=2020,
            source_db="DemoDB",
            abstract="An introduction to machine learning concepts.",
            keywords="machine learning,introduction",
        ),
        models.Resource(
            title="Deep Learning in Practice",
            authors="Alice; Bob",
            year=2022,
            source_db="DemoDB",
            abstract="Practical deep learning techniques and case studies.",
            keywords="deep learning,case study",
        ),
        models.Resource(
            title="Data Mining for Academic Libraries",
            authors="Carol",
            year=2018,
            source_db="LibraryDB",
            abstract="Explores data mining methods in academic library systems.",
            keywords="data mining,library",
        ),
    ]

    db.add_all(samples)
    db.commit()

