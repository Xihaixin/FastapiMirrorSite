# clc.json分类更新实施详细步骤

## 第一阶段：解析器开发

### 步骤1.1：创建clc.json解析器
- [ ] 创建 `scripts/parse_clc_json.py` 文件
- [ ] 实现JSON文件读取功能
- [ ] 设计递归解析算法
- [ ] 提取分类代码和描述
- [ ] 计算层级关系和父分类

### 步骤1.2：数据结构转换
- [ ] 将嵌套JSON转换为扁平列表
- [ ] 生成 `(code, name, parent_code, level)` 格式
- [ ] 验证数据完整性
- [ ] 输出分类统计信息

### 步骤1.3：权重分配
- [ ] 分析分类使用频率
- [ ] 设计权重分配算法
- [ ] 生成 `GEN_CLASS_WEIGHTS` 字典
- [ ] 验证权重分布合理性

## 第二阶段：代码更新

### 步骤2.1：更新分类定义文件
- [ ] 备份现有的 `app/cnl_classifications.py`
- [ ] 使用解析器生成新的 `CLASS_DEFS`
- [ ] 更新 `GEN_CLASS_WEIGHTS`
- [ ] 验证数据格式兼容性

### 步骤2.2：创建新的种子数据脚本
- [ ] 创建 `app/seed_data_clc.py`
- [ ] 实现清空现有数据功能
- [ ] 实现分类数据导入功能
- [ ] 添加数据验证逻辑

### 步骤2.3：更新主应用配置
- [ ] 检查 `app/main.py` 中的种子数据引用
- [ ] 确保API兼容性
- [ ] 更新相关导入语句

## 第三阶段：数据库操作

### 步骤3.1：数据备份
- [ ] 备份现有数据库
- [ ] 导出当前分类数据
- [ ] 导出资源-分类映射关系

### 步骤3.2：数据清理
- [ ] 执行清空操作（可选）
- [ ] 验证表结构完整性
- [ ] 检查外键约束

### 步骤3.3：数据导入
- [ ] 运行新的种子数据脚本
- [ ] 监控导入进度
- [ ] 验证导入结果

## 第四阶段：测试验证

### 步骤4.1：分类数据测试
- [ ] 验证分类数量
- [ ] 检查层级关系正确性
- [ ] 测试路径字段计算
- [ ] 验证唯一性约束

### 步骤4.2：API测试
- [ ] 测试分类查询API
- [ ] 验证树形结构返回
- [ ] 测试资源分类关联
- [ ] 检查前端页面显示

### 步骤4.3：性能测试
- [ ] 分类查询响应时间
- [ ] 树形结构构建性能
- [ ] 并发访问测试

## 第五阶段：部署与监控

### 步骤5.1：部署准备
- [ ] 创建部署脚本
- [ ] 准备回滚方案
- [ ] 通知相关用户

### 步骤5.2：执行部署
- [ ] 执行数据更新
- [ ] 验证系统功能
- [ ] 监控系统状态

### 步骤5.3：后续监控
- [ ] 监控系统性能
- [ ] 收集用户反馈
- [ ] 优化调整

## 关键代码示例

### clc.json解析器核心代码
```python
import json
from typing import List, Tuple

def parse_clc_json(file_path: str) -> List[Tuple[str, str, str, int]]:
    """解析clc.json文件，返回分类列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    classifications = []
    
    def traverse(items, parent_code=None, level=1):
        for item in items:
            code = item.get('id', '')
            desc = item.get('desc', '')
            
            if code and desc:
                classifications.append((code, desc, parent_code, level))
            
            # 递归处理子分类
            children = item.get('children', [])
            if children:
                traverse(children, parent_code=code, level=level+1)
    
    traverse(data)
    return classifications
```

### 数据库导入函数
```python
def import_classifications(db: Session, classifications: List[Tuple]):
    """导入分类数据到数据库"""
    # 清空现有数据
    db.query(models.ResourceClassMap).delete()
    db.query(models.CnlClass).delete()
    
    # 创建分类映射字典
    code_to_id = {}
    
    # 第一遍：创建所有分类
    for code, name, parent_code, level in classifications:
        cnl_class = models.CnlClass(
            code=code,
            name=name,
            level=level
        )
        db.add(cnl_class)
    
    db.commit()
    
    # 第二遍：更新父分类关系
    for code, name, parent_code, level in classifications:
        cnl_class = db.query(models.CnlClass).filter_by(code=code).first()
        if parent_code and parent_code in code_to_id:
            cnl_class.parent_id = code_to_id[parent_code]
    
    db.commit()
```

## 注意事项

1. **数据备份**：在执行任何数据操作前，务必备份现有数据
2. **测试环境**：先在测试环境验证所有功能
3. **逐步实施**：分阶段实施，每阶段验证通过后再继续
4. **监控日志**：详细记录操作日志，便于问题排查
5. **回滚准备**：准备完整的数据回滚方案

## 预计时间安排

- 第一阶段：1-2天（解析器开发）
- 第二阶段：1天（代码更新）
- 第三阶段：0.5天（数据库操作）
- 第四阶段：1天（测试验证）
- 第五阶段：0.5天（部署监控）

**总计：4-5天**

## 成功验收标准

1. ✅ 分类数据完整导入，无丢失
2. ✅ 层级关系正确，无孤儿节点
3. ✅ API接口保持兼容，无破坏性变更
4. ✅ 系统性能符合要求，无显著下降
5. ✅ 用户功能正常，无影响使用的问题