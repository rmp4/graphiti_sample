"""
政府採購網招標資料解析器

負責解析爬取的招標頁面 HTML，提取結構化的招標資訊
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import logging
from src.exceptions import ParsingError, TenderDataError

logger = logging.getLogger(__name__)

class TenderParser:
    """招標資料解析器"""

    @staticmethod
    def parse_tender_detail(html: str) -> Dict[str, Any]:
        """
        解析招標詳細頁面 HTML，提取結構化資料

        Args:
            html (str): 招標詳細頁面 HTML 內容

        Returns:
            Dict[str, Any]: 結構化招標資料字典
        """
        soup = BeautifulSoup(html, "html.parser")
        data = {}

        try:
            # 驗證輸入
            if not html or not html.strip():
                raise TenderDataError("提供的 HTML 內容為空")
            
            # 檢查 HTML 是否有效
            if not soup or not soup.get_text(strip=True):
                raise ParsingError("無法解析 HTML 內容或內容為空")

            # 安全地記錄部分 HTML 內容（避免記錄敏感資料）
            logger.debug(f"開始解析 HTML 內容，長度: {len(html)} 字元")

            # 嘗試用更通用的方式抓取招標案名稱
            title_tag = soup.find("td", id="tenderNameText")
            if not title_tag:
                # 嘗試用其他標籤或 class 名稱
                title_tag = soup.find("h1")
            data["tender_name"] = title_tag.get_text(strip=True) if title_tag else None

            # 嘗試抓取招標機關
            agency_tag = soup.find("td", string="機關名稱")
            if agency_tag:
                agency_value_tag = agency_tag.find_next_sibling("td")
                data["agency"] = agency_value_tag.get_text(strip=True) if agency_value_tag else None
            else:
                data["agency"] = None

            # 嘗試抓取預算金額
            budget_tag = soup.find("td", string="預算金額")
            if budget_tag:
                budget_value_tag = budget_tag.find_next_sibling("td")
                data["budget"] = budget_value_tag.get_text(strip=True) if budget_value_tag else None
            else:
                data["budget"] = None

            # 嘗試抓取決標金額
            award_tag = soup.find("td", string="決標金額")
            if award_tag:
                award_value_tag = award_tag.find_next_sibling("td")
                data["award_amount"] = award_value_tag.get_text(strip=True) if award_value_tag else None
            else:
                data["award_amount"] = None

            # 嘗試抓取開標日期或開標時間
            open_date_tag = soup.find("td", string="開標日期")
            if not open_date_tag:
                open_date_tag = soup.find("td", string="開標時間")
            if open_date_tag:
                open_date_value_tag = open_date_tag.find_next_sibling("td")
                data["open_date"] = open_date_value_tag.get_text(strip=True) if open_date_value_tag else None
            else:
                data["open_date"] = None

            # 驗證至少解析到一些關鍵資料
            if not any([data.get("tender_name"), data.get("agency"), data.get("budget")]):
                logger.warning("未解析到任何關鍵招標資訊，可能是 HTML 結構已變更")
            
            logger.info(f"成功解析招標資料: {data.get('tender_name', '未知招標案')}")
            
        except (TenderDataError, ParsingError):
            # 重新拋出已知的自訂異常
            raise
        except Exception as e:
            logger.error(f"解析招標資料時發生未預期錯誤: {type(e).__name__}: {e}")
            raise ParsingError(f"HTML 解析失敗: {e}") from e

        return data
