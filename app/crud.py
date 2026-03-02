from typing import Dict, List, Optional

from sqlalchemy import Integer, func, or_
from sqlalchemy.orm import Query, Session

from . import models

SEARCH_POINT_FIELDS = {
    "title": models.Resource.title,
    "authors": models.Resource.authors,
    "abstract": models.Resource.abstract,
}


def get_resource(db: Session, resource_id: int) -> Optional[models.Resource]:
    return db.query(models.Resource).filter(models.Resource.id == resource_id).first()


def _apply_keyword_filter(query: Query, q: Optional[str]) -> Query:
    if not q:
        return query
    like_pattern = f"%{q}%"
    return query.filter(
        or_(
            models.Resource.title.ilike(like_pattern),
            models.Resource.authors.ilike(like_pattern),
            models.Resource.abstract.ilike(like_pattern),
            models.Resource.keywords.ilike(like_pattern),
        )
    )


def _build_resource_query(
    db: Session,
    q: Optional[str],
    class_code: Optional[str] = None,
    search_point: Optional[str] = None,
    publish_year: Optional[int] = None,
    language: Optional[str] = None,
) -> Query:
    query = db.query(models.Resource)

    if search_point and search_point in SEARCH_POINT_FIELDS and q:
        like_pattern = f"%{q}%"
        query = query.filter(SEARCH_POINT_FIELDS[search_point].ilike(like_pattern))
    else:
        query = _apply_keyword_filter(query, q)

    if class_code:
        query = (
            query.join(
                models.ResourceClassMap,
                models.ResourceClassMap.resource_id == models.Resource.id,
            )
            .join(
                models.CnlClass,
                models.CnlClass.id == models.ResourceClassMap.class_id,
            )
            .filter(models.CnlClass.code.like(f"{class_code}%"))
            .distinct()
        )

    if publish_year is not None:
        query = query.filter(
            or_(
                models.Resource.publish_year == publish_year,
                func.cast(func.strftime("%Y", models.Resource.publish_date), Integer)
                == publish_year,
            )
        )

    if language:
        normalized = language.strip()
        if normalized in {"其他", "other", "Other"}:
            query = query.filter(
                or_(models.Resource.language.is_(None), models.Resource.language == "")
            )
        else:
            query = query.filter(models.Resource.language == normalized)

    return query


def _build_facet_tree(
    db: Session,
    q: Optional[str],
    search_point: Optional[str],
    publish_year: Optional[int],
    language: Optional[str],
) -> List[Dict]:
    matched_ids_subq = _build_resource_query(
        db,
        q=q,
        class_code=None,
        search_point=search_point,
        publish_year=publish_year,
        language=language,
    ).with_entities(models.Resource.id).subquery()

    counted_rows = (
        db.query(
            models.ResourceClassMap.class_id.label("class_id"),
            func.count(models.ResourceClassMap.resource_id).label("count"),
        )
        .join(
            matched_ids_subq,
            matched_ids_subq.c.id == models.ResourceClassMap.resource_id,
        )
        .group_by(models.ResourceClassMap.class_id)
        .all()
    )
    leaf_counts = {row.class_id: row.count for row in counted_rows}

    classes = db.query(models.CnlClass).order_by(models.CnlClass.code.asc()).all()
    if not classes:
        return []

    class_by_id = {item.id: item for item in classes}
    children_map: Dict[Optional[int], List[models.CnlClass]] = {}
    for item in classes:
        children_map.setdefault(item.parent_id, []).append(item)

    aggregate_counts = {item.id: leaf_counts.get(item.id, 0) for item in classes}
    ordered_desc = sorted(classes, key=lambda x: (x.level, x.code), reverse=True)
    for item in ordered_desc:
        if item.parent_id and item.parent_id in aggregate_counts:
            aggregate_counts[item.parent_id] += aggregate_counts[item.id]

    def build_node(class_id: int) -> Optional[Dict]:
        item = class_by_id[class_id]
        total = aggregate_counts.get(item.id, 0)
        if total <= 0:
            return None
        children_nodes: List[Dict] = []
        for child in children_map.get(item.id, []):
            node = build_node(child.id)
            if node:
                children_nodes.append(node)
        return {
            "code": item.code,
            "name": item.name,
            "count": total,
            "children": children_nodes,
        }

    facet_tree = []
    for root in children_map.get(None, []):
        node = build_node(root.id)
        if node:
            facet_tree.append(node)
    return facet_tree


