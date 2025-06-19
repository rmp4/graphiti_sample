"""
API 請求和回應模型定義
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """搜尋請求模型"""
    query: str = Field(description="使用者查詢字串", examples=["台電的電力設備招標"])
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="對話歷史"
    )


class SearchResponse(BaseModel):
    """搜尋回應模型"""
    response: str = Field(..., description="格式化的搜尋回應")
    response_type: str = Field(..., description="回應類型")
    search_results: List[Dict[str, Any]] = Field(..., description="搜尋結果列表")
    result_count: int = Field(..., description="結果數量")
    search_time_ms: int = Field(..., description="搜尋時間（毫秒）")
    result_quality: float = Field(..., description="結果品質評分 (0-1)")
    intent: str = Field(..., description="識別的使用者意圖")
    intent_confidence: float = Field(..., description="意圖信心度 (0-1)")
    status: str = Field(..., description="執行狀態")
    error: Optional[str] = Field(default=None, description="錯誤訊息")
    conversation_history: List[Dict[str, Any]] = Field(..., description="更新後的對話歷史")


class HealthResponse(BaseModel):
    """健康檢查回應"""
    status: str = Field(..., description="服務狀態")
    timestamp: str = Field(..., description="檢查時間")
    version: str = Field(..., description="版本資訊")
    dependencies: Dict[str, str] = Field(..., description="依賴服務狀態")


class SystemStatsResponse(BaseModel):
    """系統統計回應"""
    total_searches: int = Field(..., description="總搜尋次數")
    average_response_time: float = Field(..., description="平均回應時間")
    success_rate: float = Field(..., description="成功率")
    active_sessions: int = Field(..., description="活躍會話數")
    system_info: Dict[str, Any] = Field(..., description="系統資訊")


class ErrorResponse(BaseModel):
    """錯誤回應模型"""
    error: str = Field(..., description="錯誤類型")
    message: str = Field(..., description="錯誤訊息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="錯誤詳情")
    timestamp: str = Field(..., description="錯誤發生時間")
