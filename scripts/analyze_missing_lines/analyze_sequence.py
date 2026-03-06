#!/usr/bin/env python3
"""分析序号跳跃问题"""

def analyze_sequence():
    with open('海纳中图分类.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"文件总行数: {len(lines)}")
    
    # 提取所有序号
    sequences = []
    line_details = []
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line and ':' in line:
            parts = line.split(':')
            if len(parts) >= 2 and parts[0].strip().isdigit():
                seq_num = int(parts[0].strip())
                sequences.append(seq_num)
                line_details.append((i, seq_num, line))
    
    print(f"找到的序号数量: {len(sequences)}")
    print(f"序号范围: {min(sequences)} 到 {max(sequences)}")
    
    # 检查序号跳跃
    print(f"\n序号跳跃分析:")
    prev_seq = sequences[0]
    jumps = []
    
    for i, (line_num, seq_num, line) in enumerate(line_details):
        if i > 0:
            expected = prev_seq + 1
            if seq_num != expected:
                jump_size = seq_num - prev_seq
                jumps.append((prev_seq, seq_num, jump_size, line_num))
                print(f"  跳跃: {prev_seq} -> {seq_num} (跳跃 {jump_size} 在第 {line_num} 行)")
        prev_seq = seq_num
    
    print(f"\n总共发现 {len(jumps)} 处序号跳跃")
    
    # 显示具体的跳跃行
    print(f"\n具体的跳跃位置:")
    for prev, curr, jump_size, line_num in jumps:
        # 显示跳跃前后的行
        for i in range(max(0, line_num-3), min(len(line_details), line_num+2)):
            lnum, snum, text = line_details[i]
            prefix = ">>> " if lnum == line_num else "    "
            print(f"{prefix}第 {lnum} 行: 序号 {snum}: {text[:60]}...")
        print()
    
    # 计算缺失的序号
    all_seqs = set(sequences)
    expected_seqs = set(range(1, max(sequences) + 1))
    missing = sorted(expected_seqs - all_seqs)
    
    print(f"\n缺失的序号 ({len(missing)} 个): {missing}")
    
    # 检查是否有重复序号
    from collections import Counter
    seq_counts = Counter(sequences)
    duplicates = [seq for seq, count in seq_counts.items() if count > 1]
    
    if duplicates:
        print(f"\n重复的序号: {duplicates}")
        for seq in duplicates:
            print(f"  序号 {seq} 出现 {seq_counts[seq]} 次")
    else:
        print("\n没有重复序号")

if __name__ == "__main__":
    analyze_sequence()