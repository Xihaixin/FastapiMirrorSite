#!/usr/bin/env python3
"""
中国图书馆分类法网站爬虫
爬取 https://www.ztflh.com/ 获取完整的图书分类层级关系

采用递归深度优先访问策略：
1. 从首页开始，解析所有顶级分类
2. 对每个分类，递归访问其子页面
3. 在递归过程中记录父类关系
4. 最后统一处理路径
"""

import requests
from bs4 import BeautifulSoup
import time
import json
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from urllib.parse import urljoin
import sys


@dataclass
class Classification:
    """分类条目"""
    code: str
    name: str
    parent_code: Optional[str] = None
    level: int = 1
    path: Optional[str] = None
    url: Optional[str] = None


class ZTFLHCrawler:
    """中图分类法网站爬虫"""
    
    def __init__(self, base_url: str = "https://www.ztflh.com/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.classifications: List[Classification] = []
        self.code_to_class: Dict[str, Classification] = {}
        self.visited_urls = set()
        
        # 统计信息
        self.stats = {
            'pages_crawled': 0,
            'classifications_found': 0,
            'errors': 0
        }
    
    def normalize_code(self, code: str) -> str:
        """规范化分类代码，将F13/17转换为F13_17"""
        if not code:
            return code
        
        # 替换斜杠为下划线
        code = code.replace('/', '_')
        
        # 去除首尾空白
        return code.strip()
    
    def parse_classification_items(self, html: str, parent_code: Optional[str] = None, level: int = 1) -> List[Classification]:
        """解析HTML中的分类条目"""
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        # 查找分类列表 - 根据用户提供的HTML结构
        list_ul = soup.find('ul', {'id': 'list', 'class': 'cent'})
        if not list_ul:
            # 尝试其他可能的容器
            list_ul = soup.find('ul', {'id': 'list'})
            if not list_ul:
                list_ul = soup.find('ul', {'class': 'cent'})
        
        if not list_ul:
            return items
        
        # 解析每个<li>标签
        for li in list_ul.find_all('li'):
            # 提取分类代码
            code_span = li.find('span', {'class': 'code'})
            if not code_span:
                continue
            
            code = self.normalize_code(code_span.get_text().strip())
            
            # 提取分类名称
            name_a = li.find('a')
            if not name_a:
                continue
            
            name = name_a.get_text().strip()
            
            # 提取子分类链接
            child_url = None
            if name_a.has_attr('href'):
                child_url = urljoin(self.base_url, name_a['href'])
            
            # 创建分类对象
            cls = Classification(
                code=code,
                name=name,
                parent_code=parent_code,
                level=level,
                url=child_url
            )
            
            items.append(cls)
        
        return items
    
    def fetch_page(self, url: str) -> Optional[str]:
        """获取页面内容"""
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        self.stats['pages_crawled'] += 1
        
        try:
            print(f"正在访问: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 设置编码
            if response.encoding != 'utf-8':
                response.encoding = 'utf-8'
            
            return response.text
            
        except requests.RequestException as e:
            print(f"错误: 访问 {url} 失败: {e}")
            self.stats['errors'] += 1
            return None
        except Exception as e:
            print(f"错误: 处理 {url} 时发生异常: {e}")
            self.stats['errors'] += 1
            return None
    
    def has_subcategories(self, html: str) -> bool:
        """检查页面是否包含子分类"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 检查是否有"没有下级分类"的提示
        lost_div = soup.find('div', {'id': 'lost', 'class': 'cent'})
        if lost_div and '没有下级分类' in lost_div.get_text():
            return False
        
        # 检查是否有分类列表
        list_ul = soup.find('ul', {'id': 'list', 'class': 'cent'})
        if not list_ul:
            list_ul = soup.find('ul', {'id': 'list'})
        if not list_ul:
            list_ul = soup.find('ul', {'class': 'cent'})
        
        return list_ul is not None
    
    def crawl_recursive(self, url: str, parent_code: Optional[str] = None, level: int = 1):
        """
        递归爬取分类页面（深度优先）
        
        参数:
            url: 当前页面URL
            parent_code: 父分类代码
            level: 当前层级
        """
        # 获取页面内容
        html = self.fetch_page(url)
        if not html:
            return
        
        # 检查页面是否包含子分类
        if not self.has_subcategories(html):
            print(f"  页面 {url} 没有下级分类，停止递归")
            return
        
        # 解析当前页面的分类
        items = self.parse_classification_items(html, parent_code, level)
        
        for item in items:
            # 添加到总列表
            self.classifications.append(item)
            self.code_to_class[item.code] = item
            self.stats['classifications_found'] += 1
            
            print(f"  找到分类: {item.code} - {item.name} (层级: {level})")
            
            # 如果有子分类链接，递归爬取
            if item.url:
                # 添加延迟，避免对服务器造成压力（增加到1秒）
                time.sleep(1.0)
                self.crawl_recursive(item.url, item.code, level + 1)
    
    def calculate_paths(self):
        """计算每个分类的完整路径"""
        print("正在计算分类路径...")
        
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
    
    def save_to_json(self, filename: str = "ztflh_classifications.json"):
        """保存为JSON文件"""
        data = []
        for cls in self.classifications:
            cls_dict = asdict(cls)
            data.append(cls_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {filename}")
    
    def save_to_python(self, filename: str = "ztflh_classifications.py"):
        """保存为Python数据结构"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# 从中国图书馆分类法网站爬取的分类数据\n")
            f.write("# 来源: https://www.ztflh.com/\n")
            f.write("# 格式: (code, name, parent_code, level, path)\n\n")
            f.write("CLASSIFICATIONS = [\n")
            
            for i, cls in enumerate(self.classifications):
                parent_str = f"'{cls.parent_code}'" if cls.parent_code else "None"
                path_str = f"'{cls.path}'" if cls.path else "None"
                line = f"    (\"{cls.code}\", \"{cls.name}\", {parent_str}, {cls.level}, {path_str})"
                if i < len(self.classifications) - 1:
                    line += ","
                f.write(line + "\n")
            
            f.write("]\n")
        
        print(f"Python数据结构已保存到: {filename}")
    
    def print_statistics(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("爬取统计")
        print("="*60)
        print(f"爬取页面数: {self.stats['pages_crawled']}")
        print(f"找到分类数: {self.stats['classifications_found']}")
        print(f"错误数: {self.stats['errors']}")
        
        # 按层级统计
        level_counts = {}
        for cls in self.classifications:
            level_counts[cls.level] = level_counts.get(cls.level, 0) + 1
        
        print("\n按层级分布:")
        for level in sorted(level_counts.keys()):
            print(f"  层级 {level}: {level_counts[level]} 个分类")
        
        # 显示示例
        print("\n分类示例:")
        for i, cls in enumerate(self.classifications[:5]):
            print(f"  {cls.code}: {cls.name}")
            if cls.parent_code:
                print(f"    父类: {cls.parent_code}, 路径: {cls.path}")
            print()
    
    def crawl(self):
        """开始爬取"""
        print("开始爬取中国图书馆分类法网站...")
        print(f"基础URL: {self.base_url}")
        print("采用自动深度检测，遇到'没有下级分类'时停止")
        print("-" * 60)
        
        # 从首页开始爬取
        self.crawl_recursive(self.base_url)
        
        # 计算路径
        self.calculate_paths()
        
        # 打印统计
        self.print_statistics()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='中国图书馆分类法网站爬虫')
    parser.add_argument('--output-json', type=str, default='ztflh_classifications.json', help='JSON输出文件')
    parser.add_argument('--output-python', type=str, default='ztflh_classifications.py', help='Python输出文件')
    parser.add_argument('--test', action='store_true', help='测试模式（只测试首页）')
    
    args = parser.parse_args()
    
    crawler = ZTFLHCrawler()
    
    try:
        if args.test:
            print("测试模式：只爬取首页分类")
            # 只获取首页分类
            html = crawler.fetch_page(crawler.base_url)
            if html:
                items = crawler.parse_classification_items(html, parent_code=None, level=1)
                crawler.classifications.extend(items)
                for cls in items:
                    crawler.code_to_class[cls.code] = cls
                
                print(f"测试完成，获取到 {len(items)} 个顶级分类")
                
                # 计算路径
                crawler.calculate_paths()
                
                # 保存结果
                if crawler.classifications:
                    crawler.save_to_json(args.output_json)
                    crawler.save_to_python(args.output_python)
            else:
                print("测试失败：无法获取首页")
        else:
            # 开始完整爬取
            crawler.crawl()
            
            # 保存结果
            if crawler.classifications:
                crawler.save_to_json(args.output_json)
                crawler.save_to_python(args.output_python)
                
                print(f"\n爬取完成！共获取 {len(crawler.classifications)} 个分类")
            else:
                print("警告: 未获取到任何分类数据")
            
    except KeyboardInterrupt:
        print("\n用户中断爬取")
    except Exception as e:
        print(f"爬取过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()