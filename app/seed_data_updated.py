import argparse
import random
from collections import Counter
from typing import Dict, Optional, List, Tuple

from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal, engine

# 导入完整的分类定义
from .cnl_classifications import CLASS_DEFS, GEN_CLASS_WEIGHTS

# 使用完整的权重列表
GEN_CLASS_CODES = list(GEN_CLASS_WEIGHTS.keys())

# 扩展主题列表以匹配更细的分类
SUBJECTS = [
    # 计算机科学
    "machine learning", "artificial intelligence", "data science", "computer networks",
    "software engineering", "database systems", "cybersecurity", "cloud computing",
    "web development", "mobile applications", "algorithm design", "computer graphics",
    
    # 经济与管理
    "economic policy", "financial markets", "business management", "marketing strategy",
    "supply chain", "human resources", "entrepreneurship", "investment analysis",
    "corporate finance", "international trade", "economic development",
    
    # 医学与健康
    "medical informatics", "public health", "clinical medicine", "pharmacology",
    "nursing practice", "medical research", "healthcare management", "biomedical engineering",
    "epidemiology", "nutrition science", "mental health",
    
    # 自然科学
    "applied statistics", "advanced chemistry", "quantum physics", "biological systems",
    "environmental science", "geological studies", "astrophysics", "mathematical modeling",
    "organic chemistry", "cell biology", "genetics research",
    
    # 工程与技术
    "aerospace engineering", "civil engineering", "electrical systems", "mechanical design",
    "robotics technology", "manufacturing processes", "material science", "energy systems",
    "transportation systems", "construction management", "industrial automation",
    
    # 人文社科
    "political philosophy", "digital humanities", "world history", "cultural studies",
    "linguistic analysis", "literary criticism", "art history", "sociological research",
    "psychological studies", "educational theory", "legal frameworks",
    
    # 农业与环境
    "agricultural science", "sustainable farming", "forestry management", "food technology",
    "environmental protection", "climate change", "water resources", "soil science",
    "wildlife conservation", "renewable energy",
]

NOUNS = [
    "methods", "foundations", "applications", "practice", "analysis", "perspectives",
    "workbook", "handbook", "essentials", "approaches", "techniques", "principles",
    "theory", "implementation", "case studies", "research", "development", "innovation",
    "strategies", "solutions", "framework", "models", "systems", "technologies",
]

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "David", "Emily", "Frank", "Grace", "Helen", "Ian", "Julia",
    "Kevin", "Liam", "Megan", "Nathan", "Olivia", "Peter", "Quinn", "Rachel", "Steve", "Tina",
    "Victor", "Wendy", "Xavier", "Yvonne", "Zachary", "James", "Mary", "John", "Patricia",
    "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "Richard", "Susan",
]

LAST_NAMES = [
    "Smith", "Johnson", "Brown", "Miller", "Davis", "Wilson", "Moore", "Taylor", "Anderson",
    "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez",
    "Robinson", "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Allen", "Young",
    "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Carter", "Mitchell",
]

PUBLISHERS = [
    "Global Academic Press", "Northbridge Publishing", "Open Study Books", "Scholar House",
    "Campus Research Lab", "Science Press", "Technology Publications", "Medical Books Inc",
    "Economic Review Press", "Engineering Society", "Humanities Publishing", "Art World Press",
    "Environmental Publications", "Agricultural Press", "Legal Texts Publishing",
]

LANGUAGES = ["en", "en", "en", "en", "zh-CN", "fr", "de", "ja", "es", "ru", None]


def _get_or_create_class(
    db: Session,
    class_cache: Dict[str, models.CnlClass],
    code: str,
    name: str,
    parent_code: Optional[str],
    level: int,
) -> models.CnlClass:
    """获取或创建分类"""
    if code in class_cache:
        return class_cache[code]
    
    parent = class_cache.get(parent_code) if parent_code else None
    item = db.query(models.CnlClass).filter(models.CnlClass.code == code).one_or_none()
    
    if not item:
        # 计算路径
        if parent:
            path = f"{parent.path}/{code}" if parent.path else code
        else:
            path = code
            
        item = models.CnlClass(
            code=code,
            name=name,
            parent_id=parent.id if parent else None,
            level=level,
            path=path,
        )
        db.add(item)
        db.flush()
    
    class_cache[code] = item
    return item


def ensure_class_tree(db: Session) -> Dict[str, models.CnlClass]:
    """确保分类树存在"""
    class_cache: Dict[str, models.CnlClass] = {}
    
    # 先加载现有的分类
    for row in db.query(models.CnlClass).all():
        class_cache[row.code] = row
    
    # 创建所有分类
    for code, name, parent_code, level in CLASS_DEFS:
        _get_or_create_class(db, class_cache, code, name, parent_code, level)
    
    db.flush()
    return class_cache


