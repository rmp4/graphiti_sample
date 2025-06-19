"""
查詢意圖分析器
用於分析使用者自然語言查詢的意圖並提取參數
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """查詢意圖類型"""
    ORGANIZATION = "organization"  # 機關搜尋
    AMOUNT = "amount"             # 金額搜尋
    CATEGORY = "category"         # 類別搜尋
    DATE = "date"                 # 日期搜尋
    COMPREHENSIVE = "comprehensive"  # 綜合搜尋
    UNKNOWN = "unknown"           # 未知意圖

@dataclass
class IntentAnalysisResult:
    """意圖分析結果"""
    intent: QueryIntent
    confidence: float  # 信心度 0-1
    parameters: Dict[str, Any]
    reasoning: str
    suggestions: List[str]

class QueryIntentAnalyzer:
    """查詢意圖分析器"""
    
    def __init__(self):
        self.setup_patterns()
        self.setup_keywords()
    
    def setup_patterns(self):
        """設定匹配模式"""
        # 機關名稱模式
        self.org_patterns = [
            r'(台灣?電力|台電|電力公司)',
            r'(中華郵政|郵局)',
            r'(交通部|運輸署|公路總局)',
            r'(教育部|學校|大學|國小|國中|高中)',
            r'(衛生?福利部|醫院|衛生局)',
            r'(內政部|警察|消防)',
            r'(財政部|稅務|國稅局)',
            r'(經濟部|工業局|商業司)',
            r'(勞動部|勞工)',
            r'(環保署|環境部)',
            r'(水利署|水公司)',
            r'(市政府|縣政府|區公所|鄉公所)',
            r'(\w+公司|\w+機構|\w+單位|\w+部門)'
        ]
        
        # 金額模式
        self.amount_patterns = [
            r'(\d+(?:[,，]\d+)*)\s*(?:萬|万)',
            r'(\d+(?:[,，]\d+)*)\s*(?:元|塊)',
            r'預算\s*(?:在|為|是|約|大約)?\s*(\d+(?:[,，]\d+)*)',
            r'金額\s*(?:在|為|是|約|大約)?\s*(\d+(?:[,，]\d+)*)',
            r'(\d+(?:[,，]\d+)*)\s*(?:到|至|~|－|-)\s*(\d+(?:[,，]\d+)*)',
            r'(?:超過|大於|>)\s*(\d+(?:[,，]\d+)*)',
            r'(?:小於|少於|<)\s*(\d+(?:[,，]\d+)*)',
            r'(?:以上|以下)\s*(\d+(?:[,，]\d+)*)'
        ]
        
        # 類別模式
        self.category_patterns = [
            r'(電腦|資訊|軟體|系統|網路|IT)',
            r'(建築|工程|營建|土木|裝修)',
            r'(醫療|藥品|醫療器材|健康)',
            r'(教育|教學|培訓|課程)',
            r'(清潔|環保|垃圾|廢棄物)',
            r'(安全|保全|監控|警衛)',
            r'(運輸|交通|車輛|道路)',
            r'(辦公|文具|用品|設備)',
            r'(食品|餐飲|膳食|營養)',
            r'(能源|電力|水電|瓦斯)',
            r'(印刷|文件|紙張|出版)',
            r'(維修|保養|服務|技術)',
            r'(研究|開發|創新|科技)',
            r'(設計|規劃|顧問|諮詢)'
        ]
        
        # 日期模式
        self.date_patterns = [
            r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})[日號]?',
            r'(\d{1,2})[月/\-](\d{1,2})[日號]?',
            r'(今年|去年|前年|明年)',
            r'(本月|上月|下月|這個月|上個月|下個月)',
            r'(最近|近期|近來)',
            r'(\d+)\s*(?:天|日|周|週|月|年)\s*(?:內|前|後)',
            r'(\d{4})\s*年',
            r'(\d{1,2})\s*月'
        ]
    
    def setup_keywords(self):
        """設定關鍵字"""
        self.intent_keywords = {
            QueryIntent.ORGANIZATION: [
                '機關', '單位', '部門', '公司', '政府', '公所', '署', '局', '處', '科', '組',
                '台電', '郵局', '學校', '醫院', '警察', '消防', '法院', '銀行'
            ],
            QueryIntent.AMOUNT: [
                '金額', '預算', '價格', '費用', '成本', '萬', '元', '塊', '錢',
                '便宜', '昂貴', '高價', '低價', '划算', '經濟'
            ],
            QueryIntent.CATEGORY: [
                '採購', '招標', '類別', '種類', '類型', '項目', '產品', '服務',
                '電腦', '建築', '醫療', '教育', '清潔', '安全', '運輸', '辦公'
            ],
            QueryIntent.DATE: [
                '日期', '時間', '年', '月', '日', '最近', '近期', '今年', '去年',
                '本月', '上月', '公告', '截止', '期限', '時程'
            ]
        }
    
    def analyze_intent(self, query: str) -> IntentAnalysisResult:
        """分析查詢意圖"""
        query = query.strip()
        if not query:
            return IntentAnalysisResult(
                intent=QueryIntent.UNKNOWN,
                confidence=0.0,
                parameters={},
                reasoning="查詢為空",
                suggestions=["請輸入您想搜尋的內容"]
            )
        
        # 分析各種意圖的可能性
        intent_scores = self._calculate_intent_scores(query)
        
        # 找到最高分的意圖
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent_type, confidence = best_intent
        
        # 提取相應的參數
        parameters = self._extract_parameters(query, intent_type)
        
        # 生成解釋和建議
        reasoning = self._generate_reasoning(query, intent_type, confidence, parameters)
        suggestions = self._generate_suggestions(query, intent_type, parameters)
        
        return IntentAnalysisResult(
            intent=intent_type,
            confidence=confidence,
            parameters=parameters,
            reasoning=reasoning,
            suggestions=suggestions
        )
    
    def _calculate_intent_scores(self, query: str) -> Dict[QueryIntent, float]:
        """計算各種意圖的分數"""
        scores = {intent: 0.0 for intent in QueryIntent}
        query_lower = query.lower()
        
        # 基於關鍵字的分數計算
        for intent, keywords in self.intent_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in query_lower)
            scores[intent] += keyword_count * 0.3
        
        # 基於模式匹配的分數計算
        
        # 機關模式匹配
        for pattern in self.org_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                scores[QueryIntent.ORGANIZATION] += 0.5
        
        # 金額模式匹配
        for pattern in self.amount_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                scores[QueryIntent.AMOUNT] += 0.4
        
        # 類別模式匹配
        for pattern in self.category_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                scores[QueryIntent.CATEGORY] += 0.3
        
        # 日期模式匹配
        for pattern in self.date_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                scores[QueryIntent.DATE] += 0.4
        
        # 特殊規則調整
        if any(word in query_lower for word in ['找', '搜尋', '查詢', '尋找']):
            # 如果包含搜尋詞但沒有明確意圖，提高綜合搜尋分數
            if max(scores.values()) < 0.3:
                scores[QueryIntent.COMPREHENSIVE] += 0.4
        
        # 正規化分數
        max_score = max(scores.values())
        if max_score > 0:
            for intent in scores:
                scores[intent] = min(scores[intent] / (max_score + 0.1), 1.0)
        
        # 如果所有分數都很低，設為未知意圖
        if max(scores.values()) < 0.2:
            scores[QueryIntent.UNKNOWN] = 0.8
        
        return scores
    
    def _extract_parameters(self, query: str, intent: QueryIntent) -> Dict[str, Any]:
        """根據意圖提取參數"""
        parameters = {}
        
        if intent == QueryIntent.ORGANIZATION:
            parameters.update(self._extract_organization_params(query))
        elif intent == QueryIntent.AMOUNT:
            parameters.update(self._extract_amount_params(query))
        elif intent == QueryIntent.CATEGORY:
            parameters.update(self._extract_category_params(query))
        elif intent == QueryIntent.DATE:
            parameters.update(self._extract_date_params(query))
        elif intent == QueryIntent.COMPREHENSIVE:
            parameters['query'] = query
        
        return parameters
    
    def _extract_organization_params(self, query: str) -> Dict[str, Any]:
        """提取機關相關參數"""
        params = {}
        
        # 嘗試匹配機關名稱
        for pattern in self.org_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                params['organization_name'] = match.group(1)
                break
        
        # 如果沒有找到具體機關名稱，嘗試提取通用詞彙
        if 'organization_name' not in params:
            org_keywords = ['機關', '單位', '部門', '公司', '政府']
            for keyword in org_keywords:
                if keyword in query:
                    # 嘗試找到機關名稱前後的文字
                    pattern = rf'(\w+){keyword}|\w+{keyword}(\w+)'
                    match = re.search(pattern, query)
                    if match:
                        org_name = match.group(1) or match.group(2)
                        if org_name:
                            params['organization_name'] = org_name + keyword
                        break
        
        return params
    
    def _extract_amount_params(self, query: str) -> Dict[str, Any]:
        """提取金額相關參數"""
        params = {}
        
        # 提取金額範圍
        range_pattern = r'(\d+(?:[,，]\d+)*)\s*(?:到|至|~|－|-)\s*(\d+(?:[,，]\d+)*)'
        range_match = re.search(range_pattern, query)
        if range_match:
            min_amount = float(range_match.group(1).replace(',', '').replace('，', ''))
            max_amount = float(range_match.group(2).replace(',', '').replace('，', ''))
            params['min_amount'] = min_amount
            params['max_amount'] = max_amount
            return params
        
        # 提取單一金額
        for pattern in self.amount_patterns:
            match = re.search(pattern, query)
            if match:
                amount_str = match.group(1).replace(',', '').replace('，', '')
                try:
                    amount = float(amount_str)
                    
                    # 判斷是上限還是下限
                    if any(word in query for word in ['以上', '超過', '大於', '>']):
                        params['min_amount'] = amount
                    elif any(word in query for word in ['以下', '小於', '少於', '<']):
                        params['max_amount'] = amount
                    else:
                        # 預設為範圍搜尋，上下浮動20%
                        params['min_amount'] = amount * 0.8
                        params['max_amount'] = amount * 1.2
                    break
                except ValueError:
                    continue
        
        return params
    
    def _extract_category_params(self, query: str) -> Dict[str, Any]:
        """提取類別相關參數"""
        params = {}
        
        # 嘗試匹配具體類別
        for pattern in self.category_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                params['category'] = match.group(1)
                break
        
        # 如果沒有找到具體類別，使用整個查詢作為類別
        if 'category' not in params:
            # 移除常見的搜尋詞彙
            category_query = query
            for word in ['找', '搜尋', '查詢', '尋找', '的', '相關', '招標', '採購']:
                category_query = category_query.replace(word, '')
            category_query = category_query.strip()
            if category_query:
                params['category'] = category_query
        
        return params
    
    def _extract_date_params(self, query: str) -> Dict[str, Any]:
        """提取日期相關參數"""
        params = {}
        
        # 完整日期匹配
        date_match = re.search(r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})[日號]?', query)
        if date_match:
            year, month, day = date_match.groups()
            params['start_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            params['end_date'] = params['start_date']
            return params
        
        # 年月匹配
        year_month_match = re.search(r'(\d{4})[年/\-](\d{1,2})[月/\-]', query)
        if year_month_match:
            year, month = year_month_match.groups()
            params['start_date'] = f"{year}-{month.zfill(2)}-01"
            # 計算月底日期
            import calendar
            last_day = calendar.monthrange(int(year), int(month))[1]
            params['end_date'] = f"{year}-{month.zfill(2)}-{last_day:02d}"
            return params
        
        # 相對時間處理
        if '最近' in query or '近期' in query:
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # 最近30天
            params['start_date'] = start_date.strftime('%Y-%m-%d')
            params['end_date'] = end_date.strftime('%Y-%m-%d')
        
        return params
    
    def _generate_reasoning(self, query: str, intent: QueryIntent, 
                          confidence: float, parameters: Dict[str, Any]) -> str:
        """生成分析推理"""
        reasoning = f"分析查詢「{query}」，"
        
        if confidence > 0.7:
            reasoning += f"高信心度({confidence:.2f})判斷為{intent.value}搜尋。"
        elif confidence > 0.4:
            reasoning += f"中等信心度({confidence:.2f})判斷為{intent.value}搜尋。"
        else:
            reasoning += f"低信心度({confidence:.2f})判斷為{intent.value}搜尋。"
        
        if parameters:
            reasoning += f" 提取到的參數：{parameters}"
        
        return reasoning
    
    def _generate_suggestions(self, query: str, intent: QueryIntent, 
                            parameters: Dict[str, Any]) -> List[str]:
        """生成建議"""
        suggestions = []
        
        if intent == QueryIntent.ORGANIZATION and 'organization_name' not in parameters:
            suggestions.append("請提供更具體的機關名稱，例如：台電、郵局、教育部")
        
        if intent == QueryIntent.AMOUNT and not any(k in parameters for k in ['min_amount', 'max_amount']):
            suggestions.append("請提供金額範圍，例如：100萬到500萬、預算超過200萬")
        
        if intent == QueryIntent.CATEGORY and 'category' not in parameters:
            suggestions.append("請提供採購類別，例如：電腦設備、建築工程、清潔服務")
        
        if intent == QueryIntent.DATE and not any(k in parameters for k in ['start_date', 'end_date']):
            suggestions.append("請提供日期範圍，例如：2024年1月、最近一個月、今年")
        
        if intent == QueryIntent.UNKNOWN:
            suggestions.extend([
                "請提供更具體的搜尋條件",
                "可以搜尋機關名稱、金額範圍、採購類別或日期",
                "例如：台電的電力設備招標、預算100萬以上的採購案"
            ])
        
        return suggestions

# 全域分析器實例
analyzer = QueryIntentAnalyzer()

def analyze_user_intent(query: str) -> IntentAnalysisResult:
    """
    分析使用者查詢意圖的便利函數
    
    Args:
        query: 使用者輸入的自然語言查詢
    
    Returns:
        IntentAnalysisResult: 分析結果
    """
    return analyzer.analyze_intent(query)
