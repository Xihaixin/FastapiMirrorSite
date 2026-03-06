#!/usr/bin/env python3
"""
数据库更新脚本
清空现有数据并重新生成完整的中图分类体系和资源数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import models
from app.seed_data_updated import seed_all


def clear_database(db: Session):
    """清空数据库"""
    print("清空数据库...")
    
    # 注意：由于外键约束，需要按正确顺序删除
    db.query(models.ResourceClassMap).delete()
    db.query(models.Resource).delete()
    db.query(models.CnlClass).delete()
    
    db.commit()
    print("数据库已清空")


def update_database(target_resources: int = 1000):
    """更新数据库"""
    print("=== 开始数据库更新 ===")
    
    # 创建数据库表（如果不存在）
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 清空现有数据
        clear_database(db)
        
        # 使用新的种子数据脚本生成数据
        print(f"\n生成新的分类体系和资源数据（目标: {target_resources} 个资源）...")
        created = seed_all(target_count=target_resources)
        
        # 验证结果
        resource_count = db.query(models.Resource).count()
        class_count = db.query(models.CnlClass).count()
        mapping_count = db.query(models.ResourceClassMap).count()
        
        print(f"\n=== 更新完成 ===")
        print(f"生成的分类数量: {class_count}")
        print(f"生成的资源数量: {resource_count}")
        print(f"资源-分类映射数量: {mapping_count}")
        print(f"新创建的资源: {created}")
        
        # 显示分类统计
        print("\n分类层级统计:")
        from sqlalchemy import func
        level_stats = (
            db.query(models.CnlClass.level, func.count(models.CnlClass.id))
            .group_by(models.CnlClass.level)
            .order_by(models.CnlClass.level)
            .all()
        )
        
        for level, count in level_stats:
            print(f"  层级 {level}: {count} 个分类")
        
        # 显示资源分布
        print("\n资源分类分布 (前15):")
        resource_dist = (
            db.query(models.Resource.cnl_class_no, func.count(models.Resource.id))
            .filter(models.Resource.cnl_class_no.isnot(None))
            .group_by(models.Resource.cnl_class_no)
            .order_by(func.count(models.Resource.id).desc())
            .limit(15)
            .all()
        )
        
        for code, count in resource_dist:
            class_info = db.query(models.CnlClass).filter(models.CnlClass.code == code).first()
            class_name = class_info.name if class_info else "未知"
            print(f"  {code}: {count} 个资源 - {class_name}")
        
        return True
        
    except Exception as e:
        print(f"数据库更新失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def verify_database():
    """验证数据库完整性"""
    print("\n=== 验证数据库完整性 ===")
    
    db = SessionLocal()
    try:
        # 检查分类完整性
        class_count = db.query(models.CnlClass).count()
        print(f"分类总数: {class_count}")
        
        # 检查没有父类的分类（应该是一级分类）
        root_classes = db.query(models.CnlClass).filter(models.CnlClass.parent_id.is_(None)).all()
        print(f"一级分类数量: {len(root_classes)}")
        
        # 检查资源完整性
        resource_count = db.query(models.Resource).count()
        print(f"资源总数: {resource_count}")
        
        # 检查资源分类映射
        resources_without_class = db.query(models.Resource).filter(models.Resource.cnl_class_no.is_(None)).count()
        print(f"没有分类代码的资源: {resources_without_class}")
        
        # 检查映射关系
        mapping_count = db.query(models.ResourceClassMap).count()
        print(f"资源-分类映射数量: {mapping_count}")
        
        # 检查每个资源是否都有映射
        resources_with_mapping = (
            db.query(func.count(models.Resource.id))
            .join(models.ResourceClassMap, models.Resource.id == models.ResourceClassMap.resource_id)
            .scalar()
        )
        print(f"有映射关系的资源: {resources_with_mapping}")
        
        if resources_without_class == 0 and mapping_count >= resource_count:
            print("\n✅ 数据库完整性验证通过")
            return True
        else:
            print("\n❌ 数据库完整性验证失败")
            return False
            
    finally:
        db.close()


def main():
    """主函数"""
    print("开始执行数据库更新...")
    
    # 更新数据库
    success = update_database(target_resources=1000)
    
    if success:
        print("\n运行数据库完整性验证...")
        verify_success = verify_database()
        
        if verify_success:
            print("\n🎉 数据库更新成功完成!")
            print("\n下一步:")
            print("1. 启动应用: uv run python app/main.py")
            print("2. 访问 http://localhost:8000 查看更新后的分类体系")
            print("3. 使用 API 端点查询分类和资源")
            return 0
        else:
            print("\n⚠️ 数据库更新完成，但完整性验证发现问题")
            return 1
    else:
        print("\n❌ 数据库更新失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())