def _ensure_resource_class_mappings(
    db: Session,
    class_cache: Dict[str, models.CnlClass],
) -> None:
    """确保资源与分类的映射关系"""
    resources = db.query(models.Resource).all()
    
    for resource in resources:
        if not resource.cnl_class_no:
            continue
            
        target = class_cache.get(resource.cnl_class_no)
        if not target:
            # 如果分类不存在，创建它
            print(f"警告: 分类 {resource.cnl_class_no} 不存在，尝试创建...")
            # 这里简化处理，实际应该根据代码推断层级
            target = _get_or_create_class(
                db,
                class_cache,
                resource.cnl_class_no,
                resource.cnl_class_no,  # 使用代码作为名称
                None,
                1,
            )
        
        # 检查映射是否已存在
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
    """根据权重随机选择分类代码"""
    total = sum(GEN_CLASS_WEIGHTS.values())
    if total == 0:
        return random.choice(GEN_CLASS_CODES)
    
    pick = rng.randint(1, total)
    acc = 0
    
    for code, w in GEN_CLASS_WEIGHTS.items():
        acc += w
        if pick <= acc:
            return code
    
    # 默认返回第一个
    return GEN_CLASS_CODES[0] if GEN_CLASS_CODES else "F"


def _build_resource_row(seq: int, rng: random.Random, class_code: str) -> dict:
    """构建资源数据行"""
    subject = rng.choice(SUBJECTS)
    noun = rng.choice(NOUNS)
    
    # 根据分类调整主题
    if class_code.startswith("TP"):
        subject = rng.choice(["machine learning", "artificial intelligence", "data science", 
                             "software engineering", "computer networks", "cybersecurity"])
    elif class_code.startswith("F"):
        subject = rng.choice(["economic policy", "financial markets", "business management", 
                             "marketing strategy", "investment analysis"])
    elif class_code.startswith("R"):
        subject = rng.choice(["medical informatics", "clinical medicine", "public health", 
                             "pharmacology", "biomedical engineering"])
    
    title = f"{subject.title()} {noun.title()} Vol.{seq}"
    
    # 生成作者
    author1 = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    author2 = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    
    # 生成出版年份
    year = rng.randint(2000, 2025)
    
    # 生成ISBN
    isbn = str(9790000000000 + seq)
    
    # 生成关键词
    keywords = f"{subject}; {noun}; academic; reference"
    if class_code.startswith("TP"):
        keywords += "; computer science; technology"
    elif class_code.startswith("F"):
        keywords += "; economics; business"
    elif class_code.startswith("R"):
        keywords += "; medicine; health"
    
    return {
        "title": title,
        "authors": f"{author1}; {author2}",
        "keywords": keywords,
        "publish_year": year,
        "publisher": rng.choice(PUBLISHERS),
        "isbn": isbn,
        "language": rng.choice(LANGUAGES),
        "page_count": rng.randint(120, 980),
        "cnl_class_no": class_code,
        "abstract": f"This volume discusses {subject} with {noun} in academic and professional contexts. It provides comprehensive coverage of the latest developments and applications in the field.",
    }


def _create_one_resource(
    db: Session,
    existing_isbns: set,
    seq_start: int,
    rng: random.Random,
    forced_code: Optional[str] = None,
) -> int:
    """创建一个资源"""
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
    target_count: int = 1000,  # 增加目标数量，因为分类更多了
    seed: int = 20260305,
    min_per_class: int = 3,  # 减少每个分类的最小数量，因为分类太多
) -> int:
    """种子资源数据"""
    # 确保分类树存在
    class_cache = ensure_class_tree(db)
    rng = random.Random(seed)
    
    # 获取现有的ISBN
    existing_isbns = {x[0] for x in db.query(models.Resource.isbn).all()}
    seq = 1
    created = 0
    
    # 先保证常用分类的覆盖
    class_counts = Counter(
        code for (code,) in db.query(models.Resource.cnl_class_no)
        .filter(models.Resource.cnl_class_no.isnot(None)).all()
    )
    
    # 只对权重较高的分类保证最小数量
    high_weight_codes = [code for code, weight in GEN_CLASS_WEIGHTS.items() if weight >= 5]
    
    for code in high_weight_codes[:50]:  # 只处理前50个高权重分类
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
    
    # 确保资源与分类的映射
    _ensure_resource_class_mappings(db, class_cache)
    db.commit()
    
    return created


def seed_all(target_count: int = 1000) -> int:
    """种子所有数据"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        return seed_resources(db, target_count=target_count)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed resources into local database with complete CNL classification.")
    parser.add_argument("--count", type=int, default=1000, help="Target total resource count.")
    parser.add_argument("--min-per-class", type=int, default=3, help="Ensure minimum records per high-weight class.")
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
        print(f"Total resources in database: {db.query(models.Resource).count()}")
        print(f"Total classifications in database: {db.query(models.CnlClass).count()}")
    finally:
        db.close()