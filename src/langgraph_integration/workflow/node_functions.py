"""
LangGraph 節點函數
定義招標搜尋工作流程中各個節點的執行邏輯
"""

import logging
from typing import Dict, Any, List

from langchain_core.messages import AIMessage, HumanMessage
from ..state import State

logger = logging.getLogger(__name__)

async def analyze_intent_node(state: State) -> State:
    """意圖分析節點"""
    try:
        # 從 messages 中提取最新的用戶查詢
        user_query = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_query = msg.content
                break
        
        logger.info(f"開始分析查詢意圖: {user_query}")
        
        # 簡單的關鍵字分析
        if user_query and isinstance(user_query, str):
            query_lower = user_query.lower()
            intent_info = analyze_simple_intent(query_lower)
        else:
            intent_info = {"type": "一般綜合搜尋", "keywords": ["未檢測到查詢內容"]}
        
        response = f"✓ 已分析您的查詢: {user_query}\n意圖類型: {intent_info['type']}\n關鍵字: {', '.join(intent_info['keywords'])}"
        
        # 創建新的 messages 列表來更新狀態
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=response))
        
        # 返回更新的狀態
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }
        
    except Exception as e:
        logger.error(f"意圖分析節點發生錯誤: {e}")
        error_response = f"意圖分析失敗: {str(e)}"
        
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=error_response))
        
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }

def analyze_simple_intent(query: str) -> dict:
    """簡單的意圖分析函數"""
    # 預定義的關鍵字分類
    categories = {
        "數據相關": ["大數據", "數據", "資料", "分析", "統計", "ai", "人工智慧", "機器學習"],
        "系統相關": ["系統", "平台", "網站", "軟體", "app", "應用程式", "開發"],
        "硬體相關": ["設備", "硬體", "伺服器", "電腦", "網路", "機房"],
        "服務相關": ["服務", "維護", "支援", "諮詢", "顧問", "管理"],
        "教育相關": ["教育", "訓練", "課程", "學習", "培訓"],
        "建設相關": ["建設", "工程", "建築", "施工", "營造"]
    }
    
    # 機關關鍵字
    agencies = ["台電", "中華電信", "台灣銀行", "教育部", "經濟部", "交通部", "內政部", "財政部", "衛生福利部", "衛福部", "健保署"]
    
    # 金額關鍵字
    amount_keywords = ["萬", "千萬", "億", "元", "預算", "金額", "費用", "價格"]
    
    detected_categories = []
    detected_agencies = []
    detected_amounts = []
    all_keywords = []
    
    # 檢查類別
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in query:
                if category not in detected_categories:
                    detected_categories.append(category)
                all_keywords.append(keyword)
    
    # 檢查機關
    for agency in agencies:
        if agency in query:
            detected_agencies.append(agency)
            all_keywords.append(agency)
    
    # 檢查金額相關
    for amount_kw in amount_keywords:
        if amount_kw in query:
            detected_amounts.append(amount_kw)
            all_keywords.append(amount_kw)
    
    # 決定主要意圖類型
    if detected_agencies:
        intent_type = f"機關搜尋 ({', '.join(detected_agencies)})"
    elif detected_amounts:
        intent_type = "預算金額搜尋"
    elif detected_categories:
        intent_type = f"類別搜尋 ({', '.join(detected_categories)})"
    else:
        intent_type = "一般綜合搜尋"
    
    return {
        "type": intent_type,
        "keywords": all_keywords if all_keywords else ["未檢測到特定關鍵字"],
        "categories": detected_categories,
        "agencies": detected_agencies,
        "amounts": detected_amounts
    }

