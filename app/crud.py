from typing import Dict, List, Optional

from sqlalchemy import Integer, func, or_
from sqlalchemy.orm import Query, Session

from app import models

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
    return [
        {"key": str(row.year) if row.year is not None else "未知", "count": row.count}
        for row in rows
    ]


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
