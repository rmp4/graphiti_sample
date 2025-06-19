"""
LangGraph 狀態管理器
定義和管理招標搜尋工作流程的狀態
"""

import logging
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

class SearchStatus(Enum):
    """搜尋狀態"""
    INITIALIZED = "initialized"
    ANALYZING_INTENT = "analyzing_intent"
    EXECUTING_SEARCH = "executing_search"
    REFINING_RESULTS = "refining_results"
    FORMATTING_RESPONSE = "formatting_response"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class SearchContext:
    """搜尋上下文"""
    original_query: str = ""
    intent_type: str = ""
    confidence: float = 0.0
    search_parameters: Dict[str, Any] = field(default_factory=dict)
    search_strategy: str = ""
    refinement_count: int = 0
    max_refinements: int = 3
    
    def add_refinement(self, refinement_info: Dict[str, Any]):
        """添加精煉資訊"""
        self.refinement_count += 1
        if not hasattr(self, 'refinement_history'):
            self.refinement_history = []
        self.refinement_history.append({
            'count': self.refinement_count,
            'timestamp': datetime.now().isoformat(),
            'info': refinement_info
        })
    
    def can_refine(self) -> bool:
        """檢查是否可以繼續精煉"""
        return self.refinement_count < self.max_refinements

@dataclass  
class SearchResult:
    """搜尋結果"""
    results: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    search_time_ms: int = 0
    result_quality: float = 0.0  # 結果品質評分 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_result(self, result: Dict[str, Any]):
        """添加單一結果"""
        self.results.append(result)
        self.total_count = len(self.results)
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取結果摘要"""
        if not self.results:
            return {"message": "無搜尋結果"}
        
        agencies = set()
        categories = set()
        amount_info = []
        
        for result in self.results:
            if 'agency' in result and result['agency']:
                agencies.add(result['agency'])
            if 'category' in result and result['category']:
                categories.add(result['category'])
            if 'amount' in result and result['amount']:
                amount_info.append(result['amount'])
        
        return {
            "total_results": self.total_count,
            "unique_agencies": len(agencies),
            "unique_categories": len(categories),
            "search_time_ms": self.search_time_ms,
            "quality_score": self.result_quality,
            "top_agencies": list(agencies)[:5],
            "top_categories": list(categories)[:5]
        }

class TenderSearchState(TypedDict):
    """招標搜尋狀態定義"""
    # 對話訊息
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 搜尋相關狀態
    search_context: SearchContext
    search_results: SearchResult
    current_status: SearchStatus
    
    # 使用者輸入和意圖
    user_query: str
    user_intent: str
    intent_confidence: float
    intent_parameters: Dict[str, Any]
    
    # 工作流程控制
    current_step: str
    next_step: Optional[str]
    error_message: Optional[str]
    should_continue: bool
    
    # 回應生成
    formatted_response: str
    response_type: str  # "text", "summary", "detailed", "comparison"
    
    # 精煉和迭代
    refinement_history: List[Dict[str, Any]]
    needs_refinement: bool
    refinement_suggestions: List[str]

class StateManager:
    """狀態管理器"""
    
    def __init__(self):
        self.default_state = self._create_default_state()
    
    def _create_default_state(self) -> TenderSearchState:
        """創建預設狀態"""
        return TenderSearchState(
            messages=[],
            search_context=SearchContext(),
            search_results=SearchResult(),
            current_status=SearchStatus.INITIALIZED,
            user_query="",
            user_intent="",
            intent_confidence=0.0,
            intent_parameters={},
            current_step="start",
            next_step="analyze_intent",
            error_message=None,
            should_continue=True,
            formatted_response="",
            response_type="text",
            refinement_history=[],
            needs_refinement=False,
            refinement_suggestions=[]
        )
    
    def initialize_state(self, user_query: str) -> TenderSearchState:
        """初始化新的搜尋狀態"""
        state = self._create_default_state()
        state["user_query"] = user_query
        state["search_context"].original_query = user_query
        
        logger.info(f"初始化搜尋狀態，查詢: {user_query}")
        return state
    
    def update_intent_analysis(self, state: TenderSearchState, 
                             intent: str, confidence: float, 
                             parameters: Dict[str, Any]) -> TenderSearchState:
        """更新意圖分析結果"""
        state["user_intent"] = intent
        state["intent_confidence"] = confidence
        state["intent_parameters"] = parameters
        state["search_context"].intent_type = intent
        state["search_context"].confidence = confidence
        state["search_context"].search_parameters = parameters
        state["current_status"] = SearchStatus.ANALYZING_INTENT
        
        logger.info(f"更新意圖分析: {intent}, 信心度: {confidence}")
        return state
    
    def update_search_results(self, state: TenderSearchState, 
                            results: List[Dict[str, Any]], 
                            search_time_ms: int = 0) -> TenderSearchState:
        """更新搜尋結果"""
        state["search_results"].results = results
        state["search_results"].total_count = len(results)
        state["search_results"].search_time_ms = search_time_ms
        state["current_status"] = SearchStatus.EXECUTING_SEARCH
        
        # 評估結果品質
        quality_score = self._evaluate_result_quality(results)
        state["search_results"].result_quality = quality_score
        
        logger.info(f"更新搜尋結果: {len(results)} 個結果, 品質分數: {quality_score}")
        return state
    
    def update_refinement_status(self, state: TenderSearchState, 
                               needs_refinement: bool, 
                               suggestions: Optional[List[str]] = None) -> TenderSearchState:
        """更新精煉狀態"""
        state["needs_refinement"] = needs_refinement
        state["refinement_suggestions"] = suggestions or []
        
        if needs_refinement and state["search_context"].can_refine():
            state["current_status"] = SearchStatus.REFINING_RESULTS
            state["next_step"] = "refine_results"
        else:
            state["next_step"] = "format_response"
        
        logger.info(f"更新精煉狀態: {needs_refinement}, 建議: {len(suggestions or [])}")
        return state
    
    def update_formatted_response(self, state: TenderSearchState, 
                                formatted_response: str, 
                                response_type: str = "text") -> TenderSearchState:
        """更新格式化回應"""
        state["formatted_response"] = formatted_response
        state["response_type"] = response_type
        state["current_status"] = SearchStatus.FORMATTING_RESPONSE
        state["should_continue"] = False  # 完成搜尋
        
        logger.info(f"更新格式化回應: {response_type}, 長度: {len(formatted_response)}")
        return state
    
    def add_error(self, state: TenderSearchState, error_message: str) -> TenderSearchState:
        """添加錯誤訊息"""
        state["error_message"] = error_message
        state["current_status"] = SearchStatus.ERROR
        state["should_continue"] = False
        
        logger.error(f"搜尋過程發生錯誤: {error_message}")
        return state
    
    def determine_next_step(self, state: TenderSearchState) -> str:
        """決定下一步驟"""
        current_status = state["current_status"]
        
        if current_status == SearchStatus.INITIALIZED:
            return "analyze_intent"
        elif current_status == SearchStatus.ANALYZING_INTENT:
            return "execute_search"
        elif current_status == SearchStatus.EXECUTING_SEARCH:
            # 檢查是否需要精煉
            if self._should_refine_results(state):
                return "refine_results"
            else:
                return "format_response"
        elif current_status == SearchStatus.REFINING_RESULTS:
            return "format_response"
        elif current_status == SearchStatus.FORMATTING_RESPONSE:
            return "complete"
        elif current_status == SearchStatus.ERROR:
            return "handle_error"
        else:
            return "complete"
    
    def _evaluate_result_quality(self, results: List[Dict[str, Any]]) -> float:
        """評估結果品質"""
        if not results:
            return 0.0
        
        quality_score = 0.0
        total_weight = 0.0
        
        # 結果數量分數 (0.3權重)
        count_score = min(len(results) / 10.0, 1.0)  # 10個結果為滿分
        quality_score += count_score * 0.3
        total_weight += 0.3
        
        # 資料完整性分數 (0.4權重)
        completeness_score = 0.0
        required_fields = ['tender_name', 'agency', 'amount']
        
        for result in results:
            field_score = sum(1 for field in required_fields if result.get(field))
            completeness_score += field_score / len(required_fields)
        
        completeness_score /= len(results)
        quality_score += completeness_score * 0.4
        total_weight += 0.4
        
        # 多樣性分數 (0.3權重)
        agencies = set(r.get('agency') for r in results if r.get('agency'))
        categories = set(r.get('category') for r in results if r.get('category'))
        
        diversity_score = 0.0
        if len(results) > 1:
            agency_diversity = len(agencies) / len(results)
            category_diversity = len(categories) / len(results)
            diversity_score = (agency_diversity + category_diversity) / 2.0
        
        quality_score += diversity_score * 0.3
        total_weight += 0.3
        
        return quality_score / total_weight if total_weight > 0 else 0.0
    
    def _should_refine_results(self, state: TenderSearchState) -> bool:
        """判斷是否應該精煉結果"""
        results = state["search_results"]
        
        # 如果沒有結果，需要精煉
        if results.total_count == 0:
            return True
        
        # 如果結果品質太低，需要精煉
        if results.result_quality < 0.5:
            return True
        
        # 如果結果太少且信心度不高，需要精煉
        if results.total_count < 3 and state["intent_confidence"] < 0.7:
            return True
        
        # 如果還可以繼續精煉，且用戶意圖不明確
        if (state["search_context"].can_refine() and 
            state["user_intent"] == "unknown"):
            return True
        
        return False
    
    def get_state_summary(self, state: TenderSearchState) -> Dict[str, Any]:
        """獲取狀態摘要"""
        return {
            "current_status": state["current_status"].value,
            "user_query": state["user_query"],
            "intent": state["user_intent"],
            "intent_confidence": state["intent_confidence"],
            "result_count": state["search_results"].total_count,
            "result_quality": state["search_results"].result_quality,
            "needs_refinement": state["needs_refinement"],
            "should_continue": state["should_continue"],
            "error": state["error_message"]
        }

# 全域狀態管理器實例
state_manager = StateManager()

def create_initial_state(user_query: str) -> TenderSearchState:
    """創建初始狀態的便利函數"""
    return state_manager.initialize_state(user_query)

def get_state_info(state: TenderSearchState) -> str:
    """獲取狀態資訊的便利函數"""
    summary = state_manager.get_state_summary(state)
    return f"狀態: {summary['current_status']}, 查詢: {summary['user_query']}, 結果: {summary['result_count']}"
