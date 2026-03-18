#!/usr/bin/env python3
"""
验证clc.json分类数据导入结果
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app import models
from app.database import SessionLocal


def verify_classification_import():
    """验证分类数据导入结果"""
    print("=" * 60)
    print("验证clc.json分类数据导入结果")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 1. 检查分类总数
        total_classes = db.query(models.CnlClass).count()
        print(f"1. 数据库中的分类总数: {total_classes}")
        
        # 2. 检查层级分布
        print("\n2. 分类层级分布:")
        level_stats = db.query(
            models.CnlClass.level,
            func.count(models.CnlClass.id).label('count')
        ).group_by(models.CnlClass.level).order_by(models.CnlClass.level).all()
        
        for level, count in level_stats:
            percentage = (count / total_classes) * 100
            print(f"   层级 {level}: {count} 个分类 ({percentage:.1f}%)")
        
        # 3. 检查顶级分类
        print("\n3. 顶级分类检查:")
        top_level_classes = db.query(models.CnlClass).filter(
            models.CnlClass.parent_id.is_(None)
        ).all()
        
        print(f"   顶级分类数量: {len(top_level_classes)}")
        print("   顶级分类列表:")
        for cls in top_level_classes[:10]:  # 只显示前10个
            print(f"     - {cls.code}: {cls.name}")
        
        if len(top_level_classes) > 10:
            print(f"     ... 还有 {len(top_level_classes) - 10} 个顶级分类")
        
        # 4. 检查层级关系完整性
        print("\n4. 层级关系完整性检查:")
        
        # 检查没有父分类但层级不是1的分类
        invalid_parents = db.query(models.CnlClass).filter(
            and_(
                models.CnlClass.parent_id.is_(None),
                models.CnlClass.level != 1
            )
        ).count()
        
        print(f"   无效的顶级分类（parent_id为None但level≠1）: {invalid_parents}")
        
        # 检查父分类不存在的分类
        all_class_ids = {c.id for c in db.query(models.CnlClass.id).all()}
        classes_with_invalid_parents = []
        
        all_classes = db.query(models.CnlClass).all()
        for cls in all_classes:
            if cls.parent_id is not None and cls.parent_id not in all_class_ids:
                classes_with_invalid_parents.append(cls.code)
        
        print(f"   父分类不存在的分类数量: {len(classes_with_invalid_parents)}")
        if classes_with_invalid_parents:
            print(f"   前5个有问题的分类: {classes_with_invalid_parents[:5]}")
        
        # 5. 检查分类代码唯一性
        print("\n5. 分类代码唯一性检查:")
        duplicate_codes = db.query(
            models.CnlClass.code,
            func.count(models.CnlClass.id).label('count')
        ).group_by(models.CnlClass.code).having(func.count(models.CnlClass.id) > 1).all()
        
        print(f"   重复的分类代码数量: {len(duplicate_codes)}")
        if duplicate_codes:
            for code, count in duplicate_codes[:5]:
                print(f"     - {code}: 重复 {count} 次")
        
        # 6. 检查路径字段
        print("\n6. 路径字段检查:")
        classes_without_path = db.query(models.CnlClass).filter(
            models.CnlClass.path.is_(None)
        ).count()
        
        print(f"   没有路径的分类数量: {classes_without_path}")
        
        # 7. 检查资源关联
        print("\n7. 资源关联检查:")
        total_resources = db.query(models.Resource).count()
        total_mappings = db.query(models.ResourceClassMap).count()
        
        print(f"   资源总数: {total_resources}")
        print(f"   资源-分类关联总数: {total_mappings}")
        
        if total_resources > 0:
            avg_mappings_per_resource = total_mappings / total_resources
            print(f"   平均每个资源的分类关联数: {avg_mappings_per_resource:.1f}")
        
        # 8. 检查分类使用情况
        print("\n8. 分类使用情况:")
        used_classes = db.query(models.CnlClass).filter(
            models.CnlClass.id.in_(
                db.query(models.ResourceClassMap.class_id)
            )
        ).count()
        
        unused_classes = total_classes - used_classes
        usage_rate = (used_classes / total_classes) * 100 if total_classes > 0 else 0
        
        print(f"   被使用的分类数量: {used_classes}")
        print(f"   未使用的分类数量: {unused_classes}")
        print(f"   分类使用率: {usage_rate:.1f}%")
        
        # 9. 抽样检查具体分类
        print("\n9. 抽样检查具体分类:")
        
        # 随机选择5个分类进行检查
        sample_classes = db.query(models.CnlClass).order_by(func.random()).limit(5).all()
        
        for cls in sample_classes:
            parent_name = "无" if cls.parent_id is None else db.query(
                models.CnlClass.name
            ).filter_by(id=cls.parent_id).first()[0]
            
            child_count = db.query(models.CnlClass).filter_by(parent_id=cls.id).count()
            resource_count = db.query(models.ResourceClassMap).filter_by(class_id=cls.id).count()
            
            print(f"   - {cls.code} ({cls.name})")
            print(f"     层级: {cls.level}, 父分类: {parent_name}")
            print(f"     子分类数: {child_count}, 关联资源数: {resource_count}")
            print(f"     路径: {cls.path}")
        
        print("\n" + "=" * 60)
        print("验证完成!")
        print("=" * 60)
        
        # 总结
        print("\n总结:")
        if invalid_parents == 0 and len(classes_with_invalid_parents) == 0 and len(duplicate_codes) == 0:
            print("  [OK] 分类数据完整性良好")
        else:
            print("  [WARNING] 分类数据存在一些问题，需要检查")
        
        if usage_rate > 1.0:
            print("  [OK] 分类使用率合理")
        else:
            print("  [WARNING] 分类使用率较低，可以考虑增加资源数量")
        
    finally:
        db.close()


def test_api_compatibility():
    """测试API兼容性"""
    print("\n" + "=" * 60)
    print("测试API兼容性")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 测试分类查询
        print("1. 测试分类查询:")
        
        # 获取所有顶级分类
        top_classes = db.query(models.CnlClass).filter_by(parent_id=None).all()
        print(f"   成功获取 {len(top_classes)} 个顶级分类")
        
        # 获取特定分类的子分类
        if top_classes:
            sample_class = top_classes[0]
            children = db.query(models.CnlClass).filter_by(parent_id=sample_class.id).all()
            print(f"   分类 '{sample_class.code}' 有 {len(children)} 个子分类")
        
        # 测试资源查询
        print("\n2. 测试资源查询:")
        resources = db.query(models.Resource).limit(5).all()
        print(f"   成功获取 {len(resources)} 个资源样本")
        
        # 测试资源分类关联查询
        print("\n3. 测试资源分类关联查询:")
        if resources:
            resource = resources[0]
            mappings = db.query(models.ResourceClassMap).filter_by(resource_id=resource.id).all()
            print(f"   资源 '{resource.title}' 关联到 {len(mappings)} 个分类")
            
            for mapping in mappings:
                cnl_class = db.query(models.CnlClass).filter_by(id=mapping.class_id).first()
                if cnl_class:
                    primary = "主要" if mapping.is_primary == 1 else "次要"
                    print(f"     - {cnl_class.code}: {cnl_class.name} ({primary}分类)")
        
        print("\n✅ API兼容性测试通过")
        
    finally:
        db.close()


def main():
    """主函数"""
    verify_classification_import()
    test_api_compatibility()


if __name__ == "__main__":
    main()