"""
政府採購資料處理主程式

整合爬蟲、解析器和Episode轉換，完成從招標ID到知識圖譜的完整流程
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json

from openai import AsyncAzureOpenAI
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from entities.tender_entities import TenderCaseEntity, OrganizationEntity, AmountEntity, DateEntity, ContractorEntity, TechnologyEntity
from scrapers.tender_scraper import TenderScraper
from parsers.tender_parser import TenderParser
from episodes.tender_episodes import convert_tender_data_to_episodes, create_tender_entities, Episode
from config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class ContentFilter:
    """內容過濾器，用於控制寫入 Neo4j 的內容"""

    def __init__(self):
        # 敏感詞彙黑名單
        self.blacklist_keywords = [
            "密碼", "password", "secret", "token", "key",
            "個人資料", "身分證", "電話", "地址"
        ]

        # 允許的機關白名單（可選）
        self.allowed_agencies = set()

        # 最小內容長度
        self.min_content_length = 10

        # 最大內容長度
        self.max_content_length = 10000

    def is_content_safe(self, content: str) -> tuple[bool, str]:
        """檢查內容是否安全可寫入"""
        if not content or len(content.strip()) < self.min_content_length:
            return False, "內容太短或為空"

        if len(content) > self.max_content_length:
            return False, f"內容超過最大長度限制 ({self.max_content_length})"

        # 檢查黑名單關鍵詞
        content_lower = content.lower()
        for keyword in self.blacklist_keywords:
            if keyword in content_lower:
                return False, f"包含敏感詞彙: {keyword}"

        return True, "內容安全"

    def is_agency_allowed(self, agency: str) -> bool:
        """檢查機關是否在允許清單中"""
        if not self.allowed_agencies:  # 如果沒有設定白名單，則允許所有
            return True
        return agency in self.allowed_agencies

    def add_allowed_agency(self, agency: str):
        """新增允許的機關"""
        self.allowed_agencies.add(agency)

    def clean_content(self, content: str) -> str:
        """清理內容，移除不必要的字符"""
        # 移除多餘的空白
        content = ' '.join(content.split())

        # 移除特殊字符（保留中文、英文、數字、基本標點）
        import re
        content = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：「」『』（）【】\-\.\,]', '', content)

        return content.strip()

class WritePreview:
    """寫入預覽器，讓使用者確認要寫入的內容"""

    def __init__(self, enable_preview: bool = True):
        self.enable_preview = enable_preview

    def preview_episodes(self, episodes: List[Episode], entities: List[Any]) -> Dict[str, Any]:
        """預覽將要寫入的 Episodes 和實體"""
        preview_data = {
            "episodes_count": len(episodes),
            "entities_count": len(entities),
            "episodes": [],
            "entities": []
        }

        for episode in episodes:
            preview_data["episodes"].append({
                "title": episode.title,
                "content_preview": episode.content[:200] + "..." if len(episode.content) > 200 else episode.content,
                "content_length": len(episode.content)
            })

        for entity in entities:
            preview_data["entities"].append({
                "type": entity.entity_type,
                "name": entity.name,
                "properties": entity.properties
            })

        return preview_data

    def should_proceed(self, preview_data: Dict[str, Any]) -> bool:
        """詢問使用者是否繼續寫入（在實際應用中可以改為自動判斷）"""
        if not self.enable_preview:
            return True

        logger.info("=== 寫入預覽 ===")
        logger.info(f"將寫入 {preview_data['episodes_count']} 個 Episodes")
        logger.info(f"將寫入 {preview_data['entities_count']} 個實體")

        for i, episode in enumerate(preview_data["episodes"], 1):
            logger.info(f"Episode {i}: {episode['title']} (長度: {episode['content_length']})")
            logger.info(f"  內容預覽: {episode['content_preview']}")

        for i, entity in enumerate(preview_data["entities"], 1):
            logger.info(f"實體 {i}: {entity['type']} - {entity['name']}")

        # 在實際應用中，這裡可以改為基於規則的自動判斷
        # 目前為了示範，直接返回 True
        return True

class TenderProcessor:
    """政府採購資料處理器"""

    def __init__(self, graphiti_client: Graphiti, enable_content_filter: bool = True, enable_preview: bool = True):
        self.graphiti_client = graphiti_client
        self.scraper = TenderScraper()
        self.parser = TenderParser()
        self.processed_tenders = set()  # 追蹤已處理的招標案

        # 新增控制機制
        self.content_filter = ContentFilter() if enable_content_filter else None
        self.write_preview = WritePreview(enable_preview)

        # 統計資訊
        self.stats = {
            "total_processed": 0,
            "successful_writes": 0,
            "filtered_content": 0,
            "preview_rejected": 0
        }
    
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
            self.stats["total_processed"] += 1

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

            # 3. 內容過濾檢查
            if self.content_filter:
                agency = tender_data.get("agency", "")
                if agency and not self.content_filter.is_agency_allowed(agency):
                    logger.warning(f"機關 '{agency}' 不在允許清單中，跳過處理")
                    self.stats["filtered_content"] += 1
                    return []

            # 4. 轉換為Episodes
            episodes = convert_tender_data_to_episodes(tender_data)

            # 5. 內容安全檢查和清理
            if self.content_filter:
                filtered_episodes = []
                for episode in episodes:
                    is_safe, reason = self.content_filter.is_content_safe(episode.content)
                    if not is_safe:
                        logger.warning(f"Episode '{episode.title}' 內容不安全: {reason}")
                        self.stats["filtered_content"] += 1
                        continue

                    # 清理內容
                    cleaned_content = self.content_filter.clean_content(episode.content)
                    episode.content = cleaned_content
                    filtered_episodes.append(episode)

                episodes = filtered_episodes
                logger.info(f"內容過濾後剩餘 {len(episodes)} 個 Episodes")

            # 6. 創建自定義實體
            entities = create_tender_entities(tender_data)
            logger.info(f"創建了 {len(entities)} 個自定義實體")
            
            # 7. 預覽將要寫入的內容
            preview_data = self.write_preview.preview_episodes(episodes, entities)

            # 8. 確認是否繼續寫入
            if not self.write_preview.should_proceed(preview_data):
                logger.info(f"使用者選擇不寫入招標案 {tender_id}")
                self.stats["preview_rejected"] += 1
                return []

            # 9. 如果沒有有效的 Episodes，跳過寫入
            if not episodes:
                logger.warning(f"招標案 {tender_id} 沒有有效的 Episodes，跳過寫入")
                return []

            # 10. 直接傳遞自定義實體類型字典
            entity_types = {
                "TenderCase": TenderCaseEntity,
                "Organization": OrganizationEntity,
                "Amount": AmountEntity,
                "Date": DateEntity,
                "Contractor": ContractorEntity,
                "Technology": TechnologyEntity,
            }
            logger.info(f"使用自定義實體類型字典，包含 {len(entity_types)} 種實體")

            # 11. 儲存Episodes到Graphiti（使用自定義實體類型）
            successful_episodes = 0
            for episode in episodes:
                try:
                    await self.graphiti_client.add_episode(
                        name=episode.title,
                        episode_body=episode.content,
                        source=EpisodeType.text,
                        source_description=f"政府採購網_招標案_{tender_id}",
                        reference_time=datetime.now(timezone.utc),
                        entity_types=entity_types
                    )
                    logger.info(f"已加入Episode: {episode.title}")
                    successful_episodes += 1
                except Exception as e:
                    logger.error(f"寫入Episode '{episode.title}' 時發生錯誤: {e}")

            # 12. 記錄實體資訊（目前以 Episode 形式儲存實體關聯）
            if entities:
                try:
                    entity_summary = "自定義實體類型：\n"
                    for entity in entities:
                        entity_summary += f"- {entity.entity_type}: {entity.name}\n"

                    # 檢查實體摘要內容安全性
                    is_safe = True  # 預設為安全
                    if self.content_filter:
                        is_safe, reason = self.content_filter.is_content_safe(entity_summary)
                        if not is_safe:
                            logger.warning(f"實體摘要內容不安全: {reason}")
                        else:
                            entity_summary = self.content_filter.clean_content(entity_summary)

                    if is_safe:
                        await self.graphiti_client.add_episode(
                            name=f"實體摘要_{tender_data.get('tender_name', '未知')}",
                            episode_body=entity_summary,
                            source=EpisodeType.text,
                            source_description=f"政府採購網_實體摘要_{tender_id}",
                            reference_time=datetime.now(timezone.utc)
                        )
                        logger.info("已加入實體摘要Episode")
                        successful_episodes += 1
                except Exception as e:
                    logger.error(f"寫入實體摘要時發生錯誤: {e}")

            # 更新統計
            if successful_episodes > 0:
                self.stats["successful_writes"] += 1
            
            # 記錄已處理的招標案
            self.processed_tenders.add(tender_id)

            logger.info(f"完成處理招標案: {tender_id} (成功寫入 {successful_episodes} 個項目)")
            return episodes

        except Exception as e:
            logger.error(f"處理招標案 {tender_id} 時發生錯誤: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """取得處理統計資訊"""
        return {
            **self.stats,
            "processed_tenders_count": len(self.processed_tenders),
            "success_rate": (self.stats["successful_writes"] / max(1, self.stats["total_processed"])) * 100
        }

    def print_stats(self):
        """列印處理統計資訊"""
        stats = self.get_stats()
        logger.info("=== 處理統計 ===")
        logger.info(f"總計處理: {stats['total_processed']} 個招標案")
        logger.info(f"成功寫入: {stats['successful_writes']} 個招標案")
        logger.info(f"內容過濾: {stats['filtered_content']} 個項目")
        logger.info(f"預覽拒絕: {stats['preview_rejected']} 個招標案")
        logger.info(f"成功率: {stats['success_rate']:.1f}%")
        logger.info(f"已處理招標案數量: {stats['processed_tenders_count']}")

    def configure_content_filter(self,
                                blacklist_keywords: Optional[List[str]] = None,
                                allowed_agencies: Optional[List[str]] = None,
                                min_content_length: Optional[int] = None,
                                max_content_length: Optional[int] = None):
        """配置內容過濾器"""
        if not self.content_filter:
            logger.warning("內容過濾器未啟用")
            return

        if blacklist_keywords:
            self.content_filter.blacklist_keywords.extend(blacklist_keywords)
            logger.info(f"新增 {len(blacklist_keywords)} 個黑名單關鍵詞")

        if allowed_agencies:
            for agency in allowed_agencies:
                self.content_filter.add_allowed_agency(agency)
            logger.info(f"新增 {len(allowed_agencies)} 個允許的機關")

        if min_content_length is not None:
            self.content_filter.min_content_length = min_content_length
            logger.info(f"設定最小內容長度: {min_content_length}")

        if max_content_length is not None:
            self.content_filter.max_content_length = max_content_length
            logger.info(f"設定最大內容長度: {max_content_length}")

    async def close(self):
        """關閉資源"""
        await self.scraper.close()
        self.print_stats()

    @classmethod
    def from_config(cls, graphiti_client: Graphiti, config_loader: Optional[ConfigLoader] = None):
        """從配置文件創建 TenderProcessor"""
        if config_loader is None:
            config_loader = ConfigLoader()

        # 創建處理器
        processor = cls(
            graphiti_client,
            enable_content_filter=config_loader.is_content_filter_enabled(),
            enable_preview=config_loader.is_preview_enabled()
        )

        # 配置內容過濾器
        if processor.content_filter:
            limits = config_loader.get_content_limits()
            processor.configure_content_filter(
                blacklist_keywords=config_loader.get_blacklist_keywords(),
                allowed_agencies=config_loader.get_allowed_agencies(),
                min_content_length=limits.get("min_length"),
                max_content_length=limits.get("max_length")
            )

        logger.info("已從配置文件創建 TenderProcessor")
        config_loader.print_config()

        return processor
