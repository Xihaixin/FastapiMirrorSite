#!/usr/bin/env python3
"""
clc.json分类数据导入脚本
用于将解析出的分类数据导入数据库
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal, engine
from scripts.parse_clc_json import CLCJsonParser


def import_clc_classifications(db: Session, clear_existing: bool = True):
    """导入clc.json分类数据到数据库"""
    
    # 解析clc.json
    parser = CLCJsonParser()
    classifications = parser.parse_file()
    
    print(f"准备导入 {len(classifications)} 个分类...")
    
    if clear_existing:
        print("清空现有分类数据...")
        # 注意：这会级联删除resource_class_map中的关联
        db.query(models.ResourceClassMap).delete()
        db.query(models.CnlClass).delete()
        db.commit()
    
    # 创建分类映射字典
    code_to_id = {}
    
    print("创建分类记录...")
    # 第一遍：创建所有分类（不设置parent_id）
    for cls in classifications:
        cnl_class = models.CnlClass(
            code=cls.code,
            name=cls.name,
            level=cls.level,
            path=cls.path
        )
        db.add(cnl_class)
    
    db.commit()
    
    # 获取所有分类的ID
    all_classes = db.query(models.CnlClass).all()
    for cnl_class in all_classes:
        code_to_id[cnl_class.code] = cnl_class.id
    
    print("更新父分类关系...")
    # 第二遍：更新父分类关系
    for cls in classifications:
        if cls.parent_code and cls.parent_code in code_to_id:
            cnl_class = db.query(models.CnlClass).filter_by(code=cls.code).first()
            if cnl_class:
                cnl_class.parent_id = code_to_id[cls.parent_code]
    
    db.commit()
    
    print("分类数据导入完成！")
    
    # 验证导入结果
    total_count = db.query(models.CnlClass).count()
    print(f"数据库中共有 {total_count} 个分类")
    
    # 统计各层级分类数量
    from sqlalchemy import func
    level_stats = db.query(
        models.CnlClass.level,
        func.count(models.CnlClass.id).label('count')
    ).group_by(models.CnlClass.level).order_by(models.CnlClass.level).all()
    
    print("层级统计:")
    for level, count in level_stats:
        print(f"  层级 {level}: {count} 个分类")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='导入clc.json分类数据到数据库')
    parser.add_argument('--clear', action='store_true',
                       help='清空现有分类数据')
    parser.add_argument('--no-clear', dest='clear', action='store_false',
                       help='不清空现有数据（追加导入）')
    parser.set_defaults(clear=True)
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        import_clc_classifications(db, clear_existing=args.clear)
    finally:
        db.close()


if __name__ == "__main__":
    main()
