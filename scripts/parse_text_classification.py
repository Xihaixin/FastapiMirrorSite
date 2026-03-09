
#!/usr/bin/env python3
"""
海纳中图分类文件解析器
用于解析"海纳中图分类.txt"文件，生成数据库可用的分类数据
"""

import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class Classification:
    """分类条目"""
    line_no: int
    code: str
    name: str
    level: int = 1
    parent_code: Optional[str] = None
    path: Optional[str] = None


class CNLClassificationParser:
    """中图分类解析器"""
    
    def __init__(self, file_path: str = "海纳中图分类.txt"):
        """
        初始化中图分类器，维护一个“图书分类条目”列表和“图书分类代码”列表

        参数：
            file_path: str = "海纳中图分类.txt"

        属性值：
            file_path: str -> 待处理的中图分类标准
            classifications: List[Classification] -> “图书分类条目”列表
            code_to_class: Dict[str, Classification] -> “图书分类代码”列表
            cannot_match_lines: List[str] -> “无法被正则表达式匹配到的行”

        返回值：
            “中图分类解析器”实例
        
        """
        self.file_path = file_path
        self.classifications: List[Classification] = []
        self.code_to_class: Dict[str, Classification] = {}
        self.cannot_match_lines: List[str] = []
        
    def parse_line(self, line: str, line_no: int) -> Optional[Classification]:
        """解析单行分类数据，返回一个 Classification （图书分类条目）数据对象的实例"""
        # 格式示例: "   1 : A = 马克思主义、列宁主义、毛泽东思想、邓小平理论"
        line = line.strip()
        if not line:
            return None
            
        # 使用正则表达式匹配格式
        pattern = r'^\s*(\d+)\s*:\s*([A-Z][A-Z0-9._\-]*)\s*=\s*(.+)$'
        match = re.match(pattern, line)
        
        if not match:
            # 尝试其他格式
            pattern2 = r'^\s*(\d+)\s*:\s*([A-Z][A-Z0-9._\-]*)\s+(.+)$'
            match = re.match(pattern2, line)
            if not match:
                print(f"警告: 第{line_no}行无法解析: {line[:50]}...")
                self.cannot_match_lines.append(line)
                return None
        
        line_num = int(match.group(1))
        code = match.group(2)
        name = match.group(3).strip()
        
        return Classification(
            line_no=line_num,
            code=code,
            name=name
        )
    
    def infer_hierarchy(self):
        """推断分类的层级关系"""
        for cls in self.classifications:
            # 推断层级
            cls.level = self._calculate_level(cls.code)
            
            # 推断父分类代码
            cls.parent_code = self._infer_parent_code(cls.code)
            
            # 计算路径
            if cls.parent_code and cls.parent_code in self.code_to_class:
                parent = self.code_to_class[cls.parent_code]
                cls.path = f"{parent.path}/{cls.code}" if parent.path else cls.code
            else:
                cls.path = cls.code
    
    def _calculate_level(self, code: str) -> int:
        """根据分类代码计算层级"""
        # 一级分类: 单个字母
        if len(code) == 1 and code.isalpha():
            return 1
        
        # 二级分类: 字母+数字 (如B0, B5)
        if len(code) == 2 and code[0].isalpha() and code[1].isdigit():
            return 2
        
        # 三级分类: 包含分隔符或更多字符
        if '-' in code:
            # 如B0-0, B0-02
            return 3
        
        # 更复杂的分类代码
        if len(code) > 2:
            # 检查是否包含小数点
            if '.' in code:
                return 4
            # 检查是否包含下划线
            if '_' in code:
                return 3
            # 默认三级
            return 3
        
        return 1
    
    def _infer_parent_code(self, code: str) -> Optional[str]:
        """根据分类代码推断父分类代码"""
        # 一级分类没有父类
        if len(code) == 1 and code.isalpha():
            return None
        
        # 处理包含分隔符的代码
        if '-' in code:
            # 如B0-0的父类是B0
            base_part = code.split('-')[0]
            # 检查base_part是否存在
            if base_part in self.code_to_class:
                return base_part
            # 如果base_part不存在，尝试进一步推断
            if len(base_part) > 1:
                return self._infer_parent_code(base_part)
            return None
        
        # 处理包含小数点的代码
        if '.' in code:
            # 如B109.2的父类是B109
            base_part = code.split('.')[0]
            if base_part in self.code_to_class:
                return base_part
            return self._infer_parent_code(base_part)
        
        # 处理包含下划线的代码
        if '_' in code:
            # 如B31_39的父类是B3
            base_part = code.split('_')[0]
            if base_part in self.code_to_class:
                return base_part
            return self._infer_parent_code(base_part)
        
        # 普通代码: 逐步减少最后一位
        for i in range(len(code) - 1, 0, -1):
            parent_candidate = code[:i]
            if parent_candidate in self.code_to_class:
                return parent_candidate
        
        # 如果找不到明确的父类，返回一级分类
        if code[0] in self.code_to_class:
            return code[0]
        
        return None
    
    def parse_file(self):
        """解析整个文件"""
        print(f"开始解析文件: {self.file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_no, line in enumerate(lines, 1):
            cls = self.parse_line(line, line_no)
            if cls:
                self.classifications.append(cls)
                self.code_to_class[cls.code] = cls
        
        print(f"解析完成，共读取到{len(lines)} |> 找到 {len(self.classifications)} 个分类")
        
        # 推断层级关系
        self.infer_hierarchy()
        
        # 验证层级关系
        self.validate_hierarchy()
    
    def validate_hierarchy(self):
        """验证层级关系的正确性"""
        errors = []
        
        for cls in self.classifications:
            if cls.parent_code and cls.parent_code not in self.code_to_class:
                errors.append(f"分类 {cls.code} 的父类 {cls.parent_code} 不存在")
            
            if cls.level < 1 or cls.level > 5:
                errors.append(f"分类 {cls.code} 的层级 {cls.level} 超出合理范围")
        
        if errors:
            print(f"发现 {len(errors)} 个错误:")
            for error in errors[:10]:  # 只显示前10个错误
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... 还有 {len(errors) - 10} 个错误未显示")
        else:
            print("层级关系验证通过")
    
    def generate_class_defs(self) -> List[Tuple[str, str, Optional[str], int]]:
        """生成CLASS_DEFS格式的数据"""
        class_defs = []
        
        for cls in sorted(self.classifications, key=lambda x: x.line_no):
            class_defs.append((cls.code, cls.name, cls.parent_code, cls.level))
        
        return class_defs
    
    def generate_sql_inserts(self) -> List[str]:
        """生成SQL插入语句"""
        sql_statements = []
        
        for cls in sorted(self.classifications, key=lambda x: x.line_no):
            parent_id = "NULL"
            if cls.parent_code and cls.parent_code in self.code_to_class:
                # 注意：这里需要在实际插入时获取父类的ID
                parent_id = f"(SELECT id FROM cnl_classes WHERE code = '{cls.parent_code}')"
            
            # 转义单引号
            escaped_name = cls.name.replace("'", "''")
            sql = f"INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('{cls.code}', '{escaped_name}', {parent_id}, {cls.level}, '{cls.path}');"
            sql_statements.append(sql)
        
        return sql_statements
    
    def generate_weight_distribution(self) -> Dict[str, int]:
        """生成权重分配方案"""
        weights = {}
        
        # 基于分类层级和学科重要性分配权重
        for cls in self.classifications:
            base_weight = 1
            
            # 根据层级调整权重（层级越深，权重越低）
            if cls.level == 1:
                base_weight = 10
            elif cls.level == 2:
                base_weight = 5
            elif cls.level == 3:
                base_weight = 3
            elif cls.level == 4:
                base_weight = 2
            else:
                base_weight = 1
            
            # 根据学科重要性调整权重
            # 常用学科：计算机科学、经济、医学等
            if cls.code.startswith(('TP', 'F', 'R')):
                base_weight *= 2
            # 基础学科：数学、物理、化学
            elif cls.code.startswith(('O1', 'O4', 'O6')):
                base_weight *= 1.5
            # 人文社科
            elif cls.code.startswith(('B', 'C', 'D', 'G', 'H', 'I', 'J', 'K')):
                base_weight *= 1.2
            
            weights[cls.code] = int(base_weight)
        
        # 归一化，使总权重在合理范围内
        total_weight = sum(weights.values())
        target_total = 1000
        
        if total_weight > 0:
            scale_factor = target_total / total_weight
            for code in weights:
                weights[code] = max(1, int(weights[code] * scale_factor))
        
        return weights
    
    def print_statistics(self):
        """打印统计信息"""
        print("\n=== 分类统计信息 ===")
        print(f"总分类数: {len(self.classifications)}")
        
        level_counts = {}
        for cls in self.classifications:
            level_counts[cls.level] = level_counts.get(cls.level, 0) + 1
        
        for level in sorted(level_counts.keys()):
            print(f"层级 {level}: {level_counts[level]} 个分类")
        
        # 按字母分类统计
        letter_counts = {}
        for cls in self.classifications:
            letter = cls.code[0]
            letter_counts[letter] = letter_counts.get(letter, 0) + 1
        
        print("\n按字母分类统计:")
        for letter in sorted(letter_counts.keys()):
            print(f"  {letter}: {letter_counts[letter]} 个分类")
        
        # 显示一些示例
        print("\n=== 分类示例 ===")
        for i, cls in enumerate(self.classifications[:10]):
            print(f"{cls.line_no:4d}: {cls.code:10s} (L{cls.level}) - {cls.name}")
            if cls.parent_code:
                print(f"      父类: {cls.parent_code}, 路径: {cls.path}")


def main():
    """主函数"""
    parser = CNLClassificationParser("海纳中图分类.txt")
    
    try:
        parser.parse_file()
        parser.print_statistics()
        cannot_match_lines_ls = "\n".join(parser.cannot_match_lines)
        # 生成CLASS_DEFS
        class_defs = parser.generate_class_defs()
        print(f"\n生成的CLASS_DEFS包含 {len(class_defs)} 个条目")
        print(f"无法匹配的分类条目如下所示：\n{cannot_match_lines_ls}")
        
        # 生成权重分配
        weights = parser.generate_weight_distribution()
        print(f"生成的权重分配包含 {len(weights)} 个条目")
        print(f"总权重: {sum(weights.values())}")
        
        # 保存结果到文件
        with open("scripts/cnl_class_defs.py", "w", encoding="utf-8") as f:
            f.write("# 自动生成的中图分类定义\n")
            f.write("# 来源: 海纳中图分类.txt\n")
            f.write(f"# 生成时间: {__import__('datetime').datetime.now()}\n\n")
            f.write("CLASS_DEFS = [\n")
            for code, name, parent_code, level in class_defs:
                parent_str = f"'{parent_code}'" if parent_code else "None"
                f.write(f"    (\"{code}\", \"{name}\", {parent_str}, {level}),\n")
            f.write("]\n\n")
            
            f.write("GEN_CLASS_WEIGHTS = {\n")
            for code, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True)[:100]:  # 只保存前100个
                f.write(f"    \"{code}\": {weight},\n")
            f.write("}\n")
        
        print("\n结果已保存到 scripts/cnl_class_defs.py")
        
        # 生成SQL文件
        with open("scripts/cnl_classes.sql", "w", encoding="utf-8") as f:
            f.write("-- 中图分类SQL插入语句\n")
            f.write("-- 来源: 海纳中图分类.txt\n\n")
            f.write("BEGIN TRANSACTION;\n\n")
            f.write("-- 清空现有数据\n")
            f.write("DELETE FROM resource_class_map;\n")
            f.write("DELETE FROM resources;\n")
            f.write("DELETE FROM cnl_classes;\n\n")
            
            f.write("-- 插入分类数据\n")
            sql_statements = parser.generate_sql_inserts()
            for sql in sql_statements[:50]:  # 只保存前50条作为示例
                f.write(sql + "\n")
            
            f.write("\nCOMMIT;\n")
        
        print("SQL示例已保存到 scripts/cnl_classes.sql")
        
    except FileNotFoundError:
        print(f"错误: 文件 {parser.file_path} 不存在")
        print("请确保文件在当前目录下")
    except Exception as e:
        print(f"解析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()