def _build_search_points_facet(
    db: Session,
    q: Optional[str],
    class_code: Optional[str],
    publish_year: Optional[int],
    language: Optional[str],
):
    base_query = _build_resource_query(
        db,
        q=None,
        class_code=class_code,
        search_point=None,
        publish_year=publish_year,
        language=language,
    )
    if not q:
        total = base_query.count()
        return [
            {"key": "题名", "count": total},
            {"key": "责任者", "count": total},
            {"key": "摘要", "count": total},
        ]

    like_pattern = f"%{q}%"
    title_count = (
        _build_resource_query(
            db,
            q=None,
            class_code=class_code,
            publish_year=publish_year,
            language=language,
        )
        .filter(models.Resource.title.ilike(like_pattern))
        .count()
    )
    authors_count = (
        _build_resource_query(
            db,
            q=None,
            class_code=class_code,
            publish_year=publish_year,
            language=language,
        )
        .filter(models.Resource.authors.ilike(like_pattern))
        .count()
    )
    abstract_count = (
        _build_resource_query(
            db,
            q=None,
            class_code=class_code,
            publish_year=publish_year,
            language=language,
        )
        .filter(models.Resource.abstract.ilike(like_pattern))
        .count()
    )
    return [
        {"key": "题名", "count": title_count},
        {"key": "责任者", "count": authors_count},
        {"key": "摘要", "count": abstract_count},
    ]


def _build_publish_year_facet(
    db: Session,
    q: Optional[str],
    class_code: Optional[str],
    search_point: Optional[str],
    language: Optional[str],
):
    filtered_ids = _build_resource_query(
        db,
        q=q,
        class_code=class_code,
        search_point=search_point,
        publish_year=None,
        language=language,
    ).with_entities(models.Resource.id).subquery()

    year_expr = func.coalesce(
        models.Resource.publish_year,
        func.cast(func.strftime("%Y", models.Resource.publish_date), Integer),
    )
    rows = (
        db.query(year_expr.label("year"), func.count(models.Resource.id).label("count"))
        .join(filtered_ids, filtered_ids.c.id == models.Resource.id)
        .group_by(year_expr)
        .order_by(year_expr.desc())
        .all()
    )
    buckets = []
    for row in rows:
        buckets.append(
            {"key": str(row.year) if row.year is not None else "未知", "count": row.count}
        )
    return buckets


def _build_language_facet(
    db: Session,
    q: Optional[str],
    class_code: Optional[str],
    search_point: Optional[str],
    publish_year: Optional[int],
):
    filtered_ids = _build_resource_query(
        db,
        q=q,
        class_code=class_code,
        search_point=search_point,
        publish_year=publish_year,
        language=None,
    ).with_entities(models.Resource.id).subquery()

    lang_expr = func.coalesce(models.Resource.language, "其他")
    rows = (
        db.query(lang_expr.label("lang"), func.count(models.Resource.id).label("count"))
        .join(filtered_ids, filtered_ids.c.id == models.Resource.id)
        .group_by(lang_expr)
        .order_by(func.count(models.Resource.id).desc())
        .all()
    )
    return [{"key": row.lang, "count": row.count} for row in rows]


def search_resources(
    db: Session,
    q: Optional[str],
    skip: int = 0,
    limit: int = 20,
    class_code: Optional[str] = None,
    search_point: Optional[str] = None,
    publish_year: Optional[int] = None,
    language: Optional[str] = None,
):
    base_query = _build_resource_query(
        db,
        q=q,
        class_code=class_code,
        search_point=search_point,
        publish_year=publish_year,
        language=language,
    )
    total = base_query.count()
    items = base_query.order_by(models.Resource.id.asc()).offset(skip).limit(limit).all()
    cnl_facets = _build_facet_tree(
        db,
        q=q,
        search_point=search_point,
        publish_year=publish_year,
        language=language,
    )

    return {
        "items": items,
        "total": total,
        "facets": {
            "cnl": cnl_facets,
            "search_points": _build_search_points_facet(
                db,
                q=q,
                class_code=class_code,
                publish_year=publish_year,
                language=language,
            ),
            "publish_years": _build_publish_year_facet(
                db,
                q=q,
                class_code=class_code,
                search_point=search_point,
                language=language,
            ),
            "languages": _build_language_facet(
                db,
                q=q,
                class_code=class_code,
                search_point=search_point,
                publish_year=publish_year,
            ),
        },
    }


def list_home_resources(db: Session, limit: int = 16):
    return db.query(models.Resource).order_by(models.Resource.id.asc()).limit(limit).all()


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


def _ensure_sample_classes(db: Session) -> Dict[str, models.CnlClass]:
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


