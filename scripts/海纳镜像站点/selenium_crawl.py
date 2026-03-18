import time
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, List

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

@dataclass
class Classification:
    """分类条目数据结构"""
    code: str
    name: str
    parent_code: Optional[str] = None
    level: int = 1
    path: Optional[str] = None

class ChinaLibraryEdgeCrawler:
    def __init__(self, start_url: str, driver_path: str):
        if not os.path.exists(driver_path):
            raise FileNotFoundError(f"未找到 EdgeDriver: {driver_path}")

        edge_options = Options()
        # edge_options.add_argument('--headless') # 调试时建议保持窗口可见
        
        service = Service(executable_path=driver_path)
        self.driver = webdriver.Edge(service=service, options=edge_options)
        
        self.start_url = start_url
        self.all_data = []

    def save_to_json(self, filename="library_data.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([asdict(item) for item in self.all_data], f, ensure_ascii=False, indent=4)
        print(f"\n[完成] 共抓取 {len(self.all_data)} 条数据，已保存至: {filename}")

    def wait_for_sub_nodes(self, container_id: str, timeout=5):
        """等待子节点加载"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_element(By.ID, container_id).get_attribute("innerHTML").strip() != ""
            )
            return True
        except TimeoutException:
            return False

    def crawl_level(self, parent_container_element, parent_code: Optional[str], level: int, parent_path: Optional[str]):
        """
        核心递归函数
        :param parent_container_element: 当前层级的容器元素对象（可以是 WebElement）
        """
        # 定位当前容器下所有的直接标题块
        # 使用 ./ 表示在当前元素下查找
        title_elements = parent_container_element.find_elements(By.XPATH, "./div[@class='mp_cc_cNodec']/div[@class='mp_cc_cNodeTi']")

        node_infos = []
        for el in title_elements:
            text = el.text.strip()
            if not text: continue
            
            node_id = el.get_attribute("id")
            code = node_id.replace("mp_cn_", "").replace("_t", "")
            name = text.split('(')[0]
            node_infos.append({"code": code, "name": name, "el_id": node_id})

        for info in node_infos:
            current_path = f"{parent_path} > {info['name']}" if parent_path else info['name']
            
            # 存储数据
            item = Classification(
                code=info['code'],
                name=info['name'],
                parent_code=parent_code,
                level=level,
                path=current_path
            )
            self.all_data.append(item)
            print(f"{'  ' * (level-1)}|-- {info['name']} ({info['code']})")

            # 尝试处理子节点
            child_container_id = f"mp_cn_{info['code']}"
            try:
                # 重新查找点击元素防止 Stale 引用
                target_el = self.driver.find_element(By.ID, info['el_id'])
                self.driver.execute_script("arguments[0].click();", target_el)
                
                # 等待并检查是否有内容加载
                if self.wait_for_sub_nodes(child_container_id):
                    # 找到刚刚加载内容的子容器
                    child_container_el = self.driver.find_element(By.ID, child_container_id)
                    # 递归
                    self.crawl_level(child_container_el, info['code'], level + 1, current_path)
            except Exception as e:
                # 如果没有子节点或点击失败，继续下一个
                continue

    def run(self):
        try:
            self.driver.get(self.start_url)
            print(f"正在访问: {self.start_url}")
            time.sleep(2) # 等待页面初始加载

            # --- 修改重点：定位那个没有 ID 的初始根容器 ---
            # 根据你提供的特征：包含 mp_cn_18_b 的那个 div 就是我们要的根
            try:
                # 使用 XPath 找到包含特定子 ID 的父级 div
                root_container = self.driver.find_element(By.XPATH, "//div[div/@id='mp_cn_18_b']")
            except NoSuchElementException:
                print("错误：无法定位根容器，请检查页面是否已加载。")
                return

            # 开始递归
            self.crawl_level(root_container, None, 1, None)
            self.save_to_json()
            
        finally:
            self.driver.quit()

if __name__ == "__main__":
    path = "D:\Program_OR\Program_sps\edgedriver_145\msedgedriver.exe"
    # 示例 URL，请替换为真实地址
    url = "http://192.168.3.100/auto/db/search.aspx?md=10&pd=5&msd=10&psd=5&mdd=10&pdd=5&count=10&cls=13&uni=False&agfi=0&agname=&showgp=False&gp=0&db=252002&wrd=" 
    
    crawler = ChinaLibraryEdgeCrawler(url, path)
    crawler.run()