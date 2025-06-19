"""
招標搜尋 LangGraph 工作流程
整合所有節點函數建立完整的搜尋工作流程
"""

import logging
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage

from src.langgraph_integration.state import State, InputState
from src.langgraph_integration.workflow.node_functions import (
    analyze_intent_node,
    execute_search_node,
    refine_results_node,
    format_response_node,
    handle_followup_node
)

logger = logging.getLogger(__name__)

class TenderSearchGraph:
    """招標搜尋工作流程圖"""
    
    def __init__(self):
        self.graph = StateGraph(State, input=InputState)
        self.compiled_graph = None
        self._build_graph()
    
    def _build_graph(self):
        """建立 LangGraph 工作流程"""
        logger.info("開始建立招標搜尋 LangGraph")
        
        # 添加節點
        self.graph.add_node("analyze_intent", analyze_intent_node)
        self.graph.add_node("execute_search", execute_search_node)
        self.graph.add_node("refine_results", refine_results_node)
        self.graph.add_node("format_response", format_response_node)
        self.graph.add_node("handle_followup", handle_followup_node)
        
        # 定義邊和條件
        self._add_edges()
        
        # 編譯圖
        self.compiled_graph = self.graph.compile()
        
        logger.info("招標搜尋 LangGraph 建立完成")
    
    def _add_edges(self):
        """添加節點間的邊和條件"""
        # 從開始到意圖分析
        self.graph.add_edge(START, "analyze_intent")
        
        # 從意圖分析到搜尋執行
        self.graph.add_edge("analyze_intent", "execute_search")
        
        # 從搜尋執行到條件判斷
        self.graph.add_conditional_edges(
            "execute_search",
            self._should_refine_results,
            {
                "refine": "refine_results",
                "format": "format_response",
                "followup": "handle_followup"
            }
        )
        
        # 從結果精煉到格式化回應
        self.graph.add_edge("refine_results", "format_response")
        
        # 從後續查詢處理到格式化回應
        self.graph.add_edge("handle_followup", "format_response")
        
        # 從格式化回應到結束
        self.graph.add_edge("format_response", END)
    
    def _should_refine_results(self, state: State) -> str:
        """決定是否需要精煉結果"""
        try:
            # 簡化的路由邏輯，直接返回格式化
            # 由於簡化了 State，暫時移除複雜的判斷邏輯
            logger.info("直接進行格式化回應")
            return "format"
            
        except Exception as e:
            logger.error(f"判斷是否精煉時發生錯誤: {e}")
            return "format"
    
    async def run_search(self, user_query: str, 
                        conversation_history: Optional[list] = None) -> Dict[str, Any]:
        """執行搜尋工作流程"""
        try:
            logger.info(f"開始執行搜尋工作流程: {user_query}")
            
            # 創建初始狀態
            initial_state = {"messages": []}
            
            # 添加對話歷史
            if conversation_history:
                initial_state["messages"].extend(conversation_history)
            
            # 添加當前用戶訊息
            initial_state["messages"].append(HumanMessage(content=user_query))
            
            # 執行工作流程
            assert self.compiled_graph is not None, "Graph 尚未編譯，無法執行"
            final_state = await self.compiled_graph.ainvoke(initial_state)
            
            # 從 messages 中提取最後的 AI 回應
            ai_response = ""
            for msg in reversed(final_state["messages"]):
                if isinstance(msg, AIMessage) and not getattr(msg, 'tool_calls', None):
                    ai_response = msg.content
                    break
            
            # 準備回應 - 簡化版本
            result = {
                "response": ai_response,
                "response_type": "text",
                "search_results": [],
                "result_count": 0,
                "search_time_ms": 0,
                "result_quality": 0.0,
                "intent": "unknown",
                "intent_confidence": 0.0,
                "status": "completed",
                "error": None,
                "conversation_history": final_state["messages"]
            }
            
            logger.info(f"搜尋工作流程完成")
            return result
            
        except Exception as e:
            logger.error(f"執行搜尋工作流程時發生錯誤: {e}")
            return {
                "response": f"搜尋過程發生錯誤: {str(e)}",
                "response_type": "error",
                "search_results": [],
                "result_count": 0,
                "search_time_ms": 0,
                "result_quality": 0.0,
                "intent": "unknown",
                "intent_confidence": 0.0,
                "status": "error",
                "error": str(e),
                "conversation_history": []
            }
    
    def run_search_sync(self, user_query: str, 
                       conversation_history: Optional[list] = None) -> Dict[str, Any]:
        """同步執行搜尋工作流程"""
        import asyncio
        
        try:
            # 檢查是否已經在事件循環中
            loop = asyncio.get_running_loop()
            # 如果已經在事件循環中，使用不同的方法
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, 
                    self.run_search(user_query, conversation_history)
                )
                return future.result()
        except RuntimeError:
            # 沒有運行中的事件循環，可以直接運行
            return asyncio.run(self.run_search(user_query, conversation_history))
    
    def get_graph_visualization(self) -> str:
        """獲取圖的視覺化表示"""
        if not self.compiled_graph:
            return "圖尚未編譯"
        
        try:
            # 嘗試獲取圖的 mermaid 表示
            return self.compiled_graph.get_graph().draw_mermaid()
        except Exception as e:
            logger.warning(f"無法生成圖的視覺化: {e}")
            return f"圖包含以下節點: analyze_intent -> execute_search -> (refine_results|handle_followup) -> format_response"

