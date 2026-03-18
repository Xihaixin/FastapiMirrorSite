# 根据 clc.json 文件解析图书层级

与"海纳中图分类.txt"不同，clc.json是一个结构化的JSON文件，包含完整的中图分类层级关系。parse_clc_json.py 模块用于解析 clc.json 文件，并将其图书分类和层级信息结构化地写入 parsed_clc_classifications.py 文件中，得到一个常量 `CLASS_DEFS`.

parse_clc_json 模块的解析原理，首先定义了一个数据类“Classification”：

```python
@dataclass
class Classification:
    """分类条目"""
    code: str
    name: str
    parent_code: Optional[str] = None
    level: int = 1
    path: Optional[str] = None
```

然后实例化一个 clc.json解析器:
> parser = CLCJsonParser()

调用 parser.parse_file 方法就能得到 classfications ,它是一个列表，其内部元素是 Classification 实例。

当我们得到 parsed_clc_classifications.py 后，就需要将这些分类数据和层级信息导入 SQLite 数据库，它们会创建一个表：cnl_classes。这一步我们使用 import_clc_classifications.py 模块的能力，最后使用 update_database_with_clc.py 模块根据图书分类层级信息为数据库创建虚拟数据，填充 resources 表并同步创建 resource_class_map ，将数据资源表与图书层级表进行映射。