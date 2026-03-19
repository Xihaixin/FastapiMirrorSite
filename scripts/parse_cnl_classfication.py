
#!/usr/bin/env python3
"""
海纳中图分类文件解析器
用于解析"海纳中图分类.txt"文件，生成数据库可用的分类数据
"""

import re
import json
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
    
    def __init__(self, file_path: str = "./scripts/海纳中图分类.txt", output_path="./scripts/海纳中图分类筛选.json"):
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
        self.first_letters = set()
        self.output_path = output_path
        self.data = {}
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
    def is_normal(self, code):
        """判断分类号是否符合正常规则（1-2字母 + 0或多个数字）"""
        return bool(re.fullmatch(r'^[A-Z]{1,2}\d*$', code))
    

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

                if cls.code[0].isalpha():
                    self.first_letters.add(cls.code[0])
        
        # 为每个首字母初始化结构
        for letter in sorted(self.first_letters, key=lambda x: ord(x)):
            self.data[letter] = {
                "name": "",
                "normal": {},
                "filter": {}
            }
        
        # 第二遍：分类处理
        for code, classification in self.code_to_class.items():
            first = code[0]
            if first not in self.data:
                continue

            if re.fullmatch(r'^[A-Z]$',code):
                self.data[first]["name"] = classification.name

            if self.is_normal(code):
                self.data[first]["normal"][code] = classification.name
            else:
                self.data[first]["filter"][code] = classification.name

        self.save_to_json()
        print(f"文件筛选完成，共读取到{len(lines)} |> 找到 {len(self.classifications)} 个分类 |> 文件已保存到{self.output_path}")
    
    def statistics_analysis(self):
        pass


    def save_to_json(self):
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        

    
def main():
    """主函数"""
    cnl_filter = CNLClassification()
    
    try:
        cnl_filter.parse_file()
            
    except FileNotFoundError:
        print(f"错误: 文件 {cnl_filter.file_path} 不存在")
        print("请确保文件在当前目录下")
    except Exception as e:
        print(f"解析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