async def execute_search_node(state: State) -> State:
    """搜尋執行節點"""
    try:
        # 從 messages 中提取最新的用戶查詢和意圖分析結果
        user_query = ""
        intent_info = None
        
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_query = msg.content
                break
        
        # 從第二個 AI 訊息中提取意圖分析結果
        intent_type = ""
        keywords = []
        
        for i, msg in enumerate(state["messages"]):
            if isinstance(msg, AIMessage) and isinstance(msg.content, str) and "意圖類型:" in msg.content:
                # 解析意圖類型和關鍵字
                content_lines = msg.content.split('\n')
                for line in content_lines:
                    if "意圖類型:" in line:
                        intent_type = line.split("意圖類型:")[1].strip()
                    elif "關鍵字:" in line:
                        keywords = line.split("關鍵字:")[1].strip().split(', ')
                intent_info = {"type": intent_type, "keywords": keywords}
                break
        
        # 如果沒有找到意圖資訊，設置預設值
        if not intent_info:
            intent_info = {"type": "一般綜合搜尋", "keywords": []}
        
        logger.info(f"開始執行搜尋: {user_query}, 意圖: {intent_info}")
        
        # 確保 user_query 是字符串
        if not isinstance(user_query, str):
            user_query = str(user_query)
        
        # 根據意圖類型執行相應的搜尋
        search_result = await execute_actual_search(user_query, intent_info)
        
        response = f"✓ 搜尋完成: {user_query}\n\n{search_result}"
        
        # 創建新的 messages 列表來更新狀態
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=response))
        
        logger.info(f"搜尋執行完成")
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }
        
    except Exception as e:
        logger.error(f"搜尋執行節點發生錯誤: {e}")
        error_response = f"搜尋執行失敗: {str(e)}"
        
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=error_response))
        
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }

async def execute_actual_search(user_query: str, intent_info: dict) -> str:
    """根據意圖執行實際搜尋"""
    try:
        # 直接調用與 interactive_demo 中相同的搜尋工具
        from ..tools.tender_search_tools import (
            async_search_tender_by_organization,
            async_search_tender_by_category,
            async_search_tender_comprehensive
        )
        
        if not intent_info:
            intent_info = {"type": "一般綜合搜尋", "keywords": []}
        
        intent_type = intent_info.get("type", "")
        keywords = intent_info.get("keywords", [])
        
        # 根據意圖類型選擇搜尋方式
        if "機關搜尋" in intent_type:
            # 提取機關名稱
            agencies = ["台電", "中華電信", "台灣銀行", "教育部", "經濟部", "交通部", "內政部", "財政部", "衛生福利部", "衛福部", "健保署"]
            org_name = None
            for keyword in keywords:
                if keyword in agencies:
                    org_name = keyword
                    break
            if not org_name and keywords:
                org_name = keywords[0]
            
            if org_name:
                # 直接調用異步搜尋函數
                return await async_search_tender_by_organization(org_name)
            else:
                return "未指定機關名稱，請提供具體的機關名稱。"
        
        elif "類別搜尋" in intent_type:
            # 類別搜尋
            category_mapping = {
                "數據相關": "大數據 資料分析 統計",
                "系統相關": "系統 軟體 應用程式", 
                "硬體相關": "設備 硬體 伺服器",
                "服務相關": "服務 維護 支援",
                "教育相關": "教育 訓練 課程",
                "建設相關": "建設 工程 營造"
            }
            
            search_terms = None
            for category, terms in category_mapping.items():
                if category in intent_type:
                    search_terms = terms
                    break
            
            if not search_terms and keywords:
                search_terms = " ".join(keywords[:3])
            
            if search_terms:
                return await async_search_tender_by_category(search_terms)
            else:
                return "未指定搜尋類別，請提供具體的類別名稱。"
        
        elif "預算金額搜尋" in intent_type:
            # 金額搜尋 - 暫時使用綜合搜尋
            return await async_search_tender_comprehensive(f"預算 金額 {user_query}")
        
        # 綜合搜尋
        return await async_search_tender_comprehensive(user_query)
        
    except Exception as e:
        logger.error(f"執行實際搜尋時發生錯誤: {e}")
        return f"搜尋過程中發生錯誤: {str(e)}"

