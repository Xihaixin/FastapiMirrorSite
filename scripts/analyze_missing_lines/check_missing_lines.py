#!/usr/bin/env python3
"""检查缺失的行"""

def find_missing_lines():
    missing_nums = [719, 720, 852, 853, 854, 880, 881]
    
    with open('海纳中图分类.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"文件总行数: {len(lines)}")
    
    # 检查每行的序号
    found_nums = []
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line and ':' in line:
            parts = line.split(':')
            if parts[0].strip().isdigit():
                num = int(parts[0].strip())
                found_nums.append(num)
                
                if num in missing_nums:
                    print(f"\n找到缺失的序号 {num} 在第 {i} 行:")
                    print(f"  内容: {line}")
    
    # 检查哪些缺失的序号确实不在文件中
    print(f"\n缺失的序号分析:")
    for num in missing_nums:
        if num not in found_nums:
            print(f"  序号 {num}: 确实不在文件中")
        else:
            print(f"  序号 {num}: 在文件中找到")
    
    # 检查文件中的最大序号
    if found_nums:
        print(f"\n文件中的最大序号: {max(found_nums)}")
        print(f"文件中的最小序号: {min(found_nums)}")
        print(f"找到的序号数量: {len(found_nums)}")
        
        # 检查序号连续性
        expected = list(range(min(found_nums), max(found_nums) + 1))
        actually_missing = [n for n in expected if n not in found_nums]
        
        print(f"\n实际缺失的序号 ({len(actually_missing)} 个): {actually_missing}")

if __name__ == "__main__":
    find_missing_lines()