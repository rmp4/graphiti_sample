"""
招標搜尋工具模組

提供各種招標資料搜尋功能，整合 Graphiti 知識圖譜
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import os
from datetime import datetime, timezone
from langchain_core.tools import tool  
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_EPISODE_MENTIONS
from .llm_result_processor import get_llm_processor

logger = logging.getLogger(__name__)

def create_graphiti_client() -> Optional[Graphiti]:
    """創建 Graphiti 客戶端實例"""
    try:
        # 從環境變數讀取 Neo4j 和 OpenAI 設定
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        logger.info(f"嘗試連接 Neo4j: {neo4j_uri}, 用戶: {neo4j_user}")
        
        if not openai_api_key:
            logger.warning("未找到 OPENAI_API_KEY，將使用模擬模式")
            return None
            
        # 創建 Graphiti 實例（使用正確的初始化方式）
        graphiti = Graphiti(
            neo4j_uri,
            neo4j_user,
            neo4j_password,
        )
        
        logger.info("成功創建 Graphiti 客戶端")
        return graphiti
        
    except Exception as e:
        logger.error(f"創建 Graphiti 客戶端時發生錯誤: {e}")
        return None

# 全域 Graphiti 客戶端實例
_graphiti_client = None

def get_graphiti_client() -> Optional[Graphiti]:
    """獲取 Graphiti 客戶端實例（單例模式）"""
    global _graphiti_client
    if _graphiti_client is None:
        _graphiti_client = create_graphiti_client()
    return _graphiti_client

def extract_amount_from_text(text: str) -> Optional[float]:
    """從文字中提取金額數值（萬元）"""
    import re
    
    # 尋找各種金額格式
    patterns = [
        r'(\d{1,3}(?:,\d{3})*)\s*萬',  # xxx萬格式
        r'新臺幣\s*(\d{1,3}(?:,\d{3})*(?:,\d{3})*)\s*元',  # 新臺幣xxx元格式
        r'(\d{1,3}(?:,\d{3})*(?:,\d{3})*)\s*元',  # xxx元格式
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.replace(',', ''))
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                # 如果是元，轉換為萬元
                if '元' in text and '萬' not in text:
                    amount = amount / 10000
                return amount
            except ValueError:
                continue
    
    return None

def format_tender_results(results: List[Any], min_amount: Optional[float] = None, max_amount: Optional[float] = None) -> str:
    """格式化招標搜尋結果為可讀字串，可選擇按金額過濾"""
    if not results:
        return "未找到相關招標案"
    
    # 篩選出真正的招標案實體，過濾關係節點
    tender_entities = []
    amount_info = []
    other_info = []
    
    for result in results:
        if hasattr(result, 'name'):
            name = result.name
            # 檢查是否為招標案相關的實體
            if any(keyword in name for keyword in ["招標案", "專案", "系統", "平台", "計畫", "採購"]):
                tender_entities.append(result)
            elif hasattr(result, 'fact') and result.fact:
                # 這是關係資訊，檢查是否包含金額
                fact = result.fact
                if any(keyword in fact for keyword in ["金額", "預算", "萬", "元"]):
                    amount_info.append(fact)
                else:
                    other_info.append(fact)
        elif hasattr(result, 'fact'):
            # 這是邊/關係對象
            fact = result.fact
            if any(keyword in fact for keyword in ["金額", "預算", "萬", "元"]):
                amount_info.append(fact)
            else:
                other_info.append(fact)
    
    formatted_results = ""
    
    # 格式化招標案實體
    if tender_entities:
        formatted_results += "找到以下招標案：\n"
        for i, entity in enumerate(tender_entities, 1):
            tender_name = entity.name
            description = getattr(entity, 'summary', '詳細資料請查看完整招標文件')
            
            # 嘗試從名稱中提取額外資訊
            amount = "請查看詳細資料"
            agency = "請查看詳細資料"
            
            # 如果名稱包含機關信息
            if "臺北市" in tender_name:
                agency = "臺北市政府相關單位"
            elif "高雄市" in tender_name:
                agency = "高雄市政府相關單位"
            elif "新北市" in tender_name:
                agency = "新北市政府相關單位"
            elif "桃園市" in tender_name:
                agency = "桃園市政府相關單位"
            elif "臺中市" in tender_name:
                agency = "臺中市政府相關單位"
            elif "科技部" in tender_name:
                agency = "科技部"
            
            formatted_results += f"{i}. {tender_name}\n"
            formatted_results += f"   機關: {agency}\n"
            formatted_results += f"   金額: {amount}\n"
            formatted_results += f"   描述: {description}\n\n"
    
    # 如果是金額搜尋，顯示符合範圍的金額資訊
    if min_amount is not None and max_amount is not None and amount_info:
        matching_amounts = []
        for info in amount_info:
            amount = extract_amount_from_text(info)
            if amount and min_amount <= amount <= max_amount:
                matching_amounts.append((info, amount))
        
        if matching_amounts:
            if not tender_entities:
                formatted_results += f"找到符合金額範圍 {min_amount}-{max_amount}萬 的招標案：\n"
            else:
                formatted_results += f"\n符合金額範圍 {min_amount}-{max_amount}萬 的相關資訊：\n"
            
            for i, (info, amount) in enumerate(matching_amounts, 1):
                formatted_results += f"{i}. {info} (約{amount:.1f}萬元)\n"
            formatted_results += "\n"
        else:
            if not tender_entities:
                formatted_results += f"未找到金額範圍 {min_amount}-{max_amount}萬 的招標案。\n"
                formatted_results += "以下是找到的其他金額資訊：\n"
                for i, info in enumerate(amount_info[:3], 1):
                    amount = extract_amount_from_text(info)
                    amount_str = f" (約{amount:.1f}萬元)" if amount else ""
                    formatted_results += f"{i}. {info}{amount_str}\n"
    
    # 如果沒有找到招標案實體，顯示關係資訊
    elif not tender_entities and (amount_info or other_info):
        all_info = amount_info + other_info
        formatted_results += "找到相關資訊：\n"
        for i, info in enumerate(all_info[:5], 1):  # 只顯示前5個
            formatted_results += f"{i}. {info}\n"
        formatted_results += "\n💡 提示：可能需要更具體的搜尋關鍵字來找到招標案實體\n"
    
    # 如果都沒有找到
    elif not tender_entities and not amount_info and not other_info:
        formatted_results = "未找到相關招標案。請嘗試其他搜尋關鍵字。"
    
    return formatted_results

def run_async_search(search_func, *args, **kwargs):
    """執行異步搜尋函數的包裝器"""
    try:
        # 直接調用異步函數的同步版本
        # 由於 LangGraph 工具需要同步調用，我們直接在這裡處理異步邏輯
        
        graphiti_client = get_graphiti_client()
        
        if not graphiti_client:
            return "搜尋工具暫時無法使用，請稍後再試"
        
        # 根據函數名稱確定搜尋類型
        func_name = search_func.__name__ if hasattr(search_func, '__name__') else str(search_func)
        
        if 'organization' in func_name and args:
            org_name = args[0]
            # 統一使用 async_search_tender_by_organization 來確保一致性
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_search_tender_by_organization(org_name))
            finally:
                loop.close()
        
        elif 'category' in func_name and args:
            category = args[0]
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(graphiti_client.search(f"{category} 採購 招標", num_results=10))
                return f"找到 {len(results)} 個與「{category}」相關的招標案"
            finally:
                loop.close()
        
        elif 'comprehensive' in func_name and args:
            query = args[0]
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(graphiti_client.search(query, num_results=10))
                return f"綜合搜尋「{query}」找到 {len(results)} 個相關結果"
            finally:
                loop.close()
        
        else:
            return "不支援的搜尋類型"
            
    except Exception as e:
        logger.error(f"執行搜尋時發生錯誤: {e}")
        return f"搜尋時發生錯誤: {str(e)}"

async def async_search_tender_by_organization(organization_name: str) -> str:
    """異步根據機關名稱搜尋招標案"""
    graphiti_client = get_graphiti_client()
    llm_processor = get_llm_processor()
    
    if not graphiti_client:
        # 降級到模擬模式
        return f"模擬搜尋：找到與機關「{organization_name}」相關的招標案\n" + \
               f"1. {organization_name}資訊設備採購案\n" + \
               f"   機關: {organization_name}\n" + \
               f"   金額: 150萬\n" + \
               f"   描述: 辦公室資訊設備更新採購\n\n"

    try:
        # 搜尋與該機關相關的招標案
        tender_query = f"{organization_name} 招標 採購"
        tender_results = await graphiti_client.search(
            tender_query,
            num_results=15
        )
        
        # 使用 LLM 處理搜尋結果
        query_params = {"organization_name": organization_name}
        return await llm_processor.process_search_results(
            tender_results, 
            "organization", 
            query_params
        )
            
    except Exception as e:
        logger.error(f"搜尋機關招標案時發生錯誤: {e}")
        return f"搜尋機關 {organization_name} 時發生錯誤: {str(e)}"

@tool
def search_tender_by_organization(organization_name: str) -> str:
    """根據機關名稱搜尋招標案"""
    return run_async_search(async_search_tender_by_organization, organization_name)

async def async_search_tender_by_amount(min_amount: float, max_amount: float) -> str:
    """異步根據金額範圍搜尋招標案"""
    graphiti_client = get_graphiti_client()
    
    if not graphiti_client:
        # 降級到模擬模式
        return f"模擬搜尋：金額範圍 {min_amount}-{max_amount}萬 的招標案\n" + \
               f"1. 預算符合範圍的採購案A\n" + \
               f"   機關: 某政府單位\n" + \
               f"   金額: {(min_amount + max_amount) / 2}萬\n" + \
               f"   描述: 金額在指定範圍內的採購案\n\n"

    try:
        query = f"預算 金額 {min_amount}萬 {max_amount}萬 採購"
        results = await graphiti_client.search(query, num_results=15)
        return format_tender_results(results)
        
    except Exception as e:
        logger.error(f"搜尋金額範圍招標案時發生錯誤: {e}")
        return f"搜尋金額範圍 {min_amount}-{max_amount}萬 時發生錯誤: {str(e)}"

@tool
def search_tender_by_amount(min_amount: float, max_amount: float) -> str:
    """根據金額範圍搜尋招標案"""
    return run_async_search(async_search_tender_by_amount, min_amount, max_amount)

async def async_search_tender_by_category(category: str) -> str:
    """異步根據採購類別搜尋招標案"""
    graphiti_client = get_graphiti_client()
    
    if not graphiti_client:
        # 降級到模擬模式
        return f"模擬搜尋：類別「{category}」的招標案\n" + \
               f"1. {category}相關採購案\n" + \
               f"   機關: 相關主管機關\n" + \
               f"   金額: 200萬\n" + \
               f"   描述: {category}類型的政府採購\n\n"

    try:
        query = f"{category} 採購 招標"
        results = await graphiti_client.search(query, num_results=10)
        return format_tender_results(results)
        
    except Exception as e:
        logger.error(f"搜尋類別招標案時發生錯誤: {e}")
        return f"搜尋類別 {category} 時發生錯誤: {str(e)}"

@tool
def search_tender_by_category(category: str) -> str:
    """根據採購類別搜尋招標案"""
    return run_async_search(async_search_tender_by_category, category)

async def async_search_tender_by_date_range(start_date: str, end_date: str) -> str:
    """異步根據日期範圍搜尋招標案 - 支援擴展的日期類型"""
    graphiti_client = get_graphiti_client()
    
    if not graphiti_client:
        # 降級到模擬模式
        return f"模擬搜尋：日期範圍 {start_date} 到 {end_date} 的招標案\n" + \
               f"1. 期間內的招標案\n" + \
               f"   機關: 時間範圍內的機關\n" + \
               f"   金額: 120萬\n" + \
               f"   描述: 在指定時間範圍內公告的招標案\n\n"

    try:
        # 擴展搜尋查詢以包含多種日期類型
        query = f"公告日期 開標時間 截止投標 {start_date} {end_date} 招標"
        results = await graphiti_client.search(query, num_results=15)
        return format_tender_results(results)
        
    except Exception as e:
        logger.error(f"搜尋日期範圍招標案時發生錯誤: {e}")
        return f"搜尋日期範圍 {start_date} 到 {end_date} 時發生錯誤: {str(e)}"

@tool  
def search_tender_by_date_range(start_date: str, end_date: str) -> str:
    """根據日期範圍搜尋招標案"""
    return run_async_search(async_search_tender_by_date_range, start_date, end_date)

async def async_search_tender_comprehensive(query: str) -> str:
    """異步綜合搜尋招標案"""
    graphiti_client = get_graphiti_client()
    llm_processor = get_llm_processor()
    
    if not graphiti_client:
        # 降級到模擬模式
        return f"模擬搜尋：關鍵字「{query}」的招標案\n" + \
               f"1. 與'{query}'相關的招標案\n" + \
               f"   機關: 相關機關\n" + \
               f"   金額: 180萬\n" + \
               f"   描述: 包含'{query}'關鍵字的採購案\n\n"

    try:
        results = await graphiti_client.search(query, num_results=15)
        
        # 使用 LLM 處理搜尋結果
        query_params = {"query": query}
        return await llm_processor.process_search_results(
            results, 
            "comprehensive", 
            query_params
        )
        
    except Exception as e:
        logger.error(f"綜合搜尋招標案時發生錯誤: {e}")
        return f"綜合搜尋 '{query}' 時發生錯誤: {str(e)}"

@tool
def search_tender_comprehensive(query: str) -> str:
    """綜合搜尋招標案"""
    return run_async_search(async_search_tender_comprehensive, query)

# 額外的工具函數用於 LangGraph 整合

async def get_tender_statistics() -> Dict[str, Any]:
    """獲取招標案統計資訊"""
    graphiti_client = get_graphiti_client()
    
    if not graphiti_client:
        return {
            "total_tenders": 1250,
            "active_tenders": 85,
            "total_agencies": 45,
            "status": "模擬模式"
        }

    try:
        # 搜尋所有招標相關節點來獲取統計
        all_tenders = await graphiti_client.search("招標 採購", num_results=1000)
        active_tenders = await graphiti_client.search("招標中 進行中", num_results=100)
        
        return {
            "total_tenders": len(all_tenders),
            "active_tenders": len(active_tenders),
            "total_agencies": len(set(r.get('agency', '') for r in all_tenders if isinstance(r, dict))),
            "status": "真實資料"
        }
        
    except Exception as e:
        logger.error(f"獲取統計資訊時發生錯誤: {e}")
        return {"error": str(e)}

@tool
def get_tender_stats() -> str:
    """獲取招標案統計資訊"""
    try:
        # 簡化版本，直接返回模擬統計資訊
        return f"招標案統計資訊：\n" + \
               f"總招標案數: 1250\n" + \
               f"進行中招標案: 85\n" + \
               f"參與機關數: 45\n" + \
               f"資料狀態: 模擬模式"
    except Exception as e:
        return f"獲取統計資訊失敗: {str(e)}"

# 新增：支援擴展實體類型的搜尋工具

async def async_search_tender_by_procurement_type(procurement_type: str) -> str:
    """異步根據採購類型搜尋招標案（支援分類實體）"""
    graphiti_client = get_graphiti_client()
    
    if not graphiti_client:
        return f"模擬搜尋：採購類型「{procurement_type}」的招標案\n" + \
               f"1. {procurement_type}採購案範例\n" + \
               f"   分類: {procurement_type}\n" + \
               f"   機關: 相關主管機關\n" + \
               f"   金額: 300萬\n\n"

    try:
        # 搜尋包含採購類型的招標案
        query = f"{procurement_type} 採購類型 分類 招標"
        results = await graphiti_client.search(query, num_results=15)
        
        formatted_result = f"找到採購類型「{procurement_type}」的相關招標案：\n\n"
        
        if results:
            formatted_result += format_tender_results(results)
        else:
            formatted_result += f"未找到「{procurement_type}」類型的招標案，請嘗試其他關鍵字。"
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"搜尋採購類型招標案時發生錯誤: {e}")
        return f"搜尋採購類型 {procurement_type} 時發生錯誤: {str(e)}"

@tool
def search_tender_by_procurement_type(procurement_type: str) -> str:
    """根據採購類型搜尋招標案（工程類/財物類/勞務類）"""
    return run_async_search(async_search_tender_by_procurement_type, procurement_type)

async def async_search_tender_by_specific_date_type(date_type: str, date_value: str) -> str:
    """異步根據特定日期類型搜尋招標案"""
    graphiti_client = get_graphiti_client()
    
    if not graphiti_client:
        return f"模擬搜尋：{date_type}為「{date_value}」的招標案\n" + \
               f"1. 符合日期條件的招標案\n" + \
               f"   {date_type}: {date_value}\n" + \
               f"   機關: 相關機關\n" + \
               f"   金額: 250萬\n\n"

    try:
        # 根據不同的日期類型構建查詢
        date_type_mapping = {
            "公告日期": "announcement_date",
            "截止投標": "bid_deadline", 
            "開標時間": "bid_opening_time",
            "履約期限": "contract_period"
        }
        
        query_term = date_type_mapping.get(date_type, date_type)
        query = f"{query_term} {date_type} {date_value} 招標"
        
        results = await graphiti_client.search(query, num_results=15)
        
        formatted_result = f"找到{date_type}為「{date_value}」的招標案：\n\n"
        
        if results:
            formatted_result += format_tender_results(results)
        else:
            formatted_result += f"未找到{date_type}為「{date_value}」的招標案。"
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"搜尋特定日期類型招標案時發生錯誤: {e}")
        return f"搜尋{date_type} {date_value} 時發生錯誤: {str(e)}"

@tool  
def search_tender_by_specific_date_type(date_type: str, date_value: str) -> str:
    """根據特定日期類型搜尋招標案（公告日期/截止投標/開標時間/履約期限）"""
    return run_async_search(async_search_tender_by_specific_date_type, date_type, date_value)

async def async_search_tender_by_decision_method(decision_method: str) -> str:
    """異步根據決標方式搜尋招標案"""
    graphiti_client = get_graphiti_client()
    
    if not graphiti_client:
        return f"模擬搜尋：決標方式「{decision_method}」的招標案\n" + \
               f"1. 使用{decision_method}的招標案\n" + \
               f"   決標方式: {decision_method}\n" + \
               f"   機關: 相關機關\n" + \
               f"   金額: 400萬\n\n"

    try:
        query = f"{decision_method} 決標方式 招標"
        results = await graphiti_client.search(query, num_results=15)
        
        formatted_result = f"找到決標方式為「{decision_method}」的招標案：\n\n"
        
        if results:
            formatted_result += format_tender_results(results)
        else:
            formatted_result += f"未找到決標方式為「{decision_method}」的招標案。"
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"搜尋決標方式招標案時發生錯誤: {e}")
        return f"搜尋決標方式 {decision_method} 時發生錯誤: {str(e)}"

@tool
def search_tender_by_decision_method(decision_method: str) -> str:
    """根據決標方式搜尋招標案（最有利標/最低標/準用最有利標等）"""
    return run_async_search(async_search_tender_by_decision_method, decision_method)

async def async_search_related_entities(entity_name: str, relationship_type: str = "all") -> str:
    """異步搜尋與指定實體相關的其他實體"""
    graphiti_client = get_graphiti_client()
    
    if not graphiti_client:
        return f"模擬搜尋：與「{entity_name}」相關的實體\n" + \
               f"關係類型: {relationship_type}\n" + \
               f"找到相關實體：招標案A、機關B、金額C\n\n"

    try:
        # 根據關係類型調整查詢
        if relationship_type == "hosts":
            query = f"{entity_name} 主辦 招標案"
        elif relationship_type == "belongs_to_category":
            query = f"{entity_name} 分類 類別"
        elif relationship_type == "has_budget":
            query = f"{entity_name} 預算 金額"
        else:
            query = f"{entity_name} 相關 關聯"
        
        results = await graphiti_client.search(query, num_results=20)
        
        formatted_result = f"找到與「{entity_name}」相關的實體：\n\n"
        
        if results:
            # 分類顯示不同類型的相關實體
            organizations = []
            tenders = []
            amounts = []
            dates = []
            categories = []
            others = []
            
            for result in results:
                if hasattr(result, 'name'):
                    name = result.name
                    if any(keyword in name for keyword in ["招標案", "採購", "專案", "系統", "平台"]):
                        tenders.append(name)
                    elif any(keyword in name for keyword in ["政府", "機關", "部", "局", "委員會"]):
                        organizations.append(name)
                    elif any(keyword in name for keyword in ["金額", "預算", "萬", "元"]):
                        amounts.append(name)
                    elif any(keyword in name for keyword in ["日期", "時間", "期限"]):
                        dates.append(name)
                    elif any(keyword in name for keyword in ["分類", "類別", "性質"]):
                        categories.append(name)
                    else:
                        others.append(name)
            
            if organizations:
                formatted_result += f"相關機關：\n"
                for org in organizations[:3]:
                    formatted_result += f"  • {org}\n"
                formatted_result += "\n"
            
            if tenders:
                formatted_result += f"相關招標案：\n"
                for tender in tenders[:3]:
                    formatted_result += f"  • {tender}\n"
                formatted_result += "\n"
            
            if amounts:
                formatted_result += f"相關金額：\n"
                for amount in amounts[:3]:
                    formatted_result += f"  • {amount}\n"
                formatted_result += "\n"
            
            if dates:
                formatted_result += f"相關日期：\n"
                for date in dates[:3]:
                    formatted_result += f"  • {date}\n"
                formatted_result += "\n"
            
            if categories:
                formatted_result += f"相關分類：\n"
                for category in categories[:3]:
                    formatted_result += f"  • {category}\n"
                formatted_result += "\n"
                    
            if not any([organizations, tenders, amounts, dates, categories]):
                formatted_result += "未找到明確的相關實體。\n"
                if others:
                    formatted_result += "其他可能相關的資訊：\n"
                    for other in others[:5]:
                        formatted_result += f"  • {other}\n"
        else:
            formatted_result += f"未找到與「{entity_name}」相關的實體。"
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"搜尋相關實體時發生錯誤: {e}")
        return f"搜尋與 {entity_name} 相關的實體時發生錯誤: {str(e)}"

@tool
def search_related_entities(entity_name: str, relationship_type: str = "all") -> str:
    """搜尋與指定實體相關的其他實體（支援關係類型過濾）"""
    return run_async_search(async_search_related_entities, entity_name, relationship_type)

# 實體關係類型常數（與 tender_entities.py 中的定義對應）
RELATIONSHIP_TYPES = {
    "機關與標案": ["hosts", "organizes", "supervises", "participates_in"],
    "標案與分類": ["belongs_to_category", "has_procurement_type", "classified_as"],
    "標案與日期": ["announced_on", "opens_bid_on", "deadline_on", "contract_period", "starts_on", "ends_on"],
    "標案與金額": ["has_budget", "has_estimated_cost", "awarded_for"]
}

@tool
def get_supported_relationship_types() -> str:
    """獲取支援的實體關係類型列表"""
    result = "支援的實體關係類型：\n\n"
    
    for category, relations in RELATIONSHIP_TYPES.items():
        result += f"{category}：\n"
        for relation in relations:
            result += f"  • {relation}\n"
        result += "\n"
    
    result += "使用方式：在 search_related_entities 函數中指定 relationship_type 參數\n"
    result += "例如：search_related_entities('台灣電力公司', 'hosts')"
    
    return result
