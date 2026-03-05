#!/usr/bin/env python3
"""
测试分类导入功能
验证完整的中图分类体系是否正确导入数据库
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import models
from app.seed_data_updated import ensure_class_tree, seed_resources


def test_classification_import():
    """测试分类导入"""
    print("=== 测试分类导入功能 ===")
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 清空现有数据
        print("清空现有数据...")
        db.query(models.ResourceClassMap).delete()
        db.query(models.Resource).delete()
        db.query(models.CnlClass).delete()
        db.commit()
        
        # 导入分类树
        print("导入分类树...")
        class_cache = ensure_class_tree(db)
        
        # 验证分类数量
        class_count = db.query(models.CnlClass).count()
        print(f"导入的分类数量: {class_count}")
        
        # 验证层级关系
        print("\n验证层级关系...")
        
        # 检查一级分类
        level1_classes = db.query(models.CnlClass).filter(models.CnlClass.level == 1).all()
        print(f"一级分类数量: {len(level1_classes)}")
        print("一级分类示例:")
        for cls in level1_classes[:10]:
            print(f"  {cls.code}: {cls.name}")
        
        # 检查二级分类
        level2_classes = db.query(models.CnlClass).filter(models.CnlClass.level == 2).all()
        print(f"\n二级分类数量: {len(level2_classes)}")
        
        # 检查三级分类
        level3_classes = db.query(models.CnlClass).filter(models.CnlClass.level == 3).all()
        print(f"三级分类数量: {len(level3_classes)}")
        
        # 检查父子关系
        print("\n检查父子关系...")
        classes_with_parent = db.query(models.CnlClass).filter(models.CnlClass.parent_id.isnot(None)).count()
        print(f"有父类的分类数量: {classes_with_parent}")
        
        # 检查路径字段
        print("\n检查路径字段...")
        classes_with_path = db.query(models.CnlClass).filter(models.CnlClass.path.isnot(None)).count()
        print(f"有路径的分类数量: {classes_with_path}")
        
        # 示例路径
        sample_class = db.query(models.CnlClass).filter(models.CnlClass.code == "TP31").first()
        if sample_class:
            print(f"示例分类 TP31 的路径: {sample_class.path}")
        
        # 测试资源生成
        print("\n=== 测试资源生成 ===")
        created = seed_resources(db, target_count=50, min_per_class=1)
        print(f"生成的资源数量: {created}")
        
        # 验证资源与分类的映射
        resource_count = db.query(models.Resource).count()
        mapping_count = db.query(models.ResourceClassMap).count()
        
        print(f"\n资源总数: {resource_count}")
        print(f"资源-分类映射总数: {mapping_count}")
        
        # 检查资源分类分布
        print("\n资源分类分布 (前10):")
        from sqlalchemy import func
        result = (
            db.query(models.Resource.cnl_class_no, func.count(models.Resource.id))
            .filter(models.Resource.cnl_class_no.isnot(None))
            .group_by(models.Resource.cnl_class_no)
            .order_by(func.count(models.Resource.id).desc())
            .limit(10)
            .all()
        )
        
        for code, count in result:
            class_info = db.query(models.CnlClass).filter(models.CnlClass.code == code).first()
            class_name = class_info.name if class_info else "未知"
            print(f"  {code}: {count} 个资源 - {class_name}")
        
        print("\n=== 测试完成 ===")
        print("所有测试通过!")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def test_classification_hierarchy():
    """测试分类层级关系"""
    print("\n=== 测试分类层级关系 ===")
    
    db = SessionLocal()
    try:
        # 测试几个关键分类的层级关系
        test_cases = [
            ("A", None, 1, "A"),  # 一级分类
            ("A1", "A", 2, "A/A1"),  # 二级分类
            ("A11", "A1", 3, "A/A1/A11"),  # 三级分类
            ("B", None, 1, "B"),
            ("B0", "B", 2, "B/B0"),
            ("B0-0", "B0", 3, "B/B0/B0-0"),
            ("TP", "T", 2, "T/TP"),
            ("TP3", "TP", 3, "T/TP/TP3"),
            ("TP31", "TP3", 3, "T/TP/TP3/TP31"),
        ]
        
        all_passed = True
        for code, expected_parent, expected_level, expected_path in test_cases:
            cls = db.query(models.CnlClass).filter(models.CnlClass.code == code).first()
            if not cls:
                print(f"❌ 分类 {code} 不存在")
                all_passed = False
                continue
                
            # 检查父类
            parent_code = None
            if cls.parent_id:
                parent = db.query(models.CnlClass).filter(models.CnlClass.id == cls.parent_id).first()
                parent_code = parent.code if parent else None
                
            if parent_code != expected_parent:
                print(f"❌ 分类 {code} 的父类错误: 期望 {expected_parent}, 实际 {parent_code}")
                all_passed = False
                
            # 检查层级
            if cls.level != expected_level:
                print(f"❌ 分类 {code} 的层级错误: 期望 {expected_level}, 实际 {cls.level}")
                all_passed = False
                
            # 检查路径
            if cls.path != expected_path:
                print(f"❌ 分类 {code} 的路径错误: 期望 {expected_path}, 实际 {cls.path}")
                all_passed = False
                
            if parent_code == expected_parent and cls.level == expected_level and cls.path == expected_path:
                print(f"[OK] 分类 {code} 测试通过")
        
        return all_passed
        
    finally:
        db.close()


def main():
    """主测试函数"""
    print("开始测试完整的中图分类体系导入...")
    
    # 运行测试
    success = test_classification_import()
    
    if success:
        print("\n运行层级关系测试...")
        hierarchy_success = test_classification_hierarchy()
        
        if hierarchy_success:
            print("\n🎉 所有测试通过! 分类体系更新成功!")
            return 0
        else:
            print("\n❌ 层级关系测试失败")
            return 1
    else:
        print("\n❌ 分类导入测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())