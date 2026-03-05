#!/usr/bin/env python3
"""
改进权重分配方案
基于学科重要性和分类层级设计更合理的权重
"""

import json
from typing import Dict, List, Tuple


def load_class_defs() -> List[Tuple[str, str, str, int]]:
    """从生成的文件加载分类定义"""
    class_defs = []
    
    # 读取生成的文件
    with open("scripts/cnl_class_defs.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # 找到CLASS_DEFS开始和结束的位置
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if "CLASS_DEFS = [" in line:
            start_idx = i + 1
        if start_idx != -1 and "]" in line and "GEN_CLASS_WEIGHTS" not in line:
            end_idx = i
            break
    
    if start_idx == -1 or end_idx == -1:
        print("错误: 无法找到CLASS_DEFS定义")
        return []
    
    # 解析CLASS_DEFS
    for i in range(start_idx, end_idx):
        line = lines[i].strip()
        if line.startswith("(") and line.endswith("),"):
            # 移除括号和逗号
            content = line[1:-2]
            parts = content.split(", ")
            if len(parts) >= 4:
                code = parts[0].strip('"')
                name = parts[1].strip('"')
                parent = parts[2].strip('"') if parts[2] != "None" else None
                level = int(parts[3])
                class_defs.append((code, name, parent, level))
    
    return class_defs


def calculate_improved_weights(class_defs: List[Tuple[str, str, str, int]]) -> Dict[str, int]:
    """计算改进的权重分配"""
    weights = {}
    
    # 学科重要性映射
    subject_importance = {
        # 计算机科学与技术 (高重要性)
        "TP": 10,  # 自动化技术、计算机技术
        "TN": 8,   # 无线电电子学、电信技术
        "TM": 7,   # 电工技术
        
        # 经济与管理 (高重要性)
        "F": 9,    # 经济
        "C": 8,    # 社会科学总论
        
        # 医学与健康 (高重要性)
        "R": 9,    # 医药、卫生
        
        # 工程与技术 (中高重要性)
        "T": 7,    # 工业技术
        "U": 6,    # 交通运输
        "V": 5,    # 航空、航天
        
        # 自然科学 (中重要性)
        "O": 7,    # 数理科学和化学
        "P": 6,    # 天文学、地球科学
        "Q": 6,    # 生物科学
        "N": 5,    # 自然科学总论
        
        # 人文社科 (中重要性)
        "B": 6,    # 哲学、宗教
        "D": 6,    # 政治、法律
        "G": 5,    # 文化、科学、教育、体育
        "H": 5,    # 语言、文字
        "I": 5,    # 文学
        "J": 5,    # 艺术
        "K": 5,    # 历史、地理
        
        # 农业与环境 (中重要性)
        "S": 5,    # 农业科学
        "X": 5,    # 环境科学、安全科学
        
        # 其他 (低重要性)
        "A": 3,    # 马克思主义、列宁主义等
        "Z": 3,    # 综合性图书
        "E": 4,    # 军事
    }
    
    # 热门细分领域额外加成
    hot_fields = {
        "TP3": 15,     # 计算技术、计算机技术
        "TP31": 20,    # 计算机软件
        "TP39": 18,    # 计算机的应用
        "F27": 12,     # 企业经济
        "F71": 10,     # 国内贸易经济
        "F83": 10,     # 金融、银行
        "R4": 12,      # 临床医学
        "R5": 11,      # 内科学
        "O1": 9,       # 数学
        "O4": 8,       # 物理学
        "G64": 9,      # 高等教育
        "H31": 8,      # 英语
    }
    
    for code, name, parent, level in class_defs:
        base_weight = 1
        
        # 1. 根据层级调整权重（层级越深，权重越低）
        if level == 1:
            base_weight = 10
        elif level == 2:
            base_weight = 6
        elif level == 3:
            base_weight = 3
        elif level == 4:
            base_weight = 2
        else:
            base_weight = 1
        
        # 2. 根据学科重要性调整
        first_letter = code[0]
        if first_letter in subject_importance:
            base_weight *= subject_importance[first_letter] / 5  # 归一化到合理范围
        
        # 3. 热门领域额外加成
        for hot_prefix, bonus in hot_fields.items():
            if code.startswith(hot_prefix):
                base_weight *= bonus / 10
                break
        
        # 4. 根据名称关键词调整
        important_keywords = ["计算机", "网络", "软件", "数据", "人工智能", "机器学习", 
                             "经济", "金融", "管理", "市场", "医学", "健康", "教育",
                             "数学", "物理", "化学", "生物", "工程", "技术", "设计"]
        
        for keyword in important_keywords:
            if keyword in name:
                base_weight *= 1.2
                break
        
        # 确保权重至少为1
        final_weight = max(1, int(base_weight))
        weights[code] = final_weight
    
    # 归一化处理，使总权重在合理范围内
    total_weight = sum(weights.values())
    target_total = 5000  # 比之前更大，因为分类更多
    
    if total_weight > 0:
        scale_factor = target_total / total_weight
        for code in weights:
            weights[code] = max(1, int(weights[code] * scale_factor))
    
    return weights


def analyze_weight_distribution(weights: Dict[str, int], class_defs: List[Tuple[str, str, str, int]]):
    """分析权重分布"""
    print("\n=== 权重分布分析 ===")
    
    # 按权重排序
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    
    print(f"总分类数: {len(weights)}")
    print(f"总权重: {sum(weights.values())}")
    print(f"平均权重: {sum(weights.values()) / len(weights):.2f}")
    
    # 按层级统计
    level_stats = {}
    for code, weight in weights.items():
        # 找到对应的分类
        for cls_code, name, parent, level in class_defs:
            if cls_code == code:
                if level not in level_stats:
                    level_stats[level] = {"count": 0, "total_weight": 0}
                level_stats[level]["count"] += 1
                level_stats[level]["total_weight"] += weight
                break
    
    print("\n按层级统计:")
    for level in sorted(level_stats.keys()):
        stats = level_stats[level]
        avg = stats["total_weight"] / stats["count"] if stats["count"] > 0 else 0
        print(f"层级 {level}: {stats['count']} 个分类, 总权重 {stats['total_weight']}, 平均权重 {avg:.2f}")
    
    # 按学科统计
    subject_stats = {}
    for code, weight in weights.items():
        subject = code[0]
        if subject not in subject_stats:
            subject_stats[subject] = {"count": 0, "total_weight": 0}
        subject_stats[subject]["count"] += 1
        subject_stats[subject]["total_weight"] += weight
    
    print("\n按学科统计 (前10):")
    sorted_subjects = sorted(subject_stats.items(), key=lambda x: x[1]["total_weight"], reverse=True)
    for subject, stats in sorted_subjects[:10]:
        avg = stats["total_weight"] / stats["count"] if stats["count"] > 0 else 0
        print(f"{subject}: {stats['count']} 个分类, 总权重 {stats['total_weight']}, 平均权重 {avg:.2f}")
    
    # 显示权重最高的20个分类
    print("\n权重最高的20个分类:")
    for i, (code, weight) in enumerate(sorted_weights[:20]):
        # 找到分类名称
        name = ""
        for cls_code, cls_name, parent, level in class_defs:
            if cls_code == code:
                name = cls_name
                break
        print(f"{i+1:2d}. {code:10s} (权重: {weight:3d}) - {name}")
    
    # 显示权重最低的10个分类
    print("\n权重最低的10个分类:")
    for i, (code, weight) in enumerate(sorted_weights[-10:]):
        # 找到分类名称
        name = ""
        for cls_code, cls_name, parent, level in class_defs:
            if cls_code == code:
                name = cls_name
                break
        print(f"{i+1:2d}. {code:10s} (权重: {weight:3d}) - {name}")


def save_improved_weights(weights: Dict[str, int], class_defs: List[Tuple[str, str, str, int]]):
    """保存改进的权重到文件"""
    
    # 读取原始文件
    with open("scripts/cnl_class_defs.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # 找到GEN_CLASS_WEIGHTS开始和结束的位置
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if "GEN_CLASS_WEIGHTS = {" in line:
            start_idx = i
        if start_idx != -1 and line.strip() == "}":
            end_idx = i
            break
    
    if start_idx == -1 or end_idx == -1:
        print("错误: 无法找到GEN_CLASS_WEIGHTS定义")
        return
    
    # 创建新的权重部分
    new_weights_lines = []
    new_weights_lines.append("GEN_CLASS_WEIGHTS = {\n")
    
    # 按权重排序并保存
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    for code, weight in sorted_weights:
        new_weights_lines.append(f'    "{code}": {weight},\n')
    
    new_weights_lines.append("}\n")
    
    # 替换文件中的权重部分
    new_lines = lines[:start_idx] + new_weights_lines + lines[end_idx + 1:]
    
    # 保存到新文件
    with open("scripts/cnl_class_defs_improved.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print(f"\n改进的权重已保存到 scripts/cnl_class_defs_improved.py")
    print(f"共 {len(weights)} 个分类的权重")


def main():
    """主函数"""
    print("加载分类定义...")
    class_defs = load_class_defs()
    
    if not class_defs:
        print("错误: 无法加载分类定义")
        return
    
    print(f"成功加载 {len(class_defs)} 个分类定义")
    
    print("\n计算改进的权重分配...")
    weights = calculate_improved_weights(class_defs)
    
    print(f"生成 {len(weights)} 个权重分配")
    
    # 分析权重分布
    analyze_weight_distribution(weights, class_defs)
    
    # 保存改进的权重
    save_improved_weights(weights, class_defs)
    
    # 生成用于seed_data.py的简化权重（只包含常用分类）
    print("\n生成简化权重（用于资源生成）...")
    simplified_weights = {}
    
    # 选择权重较高的分类
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    top_count = 200  # 选择前200个权重最高的分类
    
    for code, weight in sorted_weights[:top_count]:
        simplified_weights[code] = weight
    
    # 保存简化权重
    with open("scripts/simplified_weights.json", "w", encoding="utf-8") as f:
        json.dump(simplified_weights, f, ensure_ascii=False, indent=2)
    
    print(f"简化权重已保存到 scripts/simplified_weights.json")
    print(f"包含 {len(simplified_weights)} 个常用分类")


if __name__ == "__main__":
    main()