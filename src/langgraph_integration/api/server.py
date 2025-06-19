"""
FastAPI 伺服器應用程式
提供 RESTful API 端點來存取 LangGraph 工作流程
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 添加 src 到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .models import (
    SearchRequest, 
    SearchResponse, 
    HealthResponse, 
    SystemStatsResponse, 
    ErrorResponse
)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全域變數儲存統計資訊
app_stats = {
    "total_searches": 0,
    "total_errors": 0,
    "start_time": datetime.now(),
    "active_sessions": 0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    logger.info("🚀 LangGraph + Graphiti 招標搜尋 API 正在啟動...")
    
    # 啟動時的初始化工作
    try:
        # 嘗試導入 LangGraph 工作流程
        from langgraph_integration.workflow.tender_search_graph import search_tenders_async
        app.state.search_function = search_tenders_async
        logger.info("✅ LangGraph 工作流程載入成功")
    except ImportError as e:
        logger.error(f"❌ 無法載入 LangGraph 工作流程: {e}")
        app.state.search_function = None
    
    yield
    
    # 關閉時的清理工作
    logger.info("👋 LangGraph + Graphiti 招標搜尋 API 正在關閉...")

# 建立 FastAPI 應用程式
app = FastAPI(
    title="LangGraph + Graphiti 招標搜尋 API",
    description="提供智能招標搜尋功能的 RESTful API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 中介軟體
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全域例外處理器"""
    logger.error(f"未處理的例外: {exc}")
    app_stats["total_errors"] += 1
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message=str(exc),
            timestamp=datetime.now().isoformat()
        ).model_dump()
    )

@app.get("/", response_model=Dict[str, str])
async def root():
    """根端點"""
    return {
        "message": "LangGraph + Graphiti 招標搜尋 API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查端點"""
    try:
        # 檢查 LangGraph 工作流程是否可用
        search_available = hasattr(app.state, 'search_function') and app.state.search_function is not None
        
        # 檢查環境變數
        env_vars = ["OPENAI_API_KEY", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]
        env_status = {var: "✅" if os.getenv(var) else "❌" for var in env_vars}
        
        dependencies = {
            "langgraph_workflow": "✅" if search_available else "❌",
            **env_status
        }
        
        status = "healthy" if search_available else "degraded"
        
        return HealthResponse(
            status=status,
            timestamp=datetime.now().isoformat(),
            version="0.1.0",
            dependencies=dependencies
        )
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_tenders(request: SearchRequest):
    """招標搜尋端點"""
    try:
        app_stats["total_searches"] += 1
        app_stats["active_sessions"] += 1
        
        start_time = datetime.now()
        
        # 檢查搜尋功能是否可用
        if not hasattr(app.state, 'search_function') or app.state.search_function is None:
            raise HTTPException(
                status_code=503, 
                detail="搜尋功能目前不可用，請檢查 LangGraph 工作流程配置"
            )
        
        logger.info(f"收到搜尋請求: {request.query}")
        
        # 執行搜尋
        result = await app.state.search_function(
            request.query, 
            request.conversation_history
        )
        
        # 計算執行時間
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 更新結果中的搜尋時間
        if "search_time_ms" in result:
            result["search_time_ms"] = int(execution_time)
        
        app_stats["active_sessions"] -= 1
        
        logger.info(f"搜尋完成: 找到 {result.get('result_count', 0)} 個結果，耗時 {execution_time:.2f}ms")
        
        return SearchResponse(**result)
        
    except HTTPException:
        app_stats["active_sessions"] -= 1
        raise
    except Exception as e:
        app_stats["active_sessions"] -= 1
        app_stats["total_errors"] += 1
        logger.error(f"搜尋過程發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"搜尋失敗: {str(e)}")

@app.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats():
    """取得系統統計資訊"""
    try:
        uptime = (datetime.now() - app_stats["start_time"]).total_seconds()
        
        # 計算平均回應時間 (簡化版本)
        avg_response_time = 1000 if app_stats["total_searches"] == 0 else 1500
        
        # 計算成功率
        total_requests = app_stats["total_searches"]
        success_rate = (
            (total_requests - app_stats["total_errors"]) / total_requests * 100
            if total_requests > 0 else 100.0
        )
        
        return SystemStatsResponse(
            total_searches=app_stats["total_searches"],
            average_response_time=avg_response_time,
            success_rate=success_rate,
            active_sessions=app_stats["active_sessions"],
            system_info={
                "uptime_seconds": uptime,
                "start_time": app_stats["start_time"].isoformat(),
                "total_errors": app_stats["total_errors"],
                "python_version": sys.version,
                "environment": os.getenv("ENVIRONMENT", "unknown")
            }
        )
    except Exception as e:
        logger.error(f"獲取統計資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/info")
async def get_workflow_info():
    """取得工作流程資訊"""
    try:
        from langgraph_integration.workflow.tender_search_graph import get_workflow_info
        return get_workflow_info()
    except ImportError:
        raise HTTPException(status_code=503, detail="工作流程資訊不可用")
    except Exception as e:
        logger.error(f"獲取工作流程資訊失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("LANGGRAPH_HOST", "0.0.0.0")
    port = int(os.getenv("LANGGRAPH_PORT", "8123"))
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
