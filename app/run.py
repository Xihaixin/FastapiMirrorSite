"""
FastAPI 应用启动入口
用于 PyInstaller 打包后独立运行
"""
import uvicorn

from .main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
