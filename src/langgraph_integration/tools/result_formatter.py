"""
結果格式化工具
用於將 Graphiti 搜尋結果格式化為使用者友好的格式
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TenderResult:
    """招標結果數據類別"""
    tender_id: Optional[str] = None
    tender_name: Optional[str] = None
    agency: Optional[str] = None
    amount: Optional[str] = None
    description: Optional[str] = None
    announcement_date: Optional[str] = None
    deadline: Optional[str] = None
    category: Optional[str] = None
    contact_info: Optional[str] = None
    status: Optional[str] = None

class TenderResultFormatter:
    """招標結果格式化器"""
    
    def __init__(self):
        self.max_description_length = 200
        self.max_results_display = 10
    
    def format_search_results(self, results: List[Dict[str, Any]], 
                            search_type: str = "general") -> str:
        """格式化搜尋結果為可讀文字"""
        if not results:
            return "未找到符合條件的招標案"
        
        # 限制顯示結果數量
        display_results = results[:self.max_results_display]
        
        formatted_text = f"找到 {len(results)} 個招標案"
        if len(results) > self.max_results_display:
            formatted_text += f"（顯示前 {self.max_results_display} 個）"
        formatted_text += "：\n\n"
        
        for i, result in enumerate(display_results, 1):
            tender_result = self._parse_result_to_tender(result)
            formatted_text += self._format_single_tender(tender_result, i)
            formatted_text += "\n" + "-" * 60 + "\n\n"
        
        return formatted_text
    
    def format_detailed_result(self, result: Dict[str, Any]) -> str:
        """格式化單一招標案的詳細資訊"""
        tender_result = self._parse_result_to_tender(result)
        
        details = "📋 招標案詳細資訊\n"
        details += "=" * 40 + "\n\n"
        
        if tender_result.tender_name:
            details += f" 招標案名稱：{tender_result.tender_name}\n\n"
        
        if tender_result.agency:
            details += f" 招標機關：{tender_result.agency}\n\n"
        
        if tender_result.amount:
            details += f" 預算金額：{tender_result.amount}\n\n"
        
        if tender_result.category:
            details += f" 採購類別：{tender_result.category}\n\n"
        
        if tender_result.announcement_date:
            details += f" 公告日期：{tender_result.announcement_date}\n\n"
        
        if tender_result.deadline:
            details += f" 截止日期：{tender_result.deadline}\n\n"
        
        if tender_result.status:
            details += f" 狀態：{tender_result.status}\n\n"
        
        if tender_result.description:
            details += f" 描述：\n{tender_result.description}\n\n"
        
        if tender_result.contact_info:
            details += f" 聯絡資訊：\n{tender_result.contact_info}\n\n"
        
        return details
    
    def format_summary_statistics(self, results: List[Dict[str, Any]]) -> str:
        """格式化搜尋結果統計摘要"""
        if not results:
            return "無搜尋結果統計"
        
        # 統計各種資訊
        agencies = set()
        categories = set()
        total_amount = 0
        amount_count = 0
        
        for result in results:
            tender_result = self._parse_result_to_tender(result)
            
            if tender_result.agency:
                agencies.add(tender_result.agency)
            
            if tender_result.category:
                categories.add(tender_result.category)
            
            # 嘗試提取金額數字進行統計
            if tender_result.amount:
                amount_num = self._extract_amount_number(tender_result.amount)
                if amount_num:
                    total_amount += amount_num
                    amount_count += 1
        
        summary = "📊 搜尋結果統計摘要\n"
        summary += "=" * 30 + "\n\n"
        summary += f"📈 總招標案數：{len(results)}\n"
        summary += f"🏢 涉及機關數：{len(agencies)}\n"
        summary += f"📂 採購類別數：{len(categories)}\n"
        
        if amount_count > 0:
            avg_amount = total_amount / amount_count
            summary += f"💰 平均預算：{avg_amount:.1f}萬\n"
        
        if agencies:
            summary += f"\n🏢 主要機關：\n"
            for agency in list(agencies)[:5]:  # 顯示前5個機關
                summary += f"   • {agency}\n"
        
        if categories:
            summary += f"\n📂 主要類別：\n"
            for category in list(categories)[:5]:  # 顯示前5個類別
                summary += f"   • {category}\n"
        
        return summary
    
    def format_comparison_table(self, results: List[Dict[str, Any]]) -> str:
        """格式化為比較表格（簡化版）"""
        if not results:
            return "無結果可比較"
        
        # 限制比較結果數量
        compare_results = results[:5]
        
        table = "📋 招標案比較表\n"
        table += "=" * 50 + "\n\n"
        
        for i, result in enumerate(compare_results, 1):
            tender_result = self._parse_result_to_tender(result)
            table += f"{i}. {tender_result.tender_name or '未知招標案'}\n"
            table += f"   機關：{tender_result.agency or '未知'}\n"
            table += f"   金額：{tender_result.amount or '未知'}\n"
            table += f"   類別：{tender_result.category or '未知'}\n\n"
        
        return table
    
    def _parse_result_to_tender(self, result: Dict[str, Any]) -> TenderResult:
        """將原始結果解析為 TenderResult 物件"""
        return TenderResult(
            tender_id=result.get('tender_id'),
            tender_name=result.get('tender_name'),
            agency=result.get('agency'),
            amount=result.get('amount'),
            description=self._truncate_description(result.get('description')),
            announcement_date=result.get('announcement_date'),
            deadline=result.get('deadline'),
            category=result.get('category'),
            contact_info=result.get('contact_info'),
            status=result.get('status')
        )
    
    def _format_single_tender(self, tender: TenderResult, index: int) -> str:
        """格式化單一招標案資訊"""
        formatted = f"{index}. "
        
        # 招標案名稱
        if tender.tender_name:
            formatted += f"**{tender.tender_name}**\n"
        else:
            formatted += "**未知招標案**\n"
        
        # 機關資訊
        if tender.agency:
            formatted += f"   🏢 機關：{tender.agency}\n"
        
        # 金額資訊
        if tender.amount:
            formatted += f"   💰 金額：{tender.amount}\n"
        
        # 類別資訊
        if tender.category:
            formatted += f"   📂 類別：{tender.category}\n"
        
        # 日期資訊
        if tender.announcement_date:
            formatted += f"   📅 公告：{tender.announcement_date}\n"
        
        if tender.deadline:
            formatted += f"   ⏰ 截止：{tender.deadline}\n"
        
        # 描述資訊
        if tender.description:
            formatted += f"   📝 描述：{tender.description}\n"
        
        return formatted
    
    def _truncate_description(self, description: Optional[str]) -> Optional[str]:
        """截斷過長的描述"""
        if not description:
            return None
        
        if len(description) <= self.max_description_length:
            return description
        
        return description[:self.max_description_length] + "..."
    
    def _extract_amount_number(self, amount_str: str) -> Optional[float]:
        """從金額字串中提取數字（萬為單位）"""
        if not amount_str:
            return None
        
        import re
        # 尋找數字模式
        numbers = re.findall(r'[\d,]+\.?\d*', amount_str.replace(',', ''))
        
        if numbers:
            try:
                # 取第一個數字
                return float(numbers[0])
            except ValueError:
                pass
        
        return None

# 全域格式化器實例
formatter = TenderResultFormatter()

def format_tender_results(results: List[Any], 
                         format_type: str = "list",
                         search_type: str = "general") -> str:
    """
    格式化招標搜尋結果的便利函數
    
    Args:
        results: 搜尋結果列表
        format_type: 格式類型 ("list", "detailed", "summary", "comparison")
        search_type: 搜尋類型 ("organization", "amount", "category", "date", "general")
    
    Returns:
        格式化後的字串
    """
    try:
        if format_type == "detailed" and results:
            return formatter.format_detailed_result(results[0])
        elif format_type == "summary":
            return formatter.format_summary_statistics(results)
        elif format_type == "comparison":
            return formatter.format_comparison_table(results)
        else:
            return formatter.format_search_results(results, search_type)
    except Exception as e:
        logger.error(f"格式化結果時發生錯誤: {e}")
        return f"格式化結果時發生錯誤: {str(e)}"

def extract_key_info(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    從搜尋結果中提取關鍵資訊
    
    Returns:
        包含關鍵資訊的字典
    """
    if not results:
        return {"summary": "無搜尋結果"}
    
    key_info = {
        "total_count": len(results),
        "agencies": list(set(r.get('agency') for r in results if r.get('agency'))),
        "categories": list(set(r.get('category') for r in results if r.get('category'))),
        "amount_ranges": [],
        "recent_tenders": []
    }
    
    # 提取金額範圍
    for result in results:
        amount = result.get('amount')
        if amount:
            key_info["amount_ranges"].append(amount)
    
    # 提取最近的招標案（假設有日期資訊）
    for result in results[:3]:  # 取前3個作為最近的
        if result.get('tender_name'):
            key_info["recent_tenders"].append({
                "name": result.get('tender_name'),
                "agency": result.get('agency'),
                "amount": result.get('amount')
            })
    
    return key_info
