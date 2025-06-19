"""
LLM 結果處理器

使用 LLM 來智能處理和格式化 Graphiti 搜尋結果
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMResultProcessor:
    """LLM 結果處理器，用於智能分析和格式化搜尋結果"""
    
    def __init__(self):
        self.client = None
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4")
        self._initialize_openai_client()
    
    def _initialize_openai_client(self):
        """初始化 OpenAI 客戶端"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = AsyncOpenAI(api_key=api_key)
                logger.info("成功初始化 OpenAI 客戶端")
            else:
                logger.warning("未找到 OPENAI_API_KEY，LLM 處理器將使用降級模式")
        except Exception as e:
            logger.error(f"初始化 OpenAI 客戶端失敗: {e}")
    
    def _get_search_type_prompt(self, search_type: str, query_params: Dict[str, Any]) -> str:
        """根據搜尋類型獲取對應的提示詞"""
        
        base_instruction = """你是一個政府招標案智能分析助手。請分析以下 Graphiti 知識圖譜的搜尋結果，並提供清晰、有用的回答。

重要原則：
1. 盡力從關係和實體資訊中提取有用內容
2. 即使資訊不完整，也要提供可獲得的部分資訊
3. 積極分析關係資訊，嘗試推斷招標案內容
4. 使用繁體中文回答，保持樂觀和有幫助的語調
5. 格式清晰易讀，優先提供有價值的資訊

分析策略：
- 關係如 "USES_TECHNOLOGY" 可能表示技術相關招標案
- 關係如 "HAS_BUDGET_AMOUNT" 可能包含預算資訊
- 關係如 "ORGANIZED_BY" 可能表示主辦機關
- 即使只有關係資訊，也要嘗試組合推斷可能的招標案內容

"""
        
        if search_type == "organization":
            org_name = query_params.get("organization_name", "")
            return base_instruction + f"""
搜尋類型：機關搜尋
查詢機關：{org_name}

**任務：從搜尋結果中找出與「{org_name}」相關的招標案**

機關匹配規則：
- "台電" → "台灣電力股份有限公司"、"台電"、"電力公司"
- "教育部" → "教育部"、"教育部相關單位"
- "交通部" → "交通部"、"交通部相關單位"
- "衛生福利部" → "衛生福利部"、"衛福部"
- "經濟部" → "經濟部"、"經濟部相關單位"

**重點指示：**
1. 仔細檢查每個搜尋結果中的機關資訊
2. 如果關係資訊中提到「招標機關是{org_name}」，那就是相關招標案
3. 如果實體名稱包含{org_name}的招標案，也要列出
4. 從關係描述中提取招標案的完整名稱
5. 不要忽略已經找到的相關資訊

分析方法：
- 查看 fact 欄位中是否提到「招標機關是{org_name}」
- 查看實體名稱是否包含招標案相關關鍵字
- 將相關的關係資訊組合成完整的招標案描述

回應格式：
找到以下與「{org_name}」相關的招標案：

1. 招標案名稱：[從關係或實體中提取的完整招標案名稱]
   機關：{org_name}
   金額：[如果有金額資訊]
   描述：[根據搜尋結果組合的描述]

**注意：如果搜尋結果中明確提到某招標案的機關是{org_name}，一定要列出來！**
"""
        
        elif search_type == "amount":
            min_amount = query_params.get("min_amount", 0)
            max_amount = query_params.get("max_amount", 0)
            return base_instruction + f"""
搜尋類型：金額範圍搜尋
金額範圍：{min_amount}-{max_amount}萬元

請從搜尋結果中找出預算金額在 {min_amount}-{max_amount}萬元範圍內的招標案。

特別注意：
- 仔細分析金額資訊，將「元」轉換為「萬元」
- 只列出符合金額範圍的案例
- 如果沒有完全符合的，說明最接近的案例

格式：
符合金額範圍的招標案：
1. [招標案名稱]
   機關：[機關名稱]
   金額：[具體金額]萬元
   描述：[描述]
"""
        
        elif search_type == "category":
            category = query_params.get("category", "")
            return base_instruction + f"""
搜尋類型：類別搜尋
搜尋類別：{category}

請從搜尋結果中找出與「{category}」相關的招標案，特別關注：
- 技術關鍵字匹配
- 採購內容相關性
- 專案描述中的相關字詞

格式：
找到以下「{category}」相關招標案：
1. [招標案名稱]
   機關：[機關名稱]
   金額：[金額]
   相關性：[說明為什麼與{category}相關]
   描述：[描述]
"""
        
        elif search_type == "comprehensive":
            query = query_params.get("query", "")
            return base_instruction + f"""
搜尋類型：綜合搜尋
查詢關鍵字：{query}

**特別注意：如果查詢包含完整的招標案名稱，請特別關注相關的關係資訊！**

**重要指示：**
1. 首先查找 entity_type 為 "TenderCase" 的實體
2. 仔細檢查 fact 欄位中是否包含查詢中的招標案名稱
3. 如果 fact 中提到查詢的招標案名稱，立即提取相關資訊：
   - 招標機關
   - 預算金額
   - 技術類型
4. 優先顯示與查詢直接相關的招標案

**查詢分析**：
- 如果查詢像「{query}」包含招標案全名，請從搜尋結果中找出所有提到此名稱的關係
- 特別關注 fact 欄位中包含「{query}」或其部分名稱的結果
- 如果找到相關的招標案資訊，按以下格式顯示：

找到查詢的招標案：

1. 招標案名稱：{query}
   機關：[從 fact 中提取的機關名稱]
   金額：[從 fact 中提取的預算金額]
   技術：[從 fact 中提取的技術資訊]
   描述：[根據搜尋結果組合的完整描述]

**如果沒有找到直接匹配，才顯示其他相關資訊。**
"""
        
        else:
            return base_instruction + """
請分析以下搜尋結果，提取有用的招標案資訊並整理成清晰的格式。
"""
    
    async def process_search_results(
        self, 
        results: List[Any], 
        search_type: str, 
        query_params: Dict[str, Any]
    ) -> str:
        """
        使用 LLM 處理搜尋結果
        
        Args:
            results: Graphiti 搜尋結果
            search_type: 搜尋類型 (organization, amount, category, comprehensive)
            query_params: 查詢參數
            
        Returns:
            LLM 處理後的格式化結果
        """
        
        if not self.client:
            # 降級到基本格式化
            return self._fallback_formatting(results, search_type, query_params)
        
        try:
            # 準備搜尋結果數據（限制數量以避免上下文超限）
            results_data = self._prepare_results_data(results)
            limited_results_data = results_data[:10]  # 處理前10個結果以包含更多相關資料
            
            # 獲取對應的提示詞
            system_prompt = self._get_search_type_prompt(search_type, query_params)
            
            # 構建用戶訊息（簡化格式）
            user_message = f"""
搜尋結果數據（前{len(limited_results_data)}個結果）：
{json.dumps(limited_results_data, ensure_ascii=False, indent=1)}

請根據上述搜尋結果，按照指示提供清晰的分析和回答。
"""
            
            # 調用 LLM（使用環境變數中的模型名稱）
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else "LLM 回應為空"
            
        except Exception as e:
            logger.error(f"LLM 處理搜尋結果時發生錯誤: {e}")
            return self._fallback_formatting(results, search_type, query_params)
    
    def _prepare_results_data(self, results: List[Any]) -> List[Dict[str, Any]]:
        """準備搜尋結果數據供 LLM 分析"""
        prepared_data = []
        
        for result in results:
            result_info = {}
            result_type = type(result).__name__
            
            # 處理 EntityEdge（關係邊）
            if result_type == 'EntityEdge':
                result_info['type'] = 'entity_edge'
                
                # 嘗試獲取關係資訊
                if hasattr(result, 'fact'):
                    result_info['fact'] = result.fact
                
                # 嘗試獲取相關實體資訊
                if hasattr(result, 'source_node') and result.source_node:
                    source = result.source_node
                    if hasattr(source, 'name'):
                        result_info['source_entity'] = source.name
                    if hasattr(source, 'entity_type'):
                        result_info['source_type'] = source.entity_type
                
                if hasattr(result, 'target_node') and result.target_node:
                    target = result.target_node
                    if hasattr(target, 'name'):
                        result_info['target_entity'] = target.name
                    if hasattr(target, 'entity_type'):
                        result_info['target_type'] = target.entity_type
                
                # 嘗試獲取關係類型
                if hasattr(result, 'relation_type'):
                    result_info['relation_type'] = result.relation_type
                    
            # 處理 Entity（實體節點）
            elif hasattr(result, 'name'):
                result_info['name'] = result.name
                result_info['type'] = 'entity'
                
                if hasattr(result, 'summary'):
                    result_info['summary'] = result.summary
                if hasattr(result, 'entity_type'):
                    result_info['entity_type'] = result.entity_type
                    
            # 處理其他類型（如純關係）
            elif hasattr(result, 'fact'):
                result_info['fact'] = result.fact
                result_info['type'] = 'relationship'
            
            # 添加通用屬性
            for attr in ['uuid', 'created_at']:
                if hasattr(result, attr):
                    result_info[attr] = str(getattr(result, attr))
            
            # 添加調試資訊
            result_info['debug_type'] = result_type
            result_info['debug_attributes'] = [attr for attr in dir(result) if not attr.startswith('_')]
            
            if result_info:  # 只添加非空的結果
                prepared_data.append(result_info)
        
        return prepared_data
    
    def _fallback_formatting(
        self, 
        results: List[Any], 
        search_type: str, 
        query_params: Dict[str, Any]
    ) -> str:
        """當 LLM 不可用時的降級格式化"""
        
        if not results:
            return "未找到相關招標案。"
        
        # 基本的結果整理
        entities = []
        relationships = []
        
        for result in results:
            if hasattr(result, 'name') and any(keyword in result.name for keyword in ["招標案", "專案", "系統", "平台", "計畫"]):
                entities.append(result.name)
            elif hasattr(result, 'fact'):
                relationships.append(result.fact)
        
        formatted_result = ""
        
        if entities:
            formatted_result += "找到以下招標案相關實體：\n"
            for i, entity in enumerate(entities, 1):
                formatted_result += f"{i}. {entity}\n"
            formatted_result += "\n"
        
        if relationships:
            formatted_result += "相關資訊：\n"
            for i, rel in enumerate(relationships[:5], 1):
                formatted_result += f"{i}. {rel}\n"
        
        if not formatted_result:
            formatted_result = "未找到明確的招標案資訊。請嘗試更具體的搜尋關鍵字。"
        
        return formatted_result

# 全域實例
_llm_processor = None

def get_llm_processor() -> LLMResultProcessor:
    """獲取 LLM 處理器實例（單例模式）"""
    global _llm_processor
    if _llm_processor is None:
        _llm_processor = LLMResultProcessor()
    return _llm_processor