def extract_amount_range(query: str) -> tuple:
    """從查詢中提取金額範圍"""
    import re
    
    # 尋找金額相關的數字
    numbers = re.findall(r'(\d+)', query)
    if not numbers:
        return None, None
    
    # 簡單的金額範圍推測邏輯
    if len(numbers) >= 2:
        min_amount = float(numbers[0])
        max_amount = float(numbers[1])
    elif len(numbers) == 1:
        amount = float(numbers[0])
        if "以上" in query or "超過" in query:
            min_amount = amount
            max_amount = amount * 10
        elif "以下" in query or "低於" in query:
            min_amount = 0
            max_amount = amount
        else:
            # 預設範圍
            min_amount = amount * 0.5
            max_amount = amount * 1.5
    else:
        return None, None
    
    return min_amount, max_amount

async def refine_results_node(state: State) -> State:
    """結果精煉節點"""
    try:
        logger.info("開始精煉搜尋結果")
        
        response = "正在精煉搜尋結果以提供更好的答案..."
        
        # 創建新的 messages 列表來更新狀態
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=response))
        
        logger.info(f"結果精煉完成")
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }
        
    except Exception as e:
        logger.error(f"結果精煉節點發生錯誤: {e}")
        error_response = f"結果精煉失敗: {str(e)}"
        
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=error_response))
        
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }

async def format_response_node(state: State) -> State:
    """回應格式化節點"""
    try:
        logger.info("開始格式化回應")
        
        # 從 messages 中提取最新的用戶查詢和搜尋結果
        user_query = ""
        search_result = ""
        
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_query = msg.content
                break
        
        # 查找搜尋結果（第三個 AI 訊息，即搜尋完成的訊息）
        ai_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage)]
        if len(ai_messages) >= 2:  # 意圖分析 + 搜尋結果
            search_msg = ai_messages[1]  # 第二個 AI 訊息是搜尋結果
            if isinstance(search_msg.content, str) and "✓ 搜尋完成:" in search_msg.content:
                # 提取搜尋結果部分
                parts = search_msg.content.split("\n\n", 1)
                if len(parts) > 1:
                    search_result = parts[1]  # 搜尋結果內容
        
        # 格式化最終回應
        if search_result.strip():
            # 如果有搜尋結果，使用實際結果
            formatted_response = f"""
基於您的查詢「{user_query}」，我找到了以下招標案：

{search_result}

💡 搜尋提示：
• 如需更詳細資訊，請提供更具體的搜尋條件
• 支援按機關、金額範圍、類別等條件搜尋
• 可以查詢特定時間範圍的招標案

感謝您的查詢！
            """.strip()
        else:
            # 如果沒有搜尋結果，提供通用回應
            formatted_response = f"""
基於您的查詢「{user_query}」，我已經完成了招標案搜尋分析。

目前系統正在處理您的搜尋請求，由於資料庫連接或配置問題，暫時無法提供具體的搜尋結果。

建議您：
• 檢查網路連接狀態
• 確認 Neo4j 資料庫是否正常運行
• 驗證 OpenAI API 金鑰設定

如果問題持續，請聯繫系統管理員。

感謝您的查詢！
            """.strip()
        
        # 創建新的 messages 列表來更新狀態
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=formatted_response))
        
        logger.info(f"回應格式化完成")
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }
        
    except Exception as e:
        logger.error(f"回應格式化節點發生錯誤: {e}")
        error_response = f"回應格式化失敗: {str(e)}"
        
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=error_response))
        
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }

async def handle_followup_node(state: State) -> State:
    """後續查詢處理節點"""
    try:
        logger.info("處理後續查詢")
        
        response = "正在處理您的後續查詢..."
        
        # 創建新的 messages 列表來更新狀態
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=response))
        
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }
        
    except Exception as e:
        logger.error(f"後續查詢處理節點發生錯誤: {e}")
        error_response = f"後續查詢處理失敗: {str(e)}"
        
        new_messages = list(state["messages"])
        new_messages.append(AIMessage(content=error_response))
        
        return {
            "messages": new_messages,
            "is_last_step": state.get("is_last_step", False)
        }
