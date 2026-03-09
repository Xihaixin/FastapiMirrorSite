#!/usr/bin/env python3
"""
数据库更新脚本
使用clc.json更新图书分类数据，并创建虚拟资源数据

功能：
1. 导入完整的clc.json分类体系
2. 清空现有分类数据（可选）
3. 创建虚拟图书资源
4. 关联资源到分类
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from app.database import SessionLocal, engine, Base
from scripts.parse_clc_json import CLCJsonParser


def import_clc_classifications(db: Session, clear_existing: bool = True) -> Dict[str, int]:
    """
    导入clc.json分类数据到数据库
    
    参数:
        db: 数据库会话
        clear_existing: 是否清空现有数据
        
    返回:
        分类代码到ID的映射字典
    """
    print("=" * 60)
    print("开始导入clc.json分类数据")
    print("=" * 60)
    
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
        print("现有数据已清空")
    
    # 创建分类映射字典
    code_to_id = {}
    
    print("创建分类记录...")
    # 第一遍：创建所有分类（不设置parent_id）
    batch_size = 1000
    for i in range(0, len(classifications), batch_size):
        batch = classifications[i:i + batch_size]
        for cls in batch:
            cnl_class = models.CnlClass(
                code=cls.code,
                name=cls.name,
                level=cls.level,
                path=cls.path
            )
            db.add(cnl_class)
        
        if i % 5000 == 0:
            print(f"  已处理 {i}/{len(classifications)} 个分类...")
    
    db.commit()
    print("所有分类记录已创建")
    
    # 获取所有分类的ID
    print("获取分类ID映射...")
    all_classes = db.query(models.CnlClass).all()
    for cnl_class in all_classes:
        code_to_id[cnl_class.code] = cnl_class.id
    
    print("更新父分类关系...")
    # 第二遍：更新父分类关系
    for i, cls in enumerate(classifications):
        if cls.parent_code and cls.parent_code in code_to_id:
            cnl_class = db.query(models.CnlClass).filter_by(code=cls.code).first()
            if cnl_class:
                cnl_class.parent_id = code_to_id[cls.parent_code]
        
        if i % 5000 == 0:
            print(f"  已更新 {i}/{len(classifications)} 个分类的父关系...")
    
    db.commit()
    
    print("分类数据导入完成！")
    
    # 验证导入结果
    total_count = db.query(models.CnlClass).count()
    print(f"数据库中共有 {total_count} 个分类")
    
    # 统计各层级分类数量
    level_stats = db.query(
        models.CnlClass.level,
        func.count(models.CnlClass.id).label('count')
    ).group_by(models.CnlClass.level).order_by(models.CnlClass.level).all()
    
    print("层级统计:")
    for level, count in level_stats:
        print(f"  层级 {level}: {count} 个分类")
    
    return code_to_id


def create_virtual_resources(db: Session, num_resources: int = 1000,
                            code_to_id: Optional[Dict[str, int]] = None) -> List[models.Resource]:
    """
    创建虚拟图书资源
    
    参数:
        db: 数据库会话
        num_resources: 要创建的资源数量
        code_to_id: 分类代码到ID的映射
        
    返回:
        创建的资源列表
    """
    print("=" * 60)
    print(f"开始创建 {num_resources} 个虚拟资源")
    print("=" * 60)
    
    # 如果没有提供分类映射，从数据库获取
    if code_to_id is None:
        code_to_id = {}
        all_classes = db.query(models.CnlClass).all()
        for cnl_class in all_classes:
            code_to_id[cnl_class.code] = cnl_class.id
    
    # 获取所有分类代码（用于随机选择）
    class_codes = list(code_to_id.keys())
    if not class_codes:
        print("错误: 数据库中没有分类数据")
        return []
    
    # 虚拟数据生成配置
    subjects = [
        "机器学习", "人工智能", "数据科学", "计算机网络", "软件工程",
        "数据库系统", "网络安全", "云计算", "Web开发", "移动应用",
        "算法设计", "计算机图形学", "经济政策", "金融市场", "商业管理",
        "营销策略", "供应链", "人力资源", "创业", "投资分析",
        "公司金融", "国际贸易", "经济发展", "医学信息学", "公共卫生",
        "临床医学", "药理学", "护理实践", "医学研究", "医疗管理",
        "生物医学工程", "流行病学", "营养科学", "心理健康", "应用统计",
        "高级化学", "量子物理", "生物系统", "环境科学", "地质研究",
        "天体物理学", "数学建模", "有机化学", "细胞生物学", "遗传学研究",
        "航空航天工程", "土木工程", "电气系统", "机械设计", "机器人技术",
        "制造工艺", "材料科学", "能源系统", "交通系统", "施工管理",
        "工业自动化", "政治哲学", "数字人文", "世界历史", "文化研究",
        "语言分析", "文学批评", "艺术史", "社会学研究", "心理学研究",
        "教育理论", "法律框架", "农业科学", "可持续农业", "林业管理",
        "食品技术", "水资源管理", "生态保护"
    ]
    
    nouns = [
        "方法", "基础", "应用", "实践", "原理", "技术", "系统", "理论",
        "研究", "分析", "设计", "开发", "实现", "评估", "优化", "管理",
        "策略", "规划", "模型", "框架", "工具", "平台", "算法", "协议",
        "标准", "指南", "手册", "教程", "案例", "经验", "趋势", "挑战",
        "机遇", "创新", "改革", "发展", "进步", "突破", "成就", "贡献"
    ]
    
    authors_first = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴",
                     "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗"]
    
    authors_last = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军",
                    "洋", "勇", "艳", "杰", "娟", "涛", "明", "超", "秀兰", "霞"]
    
    publishers = [
        "人民出版社", "科学出版社", "高等教育出版社", "清华大学出版社", "北京大学出版社",
        "机械工业出版社", "电子工业出版社", "化学工业出版社", "人民邮电出版社", "中国电力出版社",
        "上海交通大学出版社", "复旦大学出版社", "浙江大学大学出版社", "武汉大学出版社",
        "中山大学出版社", "南京大学出版社", "中国人民大学出版社", "中国科学技术出版社",
        "中国建筑工业出版社", "中国水利水电出版社", "中国农业出版社", "中国医药科技出版社",
        "中国法制出版社", "中国财政经济出版社", "中国统计出版社", "中国环境科学出版社",
        "中国林业出版社", "中国海洋出版社", "中国地图出版社", "中国旅游出版社"
    ]
    
    languages = ["zh-CN", "en", "ja", "ko", "de", "fr", "ru", "es"]
    
    resources = []
    
    print(f"创建 {num_resources} 个资源...")
    for i in range(num_resources):
        # 生成随机ISBN
        isbn = f"978-7-{random.randint(100, 999)}-{random.randint(10000, 99999)}-{random.randint(0, 9)}"
        
        # 生成标题
        subject = random.choice(subjects)
        noun = random.choice(nouns)
        title = f"{subject}{noun}"
        
        # 生成作者（1-3位作者）
        num_authors = random.randint(1, 3)
        authors = []
        for _ in range(num_authors):
            author = f"{random.choice(authors_first)}{random.choice(authors_last)}"
            authors.append(author)
        authors_str = "; ".join(authors)
        
        # 生成关键词
        num_keywords = random.randint(2, 5)
        keywords = random.sample(subjects, min(num_keywords, len(subjects)))
        keywords_str = "; ".join(keywords)
        
        # 生成出版日期
        publish_year = random.randint(2000, 2023)
        publish_month = random.randint(1, 12)
        publish_day = random.randint(1, 28)
        publish_date = datetime(publish_year, publish_month, publish_day)
        
        # 随机选择一个分类作为主要分类
        primary_class_code = random.choice(class_codes)
        
        # 创建资源对象，设置cnl_class_no字段
        resource = models.Resource(
            title=title,
            authors=authors_str,
            keywords=keywords_str,
            publish_date=publish_date,
            publish_year=publish_year,
            publisher=random.choice(publishers),
            isbn=isbn,
            language=random.choice(languages),
            page_count=random.randint(100, 800),
            cnl_class_no=primary_class_code,  # 设置主要分类号
            abstract=f"本书系统地介绍了{subject}的{noun}，涵盖了相关理论和实践应用。"
        )
        
        db.add(resource)
        resources.append(resource)
        
        # 每100个资源提交一次
        if i % 100 == 0 and i > 0:
            db.commit()
            print(f"  已创建 {i}/{num_resources} 个资源...")
    
    db.commit()
    print(f"所有 {num_resources} 个资源已创建")
    
    return resources


def associate_resources_with_classes(db: Session, resources: List[models.Resource],
                                    code_to_id: Dict[str, int],
                                    max_classes_per_resource: int = 3):
    """
    将资源关联到分类
    
    参数:
        db: 数据库会话
        resources: 资源列表
        code_to_id: 分类代码到ID的映射
        max_classes_per_resource: 每个资源最多关联的分类数
    """
    print("=" * 60)
    print("开始关联资源到分类")
    print("=" * 60)
    
    # 获取所有分类ID
    class_codes = list(code_to_id.keys())
    
    print(f"将 {len(resources)} 个资源关联到分类...")
    
    mappings_created = 0
    
    for i, resource in enumerate(resources):
        # 首先，确保资源有cnl_class_no字段
        if not resource.cnl_class_no:
            print(f"警告: 资源ID={resource.id} 没有设置cnl_class_no字段，跳过")
            continue
        
        # 获取主要分类ID
        primary_class_code = resource.cnl_class_no
        if primary_class_code not in code_to_id:
            print(f"警告: 资源ID={resource.id} 的分类代码 '{primary_class_code}' 不存在，跳过")
            continue
        
        primary_class_id = code_to_id[primary_class_code]
        
        # 创建主要分类关联
        primary_mapping = models.ResourceClassMap(
            resource_id=resource.id,
            class_id=primary_class_id,
            is_primary=1  # 主要分类
        )
        db.add(primary_mapping)
        mappings_created += 1
        
        # 可能添加额外的次要分类（0到max_classes_per_resource-1个）
        num_extra_classes = random.randint(0, max_classes_per_resource - 1)
        if num_extra_classes > 0:
            # 排除主要分类代码
            available_codes = [code for code in class_codes if code != primary_class_code]
            if available_codes:
                # 随机选择额外的分类
                selected_codes = random.sample(
                    available_codes,
                    min(num_extra_classes, len(available_codes))
                )
                
                for extra_code in selected_codes:
                    if extra_code in code_to_id:
                        extra_mapping = models.ResourceClassMap(
                            resource_id=resource.id,
                            class_id=code_to_id[extra_code],
                            is_primary=0  # 次要分类
                        )
                        db.add(extra_mapping)
                        mappings_created += 1
        
        # 每100个资源提交一次
        if i % 100 == 0 and i > 0:
            db.commit()
            print(f"  已处理 {i}/{len(resources)} 个资源，创建了 {mappings_created} 个关联...")
    
    db.commit()
    print("资源分类关联完成！")
    
    # 统计关联情况
    total_mappings = db.query(models.ResourceClassMap).count()
    print(f"共创建 {total_mappings} 个资源-分类关联")
    
    # 验证关联
    resources_without_mappings = db.query(models.Resource).filter(
        ~models.Resource.id.in_(
            db.query(models.ResourceClassMap.resource_id)
        )
    ).count()
    
    if resources_without_mappings > 0:
        print(f"警告: 有 {resources_without_mappings} 个资源没有分类关联")


def validate_database_state(db: Session):
    """
    验证数据库状态
    
    参数:
        db: 数据库会话
    """
    print("=" * 60)
    print("验证数据库状态")
    print("=" * 60)
    
    # 统计分类数量
    class_count = db.query(models.CnlClass).count()
    print(f"1. 分类数量: {class_count}")
    
    # 统计资源数量
    resource_count = db.query(models.Resource).count()
    print(f"2. 资源数量: {resource_count}")
    
    # 统计关联数量
    mapping_count = db.query(models.ResourceClassMap).count()
    print(f"3. 资源-分类关联数量: {mapping_count}")
    
    # 检查分类层级
    level_stats = db.query(
        models.CnlClass.level,
        func.count(models.CnlClass.id).label('count')
    ).group_by(models.CnlClass.level).order_by(models.CnlClass.level).all()
    
    print("4. 分类层级分布:")
    for level, count in level_stats:
        print(f"   层级 {level}: {count} 个分类")
    
    # 检查没有父分类的分类（应该是顶级分类）
    top_level_classes = db.query(models.CnlClass).filter(models.CnlClass.parent_id.is_(None)).all()
    print(f"5. 顶级分类数量: {len(top_level_classes)}")
    
    # 检查资源关联情况
    resources_without_classes = db.query(models.Resource).filter(
        ~models.Resource.id.in_(
            db.query(models.ResourceClassMap.resource_id)
        )
    ).count()
    
    print(f"6. 未关联分类的资源数量: {resources_without_classes}")
    
    if resources_without_classes > 0:
        print("  警告: 存在未关联分类的资源")
    
    # 检查分类使用情况
    classes_without_resources = db.query(models.CnlClass).filter(
        ~models.CnlClass.id.in_(
            db.query(models.ResourceClassMap.class_id)
        )
    ).count()
    
    print(f"7. 未关联资源的分类数量: {classes_without_resources}")
    
    if class_count > 0:
        usage_rate = (class_count - classes_without_resources) / class_count * 100
        print(f"   分类使用率: {usage_rate:.1f}%")
    
    print("数据库验证完成！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='使用clc.json更新数据库并创建虚拟数据')
    
    parser.add_argument('--clear-classes', action='store_true', default=True,
                       help='清空现有分类数据（默认: True）')
    parser.add_argument('--no-clear-classes', dest='clear_classes', action='store_false',
                       help='不清空现有分类数据')
    
    parser.add_argument('--clear-resources', action='store_true', default=False,
                       help='清空现有资源数据（默认: False）')
    parser.add_argument('--no-clear-resources', dest='clear_resources', action='store_false',
                       help='不清空现有资源数据')
    
    parser.add_argument('--num-resources', type=int, default=1000,
                       help='要创建的虚拟资源数量（默认: 1000）')
    
    parser.add_argument('--skip-resources', action='store_true', default=False,
                       help='跳过资源创建（只导入分类）')
    
    parser.add_argument('--skip-associations', action='store_true', default=False,
                       help='跳过资源分类关联')
    
    parser.add_argument('--validate-only', action='store_true', default=False,
                       help='只验证数据库状态，不进行任何更新')
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        if args.validate_only:
            print("只验证数据库状态...")
            validate_database_state(db)
            return
        
        # 如果需要清空资源数据
        if args.clear_resources:
            print("清空现有资源数据...")
            db.query(models.ResourceClassMap).delete()
            db.query(models.Resource).delete()
            db.commit()
            print("资源数据已清空")
        
        # 导入分类数据
        code_to_id = import_clc_classifications(db, clear_existing=args.clear_classes)
        
        if args.skip_resources:
            print("跳过资源创建...")
        else:
            # 创建虚拟资源
            resources = create_virtual_resources(db, args.num_resources, code_to_id)
            
            if args.skip_associations:
                print("跳过资源分类关联...")
            else:
                # 关联资源到分类
                associate_resources_with_classes(db, resources, code_to_id)
        
        # 验证数据库状态
        validate_database_state(db)
        
        print("\n" + "=" * 60)
        print("数据库更新完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()