#!/usr/bin/env python3
"""
測試修正後的自定義實體類型
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

import sys
sys.path.append("src")
from tender_processor import TenderProcessor

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_fixed_entities():
    """測試修正後的自定義實體類型"""
    
    # 檢查環境變數
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("請設定 OPENAI_API_KEY 環境變數")
        return
    
    # 設定 Graphiti 客戶端
    graphiti_client = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password",
    )
    
    processor = None
    try:
        # 建立索引和約束
        await graphiti_client.build_indices_and_constraints()
        
        # 建立並測試處理器
        processor = TenderProcessor(graphiti_client)
        
        print("\n=== 測試修正後的自定義實體類型 ===")
        
        # 處理一個招標案（強制更新）
        tender_id = "NzA5Mjc1MDU="
        print(f"處理招標案: {tender_id}")
        
        episodes = await processor.process_tender(tender_id, force_update=True)
        print(f"✅ 處理完成，創建了 {len(episodes)} 個 Episodes")
        
        # 等待一下讓 Graphiti 處理完成
        print("等待 Graphiti 處理...")
        await asyncio.sleep(10)
        
        # 這裡可以加入更多驗證邏輯
        
        print("\n✅ 測試完成！")
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        if processor:
            await processor.close()
        await graphiti_client.close()

if __name__ == "__main__":
    asyncio.run(test_fixed_entities())
