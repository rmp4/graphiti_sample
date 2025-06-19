"""
LangGraph CLI 整合啟動腳本
用於在沒有安裝 FastAPI 的情況下測試基本功能
"""

import os
import sys
import logging
from datetime import datetime

# 添加 src 到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """檢查依賴是否已安裝"""
    missing_deps = []
    
    try:
        import fastapi
        logger.info("✅ FastAPI 已安裝")
    except ImportError:
        missing_deps.append("fastapi")
    
    try:
        import uvicorn
        logger.info("✅ Uvicorn 已安裝")
    except ImportError:
        missing_deps.append("uvicorn[standard]")
    
    try:
        from langgraph_integration.workflow.tender_search_graph import search_tenders
        logger.info("✅ LangGraph 工作流程可用")
    except ImportError as e:
        logger.warning(f"⚠️  LangGraph 工作流程載入問題: {e}")
    
    return missing_deps

def install_dependencies(deps):
    """安裝缺少的依賴"""
    if not deps:
        return True
        
    logger.info(f"正在安裝缺少的依賴: {', '.join(deps)}")
    
    import subprocess
    try:
        for dep in deps:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"安裝依賴失敗: {e}")
        return False

def start_server():
    """啟動服務器"""
    try:
        # 檢查並安裝依賴
        missing = check_dependencies()
        if missing:
            logger.info("檢測到缺少的依賴，嘗試自動安裝...")
            if not install_dependencies(missing):
                logger.error("依賴安裝失敗，請手動安裝：")
                for dep in missing:
                    print(f"pip install {dep}")
                return False
        
        # 重新檢查依賴
        try:
            import uvicorn
            from .server import app
        except ImportError:
            logger.error("依賴仍然缺失，無法啟動服務器")
            return False
        
        # 取得配置
        host = os.getenv("LANGGRAPH_HOST", "0.0.0.0")
        port = int(os.getenv("LANGGRAPH_PORT", "8123"))
        
        logger.info(f"🚀 正在啟動 LangGraph + Graphiti 招標搜尋 API...")
        logger.info(f"🌐 服務地址: http://{host}:{port}")
        logger.info(f"📚 API 文檔: http://{host}:{port}/docs")
        
        # 啟動服務器
        uvicorn.run(
            "src.langgraph_integration.api.server:app",
            host=host,
            port=port,
            reload=True,
            log_level="debug"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"啟動服務器失敗: {e}")
        return False

def test_basic_functionality():
    """測試基本功能"""
    logger.info("🧪 測試基本功能...")
    
    try:
        from langgraph_integration.workflow.tender_search_graph import search_tenders
        
        # 執行簡單搜尋測試
        result = search_tenders("台電")
        
        if result and "response" in result:
            logger.info("✅ LangGraph 工作流程測試成功")
            logger.info(f"測試結果預覽: {result['response'][:100]}...")
            return True
        else:
            logger.warning("⚠️  LangGraph 工作流程測試返回空結果")
            return False
            
    except Exception as e:
        logger.error(f"❌ LangGraph 工作流程測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("=" * 60)
    print("🏛️  LangGraph + Graphiti 招標搜尋系統")
    print("=" * 60)
    
    # 檢查環境變數
    env_vars = ["OPENAI_API_KEY", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]
    missing_env = [var for var in env_vars if not os.getenv(var)]
    
    if missing_env:
        logger.warning(f"⚠️  缺少環境變數: {missing_env}")
        logger.warning("請在 .env 檔案中設定這些變數")
    
    # 測試基本功能
    if test_basic_functionality():
        logger.info("✅ 基本功能測試通過")
    else:
        logger.warning("⚠️  基本功能測試未通過，但仍會嘗試啟動服務器")
    
    # 啟動服務器
    if start_server():
        logger.info("🎉 服務器啟動成功！")
    else:
        logger.error("❌ 服務器啟動失敗")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
