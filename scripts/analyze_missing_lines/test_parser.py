#!/usr/bin/env python3
"""测试解析器"""

import sys
sys.path.append('.')
from scripts.parse_text_classification import CNLClassificationParser

def main():
    parser = CNLClassificationParser("海纳中图分类.txt")
    parser.parse_file()
    
    print(f"\n解析结果:")
    print(f"总分类数: {len(parser.classifications)}")
    print(f"无法匹配的行数: {len(parser.cannot_match_lines)}")
    
    if parser.cannot_match_lines:
        print("\n无法匹配的行:")
        for i, line in enumerate(parser.cannot_match_lines[:10], 1):
            print(f"  {i}: {line}")
        if len(parser.cannot_match_lines) > 10:
            print(f"  ... 还有 {len(parser.cannot_match_lines) - 10} 行")
    else:
        print("所有行都成功匹配")
    
    # 检查序号连续性
    nums = [cls.line_no for cls in parser.classifications]
    nums.sort()
    
    print(f"\n序号分析:")
    print(f"最小序号: {min(nums)}")
    print(f"最大序号: {max(nums)}")
    print(f"序号数量: {len(nums)}")
    
    # 检查缺失的序号
    expected = list(range(1, max(nums) + 1))
    missing = [n for n in expected if n not in nums]
    
    if missing:
        print(f"缺失的序号 ({len(missing)} 个): {missing[:20]}...")
    else:
        print("序号连续，没有缺失")

if __name__ == "__main__":
    main()