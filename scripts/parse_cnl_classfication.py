
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


class CNLClassification:
    """中图分类解析器"""
    
    def __init__(self, file_path: str = "./scripts/海纳中图分类.txt"):
        """
        初始化中图分类器，维护一个“图书分类条目”列表和“图书分类代码”列表

        参数：
            file_path: str = "./scripts/海纳中图分类.txt"

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
        
    def parse_line(self, line: str, line_no: int) -> Optional[Classification]:
        """解析单行分类数据，返回一个 Classification （图书分类条目）数据对象的实例"""
        # 格式示例: "   1 : A = 马克思主义、列宁主义、毛泽东思想、邓小平理论"
        line = line.strip()
        if not line:
            return None
            
        # 使用正则表达式匹配格式: \s 表示匹配空白字符的匹配
        pattern = r'^\s*(\d+)\s*:\s*([A-Z][A-Z0-9._\-]*)\s*=\s*(.+)$'
        match = re.match(pattern, line)
        
        if not match:
            # 尝试其他格式
            pattern2 = r'^\s*(\d+)\s*:\s*([A-Z][A-Z0-9._\-]*)\s+(.+)$'
            match = re.match(pattern2, line)
            if not match:
                print(f"警告: 第{line_no}行无法解析: {line[:50]}...")
                return None
        
        line_num = int(match.group(1))
        code = match.group(2)
        name = match.group(3).strip()
        
        return Classification(
            line_no=line_num,
            code=code,
            name=name
        )
        

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
        
        
    
def main():
    """主函数"""
    filter = CNLClassification("海纳中图分类.txt")
    
    try:
        filter.parse_file()
            
    except FileNotFoundError:
        print(f"错误: 文件 {filter.file_path} 不存在")
        print("请确保文件在当前目录下")
    except Exception as e:
        print(f"解析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

    # ---------------------------------------------------------------------------
    import re

    import json

    def parse_line(line):
        """解析单行，返回 (分类号, 名称) 或 (None, None)"""
        pattern = r'^\s*\d+\s*:\s*(\S+)\s*=\s*(.+)$'
        match = re.match(pattern, line)
        if match:
            code = match.group(1).strip()
            name = match.group(2).strip()
            return code, name
        return None, None

    def is_normal(code):
        """判断分类号是否符合正常规则（1-2字母 + 0或多个数字）"""
        return bool(re.fullmatch(r'^[A-Z]{1,2}\d*$', code))

    def process_file(file_path):
        data = {}
        entries = []          # 保存所有 (code, name)
        first_letters = set() # 收集出现的首字母

        # 第一遍：收集所有条目和首字母
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                code, name = parse_line(line)
                if code:
                    entries.append((code, name))
                    if code and code[0].isalpha():
                        first_letters.add(code[0])

        # 为每个首字母初始化结构
        for letter in first_letters:
            data[letter] = {
                "name": "",
                "normal": {},
                "filter": {}
            }

        # 第二遍：分类处理
        for code, name in entries:
            first = code[0]
            if first not in data:
                continue  # 安全保护，理论上不会发生

            # 如果是纯单字母，设置为该大类的名称
            if re.fullmatch(r'^[A-Z]$', code):
                data[first]["name"] = name

            # 根据规则放入 normal 或 filter
            if is_normal(code):
                data[first]["normal"][code] = name
            else:
                data[first]["filter"][code] = name

        return data

    def save_json(data, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    if __name__ == "__main__":
        input_file = "你的文件.txt"   # 替换为实际路径
        output_file = "output.json"
        result = process_file(input_file)
        save_json(result, output_file)
        print(f"处理完成，结果已保存至 {output_file}")