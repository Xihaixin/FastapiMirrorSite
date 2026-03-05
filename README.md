## 快速开始

本项目基于 FastAPI + SQLite，用于演示简单的学术资源检索后端与前端。

### 1. 使用 uv 创建并激活虚拟环境（推荐）

在项目根目录 `FastapiMirrorSite` 下执行：

```bash
cd FastapiMirrorSite

# 创建虚拟环境（默认目录 .venv）
uv venv .venv

# 激活虚拟环境（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 若使用 CMD：
.venv\Scripts\activate.bat
```

> 提示：上述命令假设你已经可以在命令行中直接使用 `uv` 命令（如何安装 `uv` 此处不再赘述）。

### 2. 安装依赖

在已经激活的虚拟环境中运行：

```bash
uv pip install fastapi uvicorn sqlalchemy
```

如果项目目录中存在 `requirements.txt`，也可以使用：

```bash
uv pip install -r requirements.txt
```

### 3. 启动后端服务

仍在项目根目录下，确保虚拟环境已激活，然后运行：

```bash
uvicorn app.main:app --reload
```

默认会启动在 `http://127.0.0.1:8000`。

- 交互式 API 文档：`http://127.0.0.1:8000/docs`
- 静态前端页面：`http://127.0.0.1:8000/static/index.html`


### 生成虚拟数据

```bash
uv run python -m app.seed_data --count 800

```

### 学习资源

[阮一峰教程 ORM ](https://www.ruanyifeng.com/blog/2019/02/orm-tutorial.html)


### 4. 停止服务

在运行 `uvicorn` 的终端中按 `Ctrl + C` 即可停止服务。


### 5. 开发问题

中图分类法(2022) ，但是外文电子图书文库却使用中图分类法，这合适吗？


