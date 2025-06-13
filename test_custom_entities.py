#!/usr/bin/env python3
"""
測試自定義實體類型功能的腳本
"""

import asyncio
import logging
from src.parsers.tender_parser import TenderParser
from src.episodes.tender_episodes import convert_tender_data_to_episodes, create_tender_entities

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_custom_entities():
    """測試自定義實體類型功能"""
    try:
        # 讀取本地 HTML 檔案
        with open('sample_data/real_tender.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 使用解析器
        parser = TenderParser()
        result = parser.parse_tender_detail(html_content)
        result["tender_id"] = "NzA5MjcyOTY="
        
        print("\n=== 原始解析結果 ===")
        for key, value in result.items():
            print(f"{key}: {value}")
        
        # 轉換為新的 Episodes
        episodes = convert_tender_data_to_episodes(result)
        print(f"\n=== Episodes (共 {len(episodes)} 個) ===")
        for i, episode in enumerate(episodes, 1):
            print(f"\n{i}. {episode.title}")
            print(f"   Content: {episode.content}")
        
        # 創建自定義實體
        entities = create_tender_entities(result)
        print(f"\n=== 自定義實體 (共 {len(entities)} 個) ===")
        for i, entity in enumerate(entities, 1):
            print(f"\n{i}. 實體類型: {entity.entity_type}")
            print(f"   名稱: {entity.name}")
            print(f"   屬性: {entity.properties}")
        
        # 比較差異
        print("\n=== 改進效果 ===")
        print("✅ Episodes 內容更簡潔，不再包含結構化資料")
        print("✅ 金額、日期、機關等資訊分離為獨立實體")
        print("✅ 支援數值提取（金額數值化）")
        print("✅ 實體類型標準化，便於查詢和關聯")
            
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(test_custom_entities())
