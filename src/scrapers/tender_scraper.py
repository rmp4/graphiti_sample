"""
政府採購網招標資料爬蟲

實作政府採購網頁面爬取功能，包含反爬蟲機制應對和重試邏輯
"""

import asyncio
import aiohttp
import logging
import random
import time

logger = logging.getLogger(__name__)

class TenderScraper:
    """政府採購網招標資料爬蟲"""

    def __init__(self, base_url: str = "https://web.pcc.gov.tw"):
        self.base_url = base_url
        self.session = None
        self.request_delay = (1, 3)  # 請求間隔秒數範圍
        self.max_retries = 3
        self.timeout = 30
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

    async def _fetch(self, url: str) -> str:
        """非同步取得網頁內容，包含重試與延遲"""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout))
        for attempt in range(1, self.max_retries + 1):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        logger.info(f"成功取得 {url}")
                        # 隨機延遲，模擬人類行為
                        await asyncio.sleep(random.uniform(*self.request_delay))
                        return text
                    else:
                        logger.warning(f"取得 {url} 時 HTTP 狀態碼 {response.status}")
            except Exception as e:
                logger.warning(f"嘗試第 {attempt} 次取得 {url} 發生錯誤: {e}")
            await asyncio.sleep(2 ** attempt)  # 指數退避
        raise Exception(f"無法取得 {url}，超過最大重試次數")

    async def fetch_tender_detail(self, tender_id: str) -> str:
        """取得指定招標案詳細頁面 HTML"""
        url = f"{self.base_url}/tps/QueryTender/query/searchTenderDetail?pkPmsMain={tender_id}"
        html = await self._fetch(url)
        return html

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
