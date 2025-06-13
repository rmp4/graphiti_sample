"""
政府採購網招標資料解析器

負責解析爬取的招標頁面 HTML，提取結構化的招標資訊
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import logging

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
            # 輸出部分 HTML 內容以供調試
            logger.info(f"抓取的 HTML 內容前 500 字元:\n{soup.prettify()[:500]}")

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

            logger.info(f"成功解析招標資料: {data.get('tender_name', '未知招標案')}")
        except Exception as e:
            logger.error(f"解析招標資料時發生錯誤: {e}")

        return data
