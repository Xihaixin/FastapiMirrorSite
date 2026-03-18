#!/usr/bin/env python3
"""
clc.json解析器
用于解析scripts/get_cnl_classification/clc.json文件，生成数据库可用的分类数据

clc.json是一个结构化的JSON文件，包含完整的中图分类层级关系。
与"海纳中图分类.txt"不同，clc.json具有明确的层级结构，无需复杂解析。
"""

import json
import sys
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Classification:
    """分类条目"""
    code: str
    name: str
    parent_code: Optional[str] = None
    level: int = 1
    path: Optional[str] = None


class CLCJsonParser:
    """clc.json解析器"""
    
    def __init__(self, file_path: str = "scripts/get_cnl_classification/clc.json"):
        """
        初始化clc.json解析器
        
        参数:
            file_path: clc.json文件路径
        """
        self.file_path = Path(file_path)
        self.classifications: List[Classification] = []
        self.code_to_class: Dict[str, Classification] = {}
        
    def parse_file(self) -> List[Classification]:
        """
        解析clc.json文件
        
        返回:
            分类列表
        """
        print(f"开始解析文件: {self.file_path}")
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
        
        # 读取JSON文件
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 递归解析JSON数据
        self._parse_recursive(data, parent_code=None, level=1)
        
        print(f"解析完成，共找到 {len(self.classifications)} 个分类")
        
        # 计算路径
        self._calculate_paths()
        
        return self.classifications
    
    def _parse_recursive(self, items: List[Dict], parent_code: Optional[str], level: int):
        """
        递归解析JSON数据
        
        参数:
            items: JSON数据项列表
            parent_code: 父分类代码
            level: 当前层级
        """
        for item in items:
            code = item.get('id', '').strip()
            name = item.get('desc', '').strip()
            
            if not code or not name:
                print(f"警告: 跳过无效的分类项: {item}")
                continue
            
            # 创建分类对象
            cls = Classification(
                code=code,
                name=name,
                parent_code=parent_code,
                level=level
            )
            
            # 添加到列表和映射
            self.classifications.append(cls)
            self.code_to_class[code] = cls
            
            # 递归处理子分类
            children = item.get('children', [])
            if children:
                self._parse_recursive(children, parent_code=code, level=level + 1)
    
    def _calculate_paths(self):
        """计算每个分类的路径"""
        for cls in self.classifications:
            path_parts = []
            current = cls
            
            # 向上追溯构建路径
            while current:
                path_parts.insert(0, current.code)
                if current.parent_code and current.parent_code in self.code_to_class:
                    current = self.code_to_class[current.parent_code]
                else:
                    break
            
            cls.path = '/'.join(path_parts)
    
    def validate_hierarchy(self) -> List[str]:
        """
        验证层级关系的正确性
        
        返回:
            错误消息列表
        """
        errors = []
        
        for cls in self.classifications:
            # 检查父分类是否存在
            if cls.parent_code and cls.parent_code not in self.code_to_class:
                errors.append(f"分类 {cls.code} 的父类 {cls.parent_code} 不存在")
            
            # 检查层级范围
            if cls.level < 1 or cls.level > 6:
                errors.append(f"分类 {cls.code} 的层级 {cls.level} 超出合理范围")
            
            # 检查路径格式
            if not cls.path or cls.code not in cls.path:
                errors.append(f"分类 {cls.code} 的路径 {cls.path} 格式错误")
        
        return errors
    
    def generate_class_defs(self) -> List[Tuple[str, str, Optional[str], int]]:
        """
        生成CLASS_DEFS格式的数据
        
        返回:
            (code, name, parent_code, level) 元组列表
        """
        class_defs = []
        for cls in self.classifications:
            class_defs.append((cls.code, cls.name, cls.parent_code, cls.level))
        
        return class_defs
    
    def save_to_file(self, output_path: str):
        """
        将解析结果保存到文件
        
        参数:
            output_path: 输出文件路径
        """
        class_defs = self.generate_class_defs()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 从clc.json解析出的中图分类定义\n")
            f.write("# 格式: (code, name, parent_code, level)\n")
            f.write("CLASS_DEFS = [\n")
            
            for i, (code, name, parent_code, level) in enumerate(class_defs):
                parent_str = f"'{parent_code}'" if parent_code else "None"
                line = f"    (\"{code}\", \"{name}\", {parent_str}, {level})"
                if i < len(class_defs) - 1:
                    line += ","
                f.write(line + "\n")
            
            f.write("]\n")
        
        print(f"结果已保存到: {output_path}")


def main():
    """主函数"""
    parser = CLCJsonParser()
    
    try:
        # 解析文件
        classifications = parser.parse_file()
        
        # 验证层级关系
        errors = parser.validate_hierarchy()
        if errors:
            print(f"发现 {len(errors)} 个错误:")
            for error in errors[:10]:  # 只显示前10个错误
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... 还有 {len(errors) - 10} 个错误")
        else:
            print("层级关系验证通过")
        
        # 统计信息
        level_counts = {}
        for cls in classifications:
            level_counts[cls.level] = level_counts.get(cls.level, 0) + 1
        
        print("\n分类统计:")
        for level in sorted(level_counts.keys()):
            print(f"  层级 {level}: {level_counts[level]} 个分类")
        
        # 保存到文件
        output_path = "scripts/parsed_clc_classifications.py"
        parser.save_to_file(output_path)
          
    except Exception as e:
        print(f"解析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()