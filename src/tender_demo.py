"""
政府採購資料處理示範程式

示範如何使用TenderProcessor處理政府採購網的招標資料
"""

import asyncio
import os
import logging
from graphiti_core import Graphiti
from tender_processor import TenderProcessor

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # 讀取環境變數
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        logger.error("請設定 OPENAI_API_KEY 環境變數")
        return

    # 初始化Graphiti客戶端
    logger.info("連接 Graphiti")
    client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        # 建立索引和約束
        await client.build_indices_and_constraints()
        
        # 初始化招標處理器
        processor = TenderProcessor(client)
        
        # 示範：處理範例招標案
        # 使用您提供的招標案ID（從URL中提取的NzA5Mjc1MDU=）
        tender_id = "NzA5MjgzMjA="
        
        logger.info(f"開始處理示範招標案: {tender_id}")
        episodes = await processor.process_tender(tender_id)
        
        logger.info(f"成功處理 {len(episodes)} 個Episodes")
        
        # 搜尋示範
        search_query = "北區營運處"
        logger.info(f"搜尋知識圖譜: {search_query}")
        results = await client.search(search_query, num_results=5)
        
        logger.info("搜尋結果:")
        for i, edge in enumerate(results, 1):
            logger.info(f"{i}. {edge.fact}")
        
        # 關閉資源
        await processor.close()
        
    except Exception as e:
        logger.error(f"執行時發生錯誤: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
