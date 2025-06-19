"""
解析sample_data中的招標HTML檔案並寫入Graphiti

使用現有的entity和episode架構處理下載的政府採購案件HTML檔案
"""

import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from pathlib import Path

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from entities.tender_entities import TenderCaseEntity, OrganizationEntity, AmountEntity, DateEntity, ContractorEntity, TechnologyEntity
from parsers.tender_parser import TenderParser
from episodes.tender_episodes import convert_tender_data_to_episodes, create_tender_entities, Episode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleTenderProcessor:
    """處理sample_data中的招標HTML檔案"""
    
    def __init__(self, graphiti_client: Graphiti):
        self.graphiti_client = graphiti_client
        self.parser = TenderParser()
        self.processed_files = set()
        
        # 統計資訊
        self.stats = {
            "total_files": 0,
            "successful_files": 0,
            "total_episodes": 0,
            "total_entities": 0,
            "errors": []
        }
    
    async def process_html_file(self, file_path: str) -> List[Episode]:
        """處理單個HTML檔案"""
        try:
            logger.info(f"開始處理檔案: {file_path}")
            
            # 讀取HTML檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 從檔案名稱提取tender_id
            file_name = Path(file_path).stem
            tender_id = file_name.replace('tender_', '') if file_name.startswith('tender_') else file_name
            
            # 解析HTML為結構化資料
            tender_data = self.parser.parse_tender_detail(html_content)
            tender_data["tender_id"] = tender_id
            
            # 檢查是否有有效的招標案名稱
            if not tender_data.get("tender_name"):
                logger.warning(f"檔案 {file_path} 無法取得有效的招標案名稱，跳過處理")
                return []
            
            # 轉換為Episodes
            episodes = convert_tender_data_to_episodes(tender_data)
            logger.info(f"從檔案 {file_path} 轉換出 {len(episodes)} 個Episodes")
            
            # 創建自定義實體
            entities = create_tender_entities(tender_data)
            logger.info(f"從檔案 {file_path} 創建 {len(entities)} 個實體")
            
            # 定義自定義實體類型字典
            entity_types = {
                "TenderCase": TenderCaseEntity,
                "Organization": OrganizationEntity,
                "Amount": AmountEntity,
                "Date": DateEntity,
                "Contractor": ContractorEntity,
                "Technology": TechnologyEntity,
            }
            
            # 寫入Episodes到Graphiti
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
                    logger.info(f"已寫入Episode: {episode.title}")
                    successful_episodes += 1
                except Exception as e:
                    logger.error(f"寫入Episode '{episode.title}' 時發生錯誤: {e}")
                    self.stats["errors"].append(f"寫入Episode失敗: {e}")
            
            # 寫入實體摘要
            if entities:
                try:
                    entity_summary = f"招標案「{tender_data.get('tender_name', '未知')}」相關實體：\n"
                    for entity in entities:
                        entity_summary += f"- {entity.entity_type}: {entity.name}\n"
                        # 加入重要屬性
                        if entity.entity_type == "Amount" and entity.properties.get("amount_value"):
                            entity_summary += f"  金額: {entity.properties['amount_value']}\n"
                        elif entity.entity_type == "Date" and entity.properties.get("date_value"):
                            entity_summary += f"  日期: {entity.properties['date_value']}\n"
                    
                    await self.graphiti_client.add_episode(
                        name=f"實體摘要_{tender_data.get('tender_name', '未知')}",
                        episode_body=entity_summary,
                        source=EpisodeType.text,
                        source_description=f"政府採購網_實體摘要_{tender_id}",
                        reference_time=datetime.now(timezone.utc),
                        entity_types=entity_types
                    )
                    logger.info("已寫入實體摘要Episode")
                    successful_episodes += 1
                except Exception as e:
                    logger.error(f"寫入實體摘要時發生錯誤: {e}")
                    self.stats["errors"].append(f"寫入實體摘要失敗: {e}")
            
            # 更新統計
            self.stats["total_episodes"] += successful_episodes
            self.stats["total_entities"] += len(entities)
            
            logger.info(f"完成處理檔案: {file_path} (成功寫入 {successful_episodes} 個項目)")
            return episodes
            
        except Exception as e:
            logger.error(f"處理檔案 {file_path} 時發生錯誤: {e}")
            self.stats["errors"].append(f"處理檔案 {file_path} 失敗: {e}")
            return []
    
    async def process_all_tender_files(self, directory: str = "sample_data/tender"):
        """處理指定目錄中的所有招標HTML檔案"""
        try:
            tender_dir = Path(directory)
            if not tender_dir.exists():
                logger.error(f"目錄不存在: {directory}")
                return
            
            # 尋找所有HTML檔案
            html_files = list(tender_dir.glob("*.html"))
            self.stats["total_files"] = len(html_files)
            
            if not html_files:
                logger.warning(f"在目錄 {directory} 中沒有找到HTML檔案")
                return
            
            logger.info(f"找到 {len(html_files)} 個HTML檔案待處理")
            
            # 逐一處理每個檔案
            for html_file in html_files:
                try:
                    await self.process_html_file(str(html_file))
                    self.stats["successful_files"] += 1
                except Exception as e:
                    logger.error(f"處理檔案 {html_file} 時發生錯誤: {e}")
                    self.stats["errors"].append(f"處理檔案 {html_file} 失敗: {e}")
            
            # 顯示最終統計
            self.print_stats()
            
        except Exception as e:
            logger.error(f"處理目錄 {directory} 時發生錯誤: {e}")
    
    def print_stats(self):
        """列印處理統計資訊"""
        logger.info("=" * 60)
        logger.info("處理完成統計:")
        logger.info(f"總檔案數: {self.stats['total_files']}")
        logger.info(f"成功處理: {self.stats['successful_files']}")
        logger.info(f"失敗檔案: {self.stats['total_files'] - self.stats['successful_files']}")
        logger.info(f"總Episodes: {self.stats['total_episodes']}")
        logger.info(f"總實體數: {self.stats['total_entities']}")
        
        if self.stats["errors"]:
            logger.info(f"錯誤數量: {len(self.stats['errors'])}")
            for error in self.stats["errors"][:5]:  # 只顯示前5個錯誤
                logger.info(f"  - {error}")
            if len(self.stats["errors"]) > 5:
                logger.info(f"  ... 還有 {len(self.stats['errors']) - 5} 個錯誤")
        
        success_rate = (self.stats["successful_files"] / max(1, self.stats["total_files"])) * 100
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info("=" * 60)

