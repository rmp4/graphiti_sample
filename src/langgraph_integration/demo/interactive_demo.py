"""
LangGraph + Graphiti 招標搜尋系統互動演示

提供命令列介面來測試智能招標搜尋功能
"""

import asyncio
import logging
from typing import Dict, Any, List
import sys
import os

# 添加父目錄到路徑以便導入
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from langgraph_integration.tools.tender_search_tools import (
        search_tender_by_organization,
        search_tender_by_amount,
        search_tender_by_category,
        search_tender_by_date_range,
        search_tender_comprehensive,
        get_tender_stats
    )
    TOOLS_AVAILABLE = True
    LANGCHAIN_AVAILABLE = True  # 假設工具可用時 LangChain 也可用
except ImportError as e:
    logger.error(f"無法導入搜尋工具: {e}")
    TOOLS_AVAILABLE = False
    LANGCHAIN_AVAILABLE = False
    # 設置未定義變數
    search_tender_by_organization = None
    search_tender_by_amount = None
    search_tender_by_category = None
    search_tender_by_date_range = None
    search_tender_comprehensive = None
    get_tender_stats = None

class TenderSearchDemo:
    """招標搜尋演示系統"""

    def __init__(self):
        self.session_count = 0
        self.search_history = []

    def display_banner(self):
        """顯示歡迎橫幅"""
        print("=" * 60)
        print(" LangGraph + Graphiti 招標搜尋系統演示")
        print("=" * 60)
        print("功能說明：")
        print("1. 根據機關名稱搜尋招標案")
        print("2. 根據金額範圍搜尋招標案")
        print("3. 根據採購類別搜尋招標案")
        print("4. 根據日期範圍搜尋招標案")
        print("5. 綜合關鍵字搜尋")
        print("6. 查看系統統計資訊")
        print("7. 查看搜尋歷史")
        print("0. 退出系統")
        print("-" * 60)
        
        # 顯示系統狀態
        if TOOLS_AVAILABLE:
            print(f" 搜尋工具狀態: 可用")
            print(f" LangChain 狀態: {'可用' if LANGCHAIN_AVAILABLE else '降級模式'}")
        else:
            print(" 搜尋工具狀態: 不可用")
        print("=" * 60)

    def record_search(self, search_type: str, query: str, result_preview: str):
        """記錄搜尋歷史"""
        self.search_history.append({
            "type": search_type,
            "query": query,
            "result_preview": result_preview[:100] + "..." if len(result_preview) > 100 else result_preview,
            "timestamp": asyncio.get_event_loop().time()
        })

    def search_by_organization(self):
        """根據機關搜尋"""
        if not TOOLS_AVAILABLE:
            print(" 搜尋工具不可用")
            return
            
        org_name = input("請輸入機關名稱 (例如: 臺北市政府): ").strip()
        if not org_name:
            print(" 機關名稱不能為空")
            return

        print(f" 搜尋機關「{org_name}」的招標案...")
        try:
            if search_tender_by_organization is None:
                result = " 搜尋工具不可用"
            else:
                result = search_tender_by_organization(org_name)
            print("\n 搜尋結果:")
            print(result)
            self.record_search("機關搜尋", org_name, result)
        except Exception as e:
            print(f" 搜尋失敗: {e}")

    def search_by_amount(self):
        """根據金額範圍搜尋"""
        if not TOOLS_AVAILABLE:
            print(" 搜尋工具不可用")
            return
            
        try:
            min_amount = float(input("請輸入最小金額 (萬元): ").strip())
            max_amount = float(input("請輸入最大金額 (萬元): ").strip())
            
            if min_amount >= max_amount:
                print(" 最小金額必須小於最大金額")
                return
                
        except ValueError:
            print(" 請輸入有效的數字")
            return

        print(f" 搜尋金額範圍 {min_amount}-{max_amount}萬 的招標案...")
        try:
            if search_tender_by_amount is None:
                result = " 搜尋工具不可用"
            else:
                result = search_tender_by_amount.invoke({
                    "min_amount": min_amount,
                    "max_amount": max_amount
                })
            print("\n 搜尋結果:")
            print(result)
            self.record_search("金額搜尋", f"{min_amount}-{max_amount}萬", result)
        except Exception as e:
            print(f" 搜尋失敗: {e}")

    def search_by_category(self):
        """根據類別搜尋"""
        if not TOOLS_AVAILABLE:
            print(" 搜尋工具不可用")
            return
            
        category = input("請輸入採購類別 (例如: 資訊設備、工程、服務): ").strip()
        if not category:
            print(" 採購類別不能為空")
            return

        print(f" 搜尋類別「{category}」的招標案...")
        try:
            if search_tender_by_category is None:
                result = " 搜尋工具不可用"
            else:
                result = search_tender_by_category(category)
            print("\n 搜尋結果:")
            print(result)
            self.record_search("類別搜尋", category, result)
        except Exception as e:
            print(f" 搜尋失敗: {e}")

    def search_by_date_range(self):
        """根據日期範圍搜尋"""
        if not TOOLS_AVAILABLE:
            print(" 搜尋工具不可用")
            return
            
        start_date = input("請輸入開始日期 (YYYY-MM-DD): ").strip()
        end_date = input("請輸入結束日期 (YYYY-MM-DD): ").strip()
        
        if not start_date or not end_date:
            print(" 日期不能為空")
            return

        print(f"🔍 搜尋日期範圍 {start_date} 到 {end_date} 的招標案...")
        try:
            if search_tender_by_date_range is None:
                result = " 搜尋工具不可用"
            else:
                result = search_tender_by_date_range.invoke({
                    "start_date": start_date,
                    "end_date": end_date
                })
            print("\n 搜尋結果:")
            print(result)
            self.record_search("日期搜尋", f"{start_date} 到 {end_date}", result)
        except Exception as e:
            print(f" 搜尋失敗: {e}")

    def search_comprehensive(self):
        """綜合搜尋"""
        if not TOOLS_AVAILABLE:
            print(" 搜尋工具不可用")
            return
            
        query = input("請輸入搜尋關鍵字: ").strip()
        if not query:
            print(" 搜尋關鍵字不能為空")
            return

        print(f"🔍 綜合搜尋「{query}」...")
        try:
            if search_tender_comprehensive is None:
                result = " 搜尋工具不可用"
            else:
                result = search_tender_comprehensive(query)
            print("\n 搜尋結果:")
            print(result)
            self.record_search("綜合搜尋", query, result)
        except Exception as e:
            print(f" 搜尋失敗: {e}")

    def show_system_stats(self):
        """顯示系統統計"""
        if not TOOLS_AVAILABLE:
            print(" 搜尋工具不可用")
            return
            
        print(" 正在獲取系統統計資訊...")
        try:
            if get_tender_stats is None:
                stats = " 搜尋工具不可用"
            else:
                stats = get_tender_stats.invoke({})
            print("\n 系統統計:")
            print(stats)
        except Exception as e:
            print(f" 獲取統計失敗: {e}")

    def show_search_history(self):
        """顯示搜尋歷史"""
        if not self.search_history:
            print(" 暫無搜尋歷史")
            return

        print(f"\n 搜尋歷史 (共 {len(self.search_history)} 次搜尋):")
        print("-" * 50)
        for i, search in enumerate(self.search_history[-10:], 1):  # 顯示最近 10 次
            print(f"{i}. [{search['type']}] {search['query']}")
            print(f"   結果預覽: {search['result_preview']}")
            print()

    def run_interactive_session(self):
        """運行互動會話"""
        self.session_count += 1
        
        if not TOOLS_AVAILABLE:
            print(" 搜尋工具不可用，無法啟動演示")
            return

        self.display_banner()

        while True:
            try:
                print("\n" + "=" * 30)
                choice = input("請選擇功能 (0-7): ").strip()

                if choice == "0":
                    print(" 感謝使用！再見！")
                    break
                elif choice == "1":
                    self.search_by_organization()
                elif choice == "2":
                    self.search_by_amount()
                elif choice == "3":
                    self.search_by_category()
                elif choice == "4":
                    self.search_by_date_range()
                elif choice == "5":
                    self.search_comprehensive()
                elif choice == "6":
                    self.show_system_stats()
                elif choice == "7":
                    self.show_search_history()
                else:
                    print(" 無效選項，請選擇 0-7")

            except KeyboardInterrupt:
                print("\n\n 收到中斷信號，退出系統...")
                break
            except Exception as e:
                print(f" 發生錯誤: {e}")

        print(f"\n 本次會話統計: 共執行 {len(self.search_history)} 次搜尋")

def main():
    """主函數"""
    print(" 正在初始化 LangGraph + Graphiti 招標搜尋演示系統...")
    
    demo = TenderSearchDemo()
    demo.run_interactive_session()

if __name__ == "__main__":
    main()
