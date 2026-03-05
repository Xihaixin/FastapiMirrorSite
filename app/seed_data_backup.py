import argparse
import random
from collections import Counter
from typing import Dict, Optional

from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal, engine

# code, name, parent_code, level
CLASS_DEFS = [
    ("B", "哲学、宗教", None, 1),
    ("B0", "哲学理论", "B", 2),
    ("B5", "欧洲哲学", "B", 2),
    ("B81", "逻辑学（论理学）", "B", 2),
    ("B82", "伦理学（道德哲学）", "B", 2),
    ("B83", "美学", "B", 2),
    ("B84", "心理学", "B", 2),
    ("B9", "宗教", "B", 2),
    ("B99", "其它", "B", 2),
    ("C", "社会科学总论", None, 1),
    ("D", "政治、法律", None, 1),
    ("E", "军事", None, 1),
    ("F", "经济", None, 1),
    ("G", "文化、科学、教育、体育", None, 1),
    ("H", "语言、文字", None, 1),
    ("I", "文学", None, 1),
    ("J", "艺术", None, 1),
    ("K", "历史、地理", None, 1),
    ("N", "自然科学总论", None, 1),
    ("O", "数理科学和化学", None, 1),
    ("P", "天文学、地球科学", None, 1),
    ("Q", "生物科学", None, 1),
    ("R", "医药、卫生", None, 1),
    ("S", "农业科学", None, 1),
    ("T", "工业技术", None, 1),
    ("U", "交通运输", None, 1),
    ("V", "航空、航天", None, 1),
    ("X", "环境科学、安全科学", None, 1),
    ("Z", "综合性图书", None, 1),
]

# 类目分布权重，模拟真实站点“部分类目明显更大”
GEN_CLASS_WEIGHTS = {
    "B0": 5,
    "B5": 2,
    "B81": 1,
    "B82": 2,
    "B83": 2,
    "B84": 4,
    "B9": 3,
    "B99": 2,
    "C": 6,
    "D": 7,
    "E": 1,
    "F": 12,
    "G": 5,
    "H": 3,
    "I": 4,
    "J": 3,
    "K": 4,
    "N": 2,
    "O": 11,
    "P": 13,
    "Q": 4,
    "R": 16,
    "S": 2,
    "T": 8,
    "U": 1,
    "V": 1,
    "X": 3,
    "Z": 3,
}

GEN_CLASS_CODES = list(GEN_CLASS_WEIGHTS.keys())

SUBJECTS = [
    "machine learning",
    "economic policy",
    "applied statistics",
    "digital humanities",
    "political philosophy",
    "medical informatics",
    "environmental science",
    "world history",
    "advanced chemistry",
    "education technology",
    "public administration",
    "transportation systems",
    "aerospace engineering",
    "religion and society",
    "modern psychology",
]

NOUNS = [
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

FIRST_NAMES = [
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

LAST_NAMES = [
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

PUBLISHERS = [
    "Global Academic Press",
    "Northbridge Publishing",
    "Open Study Books",
    "Scholar House",
    "Campus Research Lab",
]

LANGUAGES = ["en", "en", "en", "en", "zh-CN", "fr", "de", None]


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

    for code, name, parent_code, level in CLASS_DEFS:
        _get_or_create_class(db, class_cache, code, name, parent_code, level)

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


def _weighted_class_code(rng: random.Random) -> str:
    total = sum(GEN_CLASS_WEIGHTS.values())
    pick = rng.randint(1, total)
    acc = 0
    for code, w in GEN_CLASS_WEIGHTS.items():
        acc += w
        if pick <= acc:
            return code
    return "F"


def _build_resource_row(seq: int, rng: random.Random, class_code: str) -> dict:
    subject = rng.choice(SUBJECTS)
    noun = rng.choice(NOUNS)
    title = f"{subject.title()} {noun.title()} Vol.{seq}"
    author1 = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    author2 = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    year = rng.randint(2010, 2025)
    isbn = str(9790000000000 + seq)

    return {
        "title": title,
        "authors": f"{author1}; {author2}",
        "keywords": f"{subject}; {noun}; academic; reference",
        "publish_year": year,
        "publisher": rng.choice(PUBLISHERS),
        "isbn": isbn,
        "language": rng.choice(LANGUAGES),
        "page_count": rng.randint(120, 980),
        "cnl_class_no": class_code,
        "abstract": f"This volume discusses {subject} with {noun} in higher education and research contexts.",
    }


def _create_one_resource(
    db: Session,
    existing_isbns: set,
    seq_start: int,
    rng: random.Random,
    forced_code: Optional[str] = None,
) -> int:
    seq = seq_start
    while True:
        code = forced_code or _weighted_class_code(rng)
        row = _build_resource_row(seq, rng, code)
        seq += 1
        if row["isbn"] in existing_isbns:
            continue
        existing_isbns.add(row["isbn"])
        db.add(models.Resource(**row))
        return seq


def seed_resources(
    db: Session,
    target_count: int = 500,
    seed: int = 20260304,
    min_per_class: int = 8,
) -> int:
    class_cache = ensure_class_tree(db)
    rng = random.Random(seed)

    existing_isbns = {x[0] for x in db.query(models.Resource.isbn).all()}
    seq = 1
    created = 0

    # 先保证类目覆盖：每个类至少 min_per_class 条
    class_counts = Counter(
        code for (code,) in db.query(models.Resource.cnl_class_no).filter(models.Resource.cnl_class_no.isnot(None)).all()
    )
    for code in GEN_CLASS_CODES:
        need = max(0, min_per_class - class_counts.get(code, 0))
        for _ in range(need):
            seq = _create_one_resource(db, existing_isbns, seq, rng, forced_code=code)
            created += 1

    db.flush()

    # 再补齐到目标总量
    current_count = db.query(models.Resource).count()
    need_total = max(0, target_count - current_count)
    for _ in range(need_total):
        seq = _create_one_resource(db, existing_isbns, seq, rng, forced_code=None)
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
    parser.add_argument("--min-per-class", type=int, default=8, help="Ensure minimum records per class.")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        created = seed_resources(
            db,
            target_count=args.count,
            min_per_class=args.min_per_class,
        )
        print(f"Seed complete. Newly created: {created}")
    finally:
        db.close()
