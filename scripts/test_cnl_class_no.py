#!/usr/bin/env python3
"""
测试cnl_class_no字段和映射关系的正确性
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from app.database import SessionLocal


def test_cnl_class_no_field():
    """测试Resources表中的cnl_class_no字段"""
    print("=" * 60)
    print("测试Resources表中的cnl_class_no字段")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 1. 检查有多少资源设置了cnl_class_no字段
        total_resources = db.query(models.Resource).count()
        resources_with_cnl_class_no = db.query(models.Resource).filter(
            models.Resource.cnl_class_no.isnot(None)
        ).count()
        
        print(f"1. 资源总数: {total_resources}")
        print(f"   设置了cnl_class_no字段的资源数: {resources_with_cnl_class_no}")
        print(f"   设置率: {(resources_with_cnl_class_no/total_resources*100):.1f}%")
        
        # 2. 检查cnl_class_no字段的值是否有效（存在于cnl_classes表中）
        print("\n2. cnl_class_no字段有效性检查:")
        
        # 获取所有有效的分类代码
        valid_class_codes = {c[0] for c in db.query(models.CnlClass.code).all()}
        
        # 检查资源中的cnl_class_no是否有效
        resources = db.query(models.Resource).filter(
            models.Resource.cnl_class_no.isnot(None)
        ).limit(20).all()
        
        invalid_count = 0
        valid_count = 0
        
        print("   抽样检查20个资源:")
        for i, resource in enumerate(resources, 1):
            if resource.cnl_class_no in valid_class_codes:
                valid_count += 1
                status = "[OK]"
            else:
                invalid_count += 1
                status = "[INVALID]"
            
            print(f"     {i:2d}. 资源ID={resource.id:4d}, cnl_class_no='{resource.cnl_class_no}' {status}")
        
        print(f"\n   有效: {valid_count}, 无效: {invalid_count}")
        
        # 3. 检查resource_class_map映射关系
        print("\n3. resource_class_map映射关系检查:")
        
        total_mappings = db.query(models.ResourceClassMap).count()
        print(f"   映射总数: {total_mappings}")
        
        # 检查每个资源的映射是否与其cnl_class_no对应
        sample_resources = db.query(models.Resource).filter(
            models.Resource.cnl_class_no.isnot(None)
        ).limit(10).all()
        
        print("   抽样检查10个资源的映射关系:")
        for resource in sample_resources:
            # 获取该资源的所有映射
            mappings = db.query(models.ResourceClassMap).filter_by(
                resource_id=resource.id
            ).all()
            
            # 查找主要分类映射
            primary_mapping = None
            for mapping in mappings:
                if mapping.is_primary == 1:
                    primary_mapping = mapping
                    break
            
            if primary_mapping:
                # 获取分类信息
                cnl_class = db.query(models.CnlClass).filter_by(
                    id=primary_mapping.class_id
                ).first()
                
                if cnl_class:
                    # 检查分类代码是否与cnl_class_no匹配
                    if cnl_class.code == resource.cnl_class_no:
                        match_status = "[MATCH]"
                    else:
                        match_status = "[MISMATCH]"
                    
                    print(f"     - 资源ID={resource.id}: cnl_class_no='{resource.cnl_class_no}'")
                    print(f"       主要映射 -> 分类: {cnl_class.code} ({cnl_class.name}) {match_status}")
                    print(f"       总映射数: {len(mappings)}")
            
            else:
                print(f"     - 资源ID={resource.id}: 没有主要分类映射")
        
        # 4. 统计映射分布
        print("\n4. 映射分布统计:")
        
        # 每个资源的平均映射数
        if total_resources > 0:
            avg_mappings = total_mappings / total_resources
            print(f"   平均每个资源的映射数: {avg_mappings:.2f}")
        
        # 主要vs次要映射
        primary_mappings = db.query(models.ResourceClassMap).filter_by(is_primary=1).count()
        secondary_mappings = total_mappings - primary_mappings
        
        print(f"   主要分类映射: {primary_mappings}")
        print(f"   次要分类映射: {secondary_mappings}")
        
        # 5. 验证数据一致性
        print("\n5. 数据一致性验证:")
        
        # 检查是否有资源没有映射
        resources_without_mappings = db.query(models.Resource).filter(
            ~models.Resource.id.in_(
                db.query(models.ResourceClassMap.resource_id)
            )
        ).count()
        
        print(f"   没有映射的资源数: {resources_without_mappings}")
        
        # 检查是否有映射对应的资源不存在
        mappings_without_resources = db.query(models.ResourceClassMap).filter(
            ~models.ResourceClassMap.resource_id.in_(
                db.query(models.Resource.id)
            )
        ).count()
        
        print(f"   对应资源不存在的映射数: {mappings_without_resources}")
        
        # 检查是否有映射对应的分类不存在
        mappings_without_classes = db.query(models.ResourceClassMap).filter(
            ~models.ResourceClassMap.class_id.in_(
                db.query(models.CnlClass.id)
            )
        ).count()
        
        print(f"   对应分类不存在的映射数: {mappings_without_classes}")
        
        print("\n" + "=" * 60)
        if (invalid_count == 0 and resources_without_mappings == 0 and 
            mappings_without_resources == 0 and mappings_without_classes == 0):
            print("测试通过！所有数据一致性检查都成功。")
        else:
            print("测试发现一些问题，需要进一步检查。")
        print("=" * 60)
        
    finally:
        db.close()


def main():
    """主函数"""
    test_cnl_class_no_field()


if __name__ == "__main__":
    main()