async def main():
    """主程式"""
    # 讀取環境變數
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        logger.error("請設定 OPENAI_API_KEY 環境變數")
        return

    logger.info("連接 Graphiti 知識圖譜...")
    client = Graphiti(
        neo4j_uri,
        neo4j_user,
        neo4j_password,
    )
    
    try:
        # 建立必要的索引和約束
        logger.info("建立 Graphiti 索引和約束...")
        await client.build_indices_and_constraints()
        
        # 創建處理器
        processor = SampleTenderProcessor(client)
        
        # 處理所有招標HTML檔案
        await processor.process_all_tender_files()
        
        # 簡單搜尋示範
        logger.info("=" * 60)
        logger.info("搜尋示範:")
        
        search_queries = ["招標", "預算", "機關", "開標"]
        
        for query in search_queries:
            logger.info(f"\n搜尋關鍵字: {query}")
            try:
                results = await client.search(query, num_results=3)
                if results:
                    for i, edge in enumerate(results, 1):
                        logger.info(f"  {i}. {edge.fact}")
                else:
                    logger.info("  沒有找到相關結果")
            except Exception as e:
                logger.error(f"搜尋 '{query}' 時發生錯誤: {e}")
        
        logger.info("\n招標資料已成功處理並導入 Graphiti 知識圖譜！")
        logger.info("您可以透過 Neo4j Browser (http://localhost:7474) 查看圖形結構")
        
    except Exception as e:
        logger.error(f"主程序執行時發生錯誤: {e}")
    finally:
        # 正確關閉 Graphiti 客戶端
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
