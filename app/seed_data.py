import argparse
import random
from typing import Dict, Optional

from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal, engine

LEAF_CLASS_CODES = [
    "B01",
    "B83",
    "G252.7",
    "I106",
    "I712",
    "O13",
    "O151",
    "TP18",
    "TP181",
    "TP181.1",
    "TP391",
]


def _get_or_create_class(
    db: Session,
    class_cache: Dict[str, models.CnlClass],
    code: str,
    name: str,
    parent_code: Optional[str],
    level: int,
) -> models.CnlClass:
    if code in class_cache:
        return class_cache[code]
    parent = class_cache.get(parent_code) if parent_code else None
    item = db.query(models.CnlClass).filter(models.CnlClass.code == code).one_or_none()
    if not item:
        item = models.CnlClass(
            code=code,
            name=name,
            parent_id=parent.id if parent else None,
            level=level,
            path=code if not parent else f"{parent.path}/{code}",
        )
        db.add(item)
        db.flush()
    class_cache[code] = item
    return item


def ensure_class_tree(db: Session) -> Dict[str, models.CnlClass]:
    class_cache: Dict[str, models.CnlClass] = {}
    for row in db.query(models.CnlClass).all():
        class_cache[row.code] = row

    _get_or_create_class(db, class_cache, "B", "哲学、宗教", None, 1)
    _get_or_create_class(db, class_cache, "B0", "哲学理论", "B", 2)
    _get_or_create_class(db, class_cache, "B01", "哲学基本问题", "B0", 3)
    _get_or_create_class(db, class_cache, "B83", "美学", "B", 2)

    _get_or_create_class(db, class_cache, "G", "文化、科学、教育、体育", None, 1)
    _get_or_create_class(db, class_cache, "G25", "图书馆学、情报学", "G", 2)
    _get_or_create_class(db, class_cache, "G252", "情报学", "G25", 3)
    _get_or_create_class(db, class_cache, "G252.7", "信息检索", "G252", 4)

    _get_or_create_class(db, class_cache, "I", "文学", None, 1)
    _get_or_create_class(db, class_cache, "I1", "世界文学", "I", 2)
    _get_or_create_class(db, class_cache, "I106", "文学理论与批评", "I1", 3)
    _get_or_create_class(db, class_cache, "I712", "美国文学", "I1", 3)

    _get_or_create_class(db, class_cache, "O", "数理科学和化学", None, 1)
    _get_or_create_class(db, class_cache, "O1", "数学", "O", 2)
    _get_or_create_class(db, class_cache, "O13", "高等数学", "O1", 3)
    _get_or_create_class(db, class_cache, "O151", "概率论与数理统计", "O1", 3)

    _get_or_create_class(db, class_cache, "T", "工业技术", None, 1)
    _get_or_create_class(db, class_cache, "TP", "自动化技术、计算机技术", "T", 2)
    _get_or_create_class(db, class_cache, "TP18", "人工智能技术", "TP", 3)
    _get_or_create_class(db, class_cache, "TP181", "自动化基础理论", "TP18", 4)
    _get_or_create_class(db, class_cache, "TP181.1", "机器学习", "TP181", 5)
    _get_or_create_class(db, class_cache, "TP391", "计算机图形学", "TP", 3)

    db.flush()
    return class_cache


def _ensure_resource_class_mappings(
    db: Session,
    class_cache: Dict[str, models.CnlClass],
) -> None:
    resources = db.query(models.Resource).all()
    for resource in resources:
        if not resource.cnl_class_no:
            continue
        target = class_cache.get(resource.cnl_class_no)
        if not target:
            target = _get_or_create_class(
                db,
                class_cache,
                resource.cnl_class_no,
                resource.cnl_class_no,
                None,
                1,
            )
        exists = (
            db.query(models.ResourceClassMap)
            .filter(
                models.ResourceClassMap.resource_id == resource.id,
                models.ResourceClassMap.class_id == target.id,
            )
            .first()
        )
        if not exists:
            db.add(
                models.ResourceClassMap(
                    resource_id=resource.id,
                    class_id=target.id,
                    is_primary=1,
                )
            )


def _build_resource_row(index: int, rng: random.Random) -> dict:
    subject_pool = [
        "machine learning",
        "digital library",
        "information retrieval",
        "world literature",
        "probability",
        "computer graphics",
        "philosophy",
        "data mining",
        "ethics",
        "education technology",
    ]
    noun_pool = [
        "methods",
        "foundations",
        "applications",
        "practice",
        "analysis",
        "perspectives",
        "workbook",
        "handbook",
        "essentials",
        "approaches",
    ]
    first_names = [
        "Alice",
        "Bob",
        "Carol",
        "David",
        "Emily",
        "Frank",
        "Grace",
        "Helen",
        "Ian",
        "Julia",
        "Kevin",
        "Liam",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Brown",
        "Miller",
        "Davis",
        "Wilson",
        "Moore",
        "Taylor",
        "Anderson",
        "Thomas",
        "Jackson",
    ]
    publishers = [
        "Global Academic Press",
        "Northbridge Publishing",
        "Open Study Books",
        "Scholar House",
        "Campus Research Lab",
    ]
    languages = ["en", "en", "en", "en", "zh-CN", "fr", "de", None]

    subject = rng.choice(subject_pool)
    noun = rng.choice(noun_pool)
    title = f"{subject.title()} {noun.title()} Vol.{index}"
    author1 = f"{rng.choice(first_names)} {rng.choice(last_names)}"
    author2 = f"{rng.choice(first_names)} {rng.choice(last_names)}"
    year = rng.randint(2010, 2025)
    lang = rng.choice(languages)
    class_code = rng.choice(LEAF_CLASS_CODES)
    isbn = str(9790000000000 + index)
    keywords = f"{subject}; {noun}; academic; reference"

    return {
        "title": title,
        "authors": f"{author1}; {author2}",
        "keywords": keywords,
        "publish_year": year,
        "publisher": rng.choice(publishers),
        "isbn": isbn,
        "language": lang,
        "page_count": rng.randint(120, 980),
        "cnl_class_no": class_code,
        "abstract": f"This volume discusses {subject} with {noun} in higher education and research contexts.",
    }


def seed_resources(db: Session, target_count: int = 500, seed: int = 20260302) -> int:
    class_cache = ensure_class_tree(db)
    current_count = db.query(models.Resource).count()
    if current_count >= target_count:
        _ensure_resource_class_mappings(db, class_cache)
        db.commit()
        return 0

    rng = random.Random(seed)
    existing_isbns = {x[0] for x in db.query(models.Resource.isbn).all()}
    created = 0
    index = 1
    needed = target_count - current_count

    while created < needed:
        row = _build_resource_row(index, rng)
        index += 1
        if row["isbn"] in existing_isbns:
            continue
        existing_isbns.add(row["isbn"])
        db.add(models.Resource(**row))
        created += 1

    db.flush()
    _ensure_resource_class_mappings(db, class_cache)
    db.commit()
    return created


def seed_all(target_count: int = 500) -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        return seed_resources(db, target_count=target_count)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed resources into local database.")
    parser.add_argument("--count", type=int, default=500, help="Target total resource count.")
    args = parser.parse_args()
    created = seed_all(target_count=args.count)
    print(f"Seed complete. Newly created: {created}")
