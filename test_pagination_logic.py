#!/usr/bin/env python3
"""
测试前端分页编号连续性的逻辑
"""

def calculate_continuous_index(current_page, current_size, idx):
    """计算连续编号的逻辑，与前端代码保持一致"""
    return (current_page - 1) * current_size + idx + 1

def test_pagination_logic():
    """测试分页编号逻辑"""
    test_cases = [
        # (currentPage, currentSize, idx, expected)
        (1, 10, 0, 1),   # 第一页第一个
        (1, 10, 9, 10),  # 第一页最后一个
        (2, 10, 0, 11),  # 第二页第一个
        (2, 10, 9, 20),  # 第二页最后一个
        (3, 20, 0, 41),  # 第三页第一个，每页20条
        (3, 20, 19, 60), # 第三页最后一个
        (5, 15, 7, 68),  # 第五页第8个（索引7）
    ]
    
    print("测试分页编号连续性逻辑：")
    print("=" * 50)
    
    all_passed = True
    for page, size, idx, expected in test_cases:
        result = calculate_continuous_index(page, size, idx)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "PASS" if passed else "FAIL"
        print(f"{status} 页码={page}, 每页={size}, 索引={idx}: 结果={result}, 期望={expected}")
    
    print("=" * 50)
    if all_passed:
        print("所有测试通过！前端分页编号逻辑正确。")
    else:
        print("部分测试失败！请检查逻辑。")
    
    # 模拟实际分页场景
    print("\n模拟实际分页场景（每页10条）：")
    for page in range(1, 4):
        print(f"\n第{page}页：")
        for idx in range(10):
            num = calculate_continuous_index(page, 10, idx)
            print(f"  索引 {idx} -> 编号 {num}")

if __name__ == "__main__":
    test_pagination_logic()