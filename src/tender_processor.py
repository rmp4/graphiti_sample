"""
政府採購資料處理主程式

整合爬蟲、解析器和Episode轉換，完成從招標ID到知識圖譜的完整流程
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from openai import AsyncAzureOpenAI
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from entities.tender_entities import TenderCaseEntity, OrganizationEntity, AmountEntity, DateEntity, ContractorEntity
from scrapers.tender_scraper import TenderScraper
from parsers.tender_parser import TenderParser
from episodes.tender_episodes import convert_tender_data_to_episodes, create_tender_entities, Episode

logger = logging.getLogger(__name__)

class TenderProcessor:
    """政府採購資料處理器"""
    
    def __init__(self, graphiti_client: Graphiti):
        self.graphiti_client = graphiti_client
        self.scraper = TenderScraper()
        self.parser = TenderParser()
        self.processed_tenders = set()  # 追蹤已處理的招標案
    
    async def process_tender(self, tender_id: str, force_update: bool = False) -> List[Episode]:
        """
        處理單一招標案，從ID到知識圖譜的完整流程
        
        Args:
            tender_id (str): 招標案ID
            force_update (bool): 是否強制更新，忽略去重檢查
            
        Returns:
            List[Episode]: 處理後的Episodes
        """
        try:
            # 檢查是否已處理過（除非強制更新）
            if not force_update and tender_id in self.processed_tenders:
                logger.info(f"招標案 {tender_id} 已處理過，跳過")
                return []
            
            logger.info(f"開始處理招標案: {tender_id}")
            
            # 1. 爬取HTML
            html = await self.scraper.fetch_tender_detail(tender_id)
            
            # 2. 解析結構化資料
            tender_data = self.parser.parse_tender_detail(html)
            tender_data["tender_id"] = tender_id
            
            # 檢查是否有有效的招標案名稱（避免處理失敗的案件）
            if not tender_data.get("tender_name"):
                logger.warning(f"招標案 {tender_id} 無法取得有效資料，跳過處理")
                return []
            
            # 3. 轉換為Episodes
            episodes = convert_tender_data_to_episodes(tender_data)
            
            # 4. 創建自定義實體
            entities = create_tender_entities(tender_data)
            logger.info(f"創建了 {len(entities)} 個自定義實體")
            
            # 5. 直接傳遞自定義實體類型字典
            entity_types = {
                "TenderCase": TenderCaseEntity,
                "Organization": OrganizationEntity,
                "Amount": AmountEntity,
                "Date": DateEntity,
                "Contractor": ContractorEntity,
            }
            logger.info(f"使用自定義實體類型字典，包含 {len(entity_types)} 種實體")
            
            # 6. 儲存Episodes到Graphiti（使用自定義實體類型）
            for episode in episodes:
                await self.graphiti_client.add_episode(
                    name=episode.title,
                    episode_body=episode.content,
                    source=EpisodeType.text,
                    source_description=f"政府採購網_招標案_{tender_id}",
                    reference_time=datetime.now(timezone.utc),
                    entity_types=entity_types
                )
                logger.info(f"已加入Episode: {episode.title}")
            
            # 6. 記錄實體資訊（目前以 Episode 形式儲存實體關聯）
            if entities:
                entity_summary = "自定義實體類型：\n"
                for entity in entities:
                    entity_summary += f"- {entity.entity_type}: {entity.name}\n"
                
                await self.graphiti_client.add_episode(
                    name=f"實體摘要_{tender_data.get('tender_name', '未知')}",
                    episode_body=entity_summary,
                    source=EpisodeType.text,
                    source_description=f"政府採購網_實體摘要_{tender_id}",
                    reference_time=datetime.now(timezone.utc)
                )
                logger.info("已加入實體摘要Episode")
            
            # 記錄已處理的招標案
            self.processed_tenders.add(tender_id)
            
            logger.info(f"完成處理招標案: {tender_id}")
            return episodes
            
        except Exception as e:
            logger.error(f"處理招標案 {tender_id} 時發生錯誤: {e}")
            raise
    
    async def close(self):
        """關閉資源"""
        await self.scraper.close()