def create_sample_data(db: Session) -> None:
    sample_rows = [
        {
            "title": "Machine Learning Basics",
            "authors": "Tom; Jerry",
            "keywords": "machine learning; introduction",
            "publish_year": 2020,
            "publisher": "Demo Press",
            "isbn": "9780000000001",
            "language": "en",
            "page_count": 320,
            "cnl_class_no": "TP181",
            "abstract": "An introduction to machine learning concepts.",
        },
        {
            "title": "Deep Learning in Practice",
            "authors": "Alice; Bob",
            "keywords": "deep learning; neural network; case study",
            "publish_year": 2022,
            "publisher": "Demo Press",
            "isbn": "9780000000002",
            "language": "en",
            "page_count": 420,
            "cnl_class_no": "TP181.1",
            "abstract": "Practical deep learning techniques and case studies.",
        },
        {
            "title": "Data Mining for Academic Libraries",
            "authors": "Carol",
            "keywords": "data mining; library; information retrieval",
            "publish_year": 2018,
            "publisher": "Library Press",
            "isbn": "9780000000003",
            "language": "en",
            "page_count": 250,
            "cnl_class_no": "G252.7",
            "abstract": "Explores data mining methods in academic library systems.",
        },
        {
            "title": "Philosophy of Science: An Introduction",
            "authors": "Steven French",
            "keywords": "philosophy; science; epistemology",
            "publish_year": 2019,
            "publisher": "Academic Minds",
            "isbn": "9780000000004",
            "language": "en",
            "page_count": 288,
            "cnl_class_no": "B01",
            "abstract": "A concise guide to major debates in philosophy of science.",
        },
        {
            "title": "Modern Aesthetics and Visual Culture",
            "authors": "J. Coleman",
            "keywords": "aesthetics; visual culture; art theory",
            "publish_year": 2017,
            "publisher": "Artsline",
            "isbn": "9780000000005",
            "language": "en",
            "page_count": 301,
            "cnl_class_no": "B83",
            "abstract": "A survey of modern aesthetics and visual interpretation.",
        },
        {
            "title": "Information Retrieval Systems",
            "authors": "Ricardo Baeza-Yates; Berthier Ribeiro-Neto",
            "keywords": "information retrieval; indexing; search engine",
            "publish_year": 2011,
            "publisher": "SearchLab",
            "isbn": "9780000000006",
            "language": "en",
            "page_count": 512,
            "cnl_class_no": "G252.7",
            "abstract": "Classic methods and modern architectures for search systems.",
        },
        {
            "title": "World Literature in a Digital Age",
            "authors": "M. Damrosch",
            "keywords": "world literature; comparative literature; digital humanities",
            "publish_year": 2021,
            "publisher": "Global Lit House",
            "isbn": "9780000000007",
            "language": "en",
            "page_count": 275,
            "cnl_class_no": "I106",
            "abstract": "How digital platforms reshape circulation of world literature.",
        },
        {
            "title": "American Fiction Since 1945",
            "authors": "R. Gray",
            "keywords": "american literature; fiction; postwar",
            "publish_year": 2016,
            "publisher": "US Letters Press",
            "isbn": "9780000000008",
            "language": "en",
            "page_count": 366,
            "cnl_class_no": "I712",
            "abstract": "An overview of major authors and themes in late US fiction.",
        },
        {
            "title": "Advanced Calculus for Engineers",
            "authors": "Peter V. O'Neil",
            "keywords": "calculus; engineering mathematics; analysis",
            "publish_year": 2015,
            "publisher": "MathBridge",
            "isbn": "9780000000009",
            "language": "en",
            "page_count": 534,
            "cnl_class_no": "O13",
            "abstract": "Advanced calculus topics with engineering applications.",
        },
        {
            "title": "Probability and Statistics Essentials",
            "authors": "D. Freedman",
            "keywords": "probability; statistics; inference",
            "publish_year": 2014,
            "publisher": "MathBridge",
            "isbn": "9780000000010",
            "language": "en",
            "page_count": 418,
            "cnl_class_no": "O151",
            "abstract": "Foundational probability and statistics for data analysis.",
        },
        {
            "title": "Computer Graphics: Principles and Practice",
            "authors": "John F. Hughes; Andries van Dam",
            "keywords": "computer graphics; rendering; modeling",
            "publish_year": 2013,
            "publisher": "Compute Press",
            "isbn": "9780000000011",
            "language": "en",
            "page_count": 1178,
            "cnl_class_no": "TP391",
            "abstract": "Comprehensive reference for computer graphics techniques.",
        },
        {
            "title": "AI Ethics in Higher Education",
            "authors": "L. Johnson; P. Holmes",
            "keywords": "ai ethics; higher education; policy",
            "publish_year": 2024,
            "publisher": "Campus Research Lab",
            "isbn": "9780000000012",
            "language": "en",
            "page_count": 240,
            "cnl_class_no": "TP18",
            "abstract": "Ethical frameworks for AI deployment in universities.",
        },
    ]

    for row in sample_rows:
        exists = db.query(models.Resource).filter(models.Resource.isbn == row["isbn"]).first()
        if not exists:
            db.add(models.Resource(**row))
    db.flush()

    class_cache = _ensure_sample_classes(db)
    _ensure_resource_class_mappings(db, class_cache)
    db.commit()