# 全域圖實例
_tender_search_instance = TenderSearchGraph()

# LangGraph CLI 需要的圖實例
tender_search_graph = _tender_search_instance.compiled_graph

def search_tenders(user_query: str, 
                  conversation_history: Optional[list] = None) -> Dict[str, Any]:
    """
    搜尋招標案的便利函數
    
    Args:
        user_query: 用戶查詢
        conversation_history: 對話歷史
    
    Returns:
        包含搜尋結果的字典
    """
    return _tender_search_instance.run_search_sync(user_query, conversation_history)

async def search_tenders_async(user_query: str, 
                              conversation_history: Optional[list] = None) -> Dict[str, Any]:
    """
    異步搜尋招標案的便利函數
    
    Args:
        user_query: 用戶查詢
        conversation_history: 對話歷史
    
    Returns:
        包含搜尋結果的字典
    """
    return await _tender_search_instance.run_search(user_query, conversation_history)

def get_workflow_info() -> Dict[str, Any]:
    """獲取工作流程資訊"""
    return {
        "workflow_name": "TenderSearchGraph",
        "nodes": ["analyze_intent", "execute_search", "refine_results", "format_response", "handle_followup"],
        "capabilities": [
            "自然語言意圖分析",
            "多種搜尋策略",
            "智能結果精煉",
            "格式化回應生成",
            "後續查詢處理"
        ],
        "supported_intents": ["organization", "amount", "category", "date", "comprehensive"],
        "visualization": _tender_search_instance.get_graph_visualization()
    }

# 用於測試的簡單介面
class TenderSearchInterface:
    """招標搜尋介面"""
    
    def __init__(self):
        self.conversation_history = []
    
    def search(self, query: str) -> str:
        """執行搜尋並返回格式化結果"""
        result = search_tenders(query, self.conversation_history)
        
        # 更新對話歷史
        self.conversation_history = result.get("conversation_history", [])
        
        return result["response"]
    
    def get_last_results(self) -> Dict[str, Any]:
        """獲取最後一次搜尋的詳細結果"""
        if not self.conversation_history:
            return {"message": "尚未進行任何搜尋"}
        
        # 這裡應該保存更詳細的結果，目前簡化處理
        return {"conversation_length": len(self.conversation_history)}
    
    def clear_history(self):
        """清除對話歷史"""
        self.conversation_history = []
        logger.info("對話歷史已清除")

# 全域介面實例
search_interface = TenderSearchInterface()
