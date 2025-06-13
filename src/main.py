import asyncio
import os
import hashlib
from datetime import datetime, timezone
from bs4 import BeautifulSoup, Tag
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Episode(BaseModel):
    title: str
    content: str
    
    def get_content_hash(self) -> str:
        """生成內容的雜湊值用於唯一識別"""
        content_for_hash = f"{self.title}:{self.content}"
        return hashlib.md5(content_for_hash.encode('utf-8')).hexdigest()[:8]
    
    def get_unique_name(self) -> str:
        """生成唯一的名稱"""
        return f"{self.title}_{self.get_content_hash()}"

async def parse_html_file(filepath: str) -> List[Episode]:
    logger.info(f"讀取 HTML 檔案: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    episodes = []

    # 取得標題與段落
    for header in soup.find_all(['h1', 'h2', 'h3']):
        title = header.get_text(strip=True)
        # 取得 header 之後的段落直到下一個 header
        content_parts = []
        for sibling in header.find_next_siblings():
            # 只處理 Tag 對象，跳過文字節點等
            if isinstance(sibling, Tag):
                if sibling.name.startswith('h'):
                    break
                if sibling.name == 'p':
                    content_parts.append(sibling.get_text(strip=True))
        content = "\n".join(content_parts)
        if content.strip():  # 只添加有內容的 episodes
            episodes.append(Episode(title=title, content=content))
    logger.info(f"解析出 {len(episodes)} 個 Episodes")
    return episodes

async def check_episode_exists_by_name(client: Graphiti, episode_name: str) -> bool:
    """直接查詢 Neo4j 檢查是否已存在相同 name 的節點"""
    try:
        # 使用 Neo4j driver 直接查詢
        driver = client.driver
        
        async with driver.session() as session:
            result = await session.run(
                "MATCH (n:Episodic {name: $name}) RETURN count(n) as count",
                name=episode_name
            )
            record = await result.single()
            count = record["count"] if record else 0
            
            return count > 0
            
    except Exception as e:
        logger.warning(f"檢查節點是否存在時發生錯誤: {e}")
        return False

async def add_episode_if_not_exists(client: Graphiti, episode: Episode, source_file: str, stats: Dict[str, int]) -> None:
    """只有當節點不存在時才添加 episode"""
    try:
        unique_name = episode.get_unique_name()
        source_description = f"{source_file}#{episode.title}"
        
        # 檢查是否已存在相同 name 的節點
        if await check_episode_exists_by_name(client, unique_name):
            logger.info(f"節點已存在，跳過: {episode.title}")
            stats["skipped"] += 1
            return
        
        # 只有當節點不存在時才添加
        logger.info(f"新增 Episode: {episode.title}")
        await client.add_episode(
            name=unique_name,
            episode_body=episode.content,
            source=EpisodeType.text,
            source_description=source_description,
            reference_time=datetime.now(timezone.utc)
        )
        
        stats["new_added"] += 1
        stats["total_processed"] += 1
        
    except Exception as e:
        logger.error(f"處理 Episode '{episode.title}' 時發生錯誤: {e}")
        stats["skipped"] += 1

async def process_episodes_batch(client: Graphiti, episodes: List[Episode], source_file: str) -> Dict[str, int]:
    """批次處理 episodes，包含本地去重"""
    stats = {
        "total_processed": 0,
        "new_added": 0,
        "updated": 0,
        "skipped": 0
    }
    
    # 本地去重：移除同一批次中的重複標題
    unique_episodes = []
    seen_titles = set()
    
    for episode in episodes:
        if episode.title not in seen_titles:
            unique_episodes.append(episode)
            seen_titles.add(episode.title)
        else:
            logger.info(f"跳過本地重複標題: {episode.title}")
            stats["skipped"] += 1
    
    logger.info(f"本地去重後剩餘 {len(unique_episodes)} 個 Episodes")
    
    # 逐一處理每個 episode
    for episode in unique_episodes:
        await add_episode_if_not_exists(client, episode, source_file, stats)
    
    return stats

async def main():
    # 讀取環境變數
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    update_mode = os.getenv("UPDATE_MODE", "incremental")  # "clean" 或 "incremental"

    if not openai_api_key:
        logger.error("請設定 OPENAI_API_KEY 環境變數")
        return

    logger.info(f"連接 Graphiti (模式: {update_mode})")
    client = Graphiti(
        neo4j_uri,
        neo4j_user,
        neo4j_password,
    )
    
    try:
        # 建立必要的索引和約束
        logger.info("建立 Graphiti 索引和約束")
        await client.build_indices_and_constraints()

        # 解析 sample.html
        source_file = "sample_data/sample.html"
        episodes = await parse_html_file(source_file)

        if not episodes:
            logger.warning("沒有找到任何 Episodes")
            return

        # 處理模式
        if update_mode == "clean":
            logger.info("清除模式：注意 - 此模式將清除現有相關資料")
            # 注意：Graphiti 沒有直接的清除方法，這裡只是提醒
            logger.warning("請手動清除 Neo4j 資料庫或使用 Neo4j Browser 清除相關節點")

        # 批次處理 episodes
        logger.info("開始批次處理 Episodes...")
        stats = await process_episodes_batch(client, episodes, source_file)

        # 報告處理結果
        logger.info("=" * 50)
        logger.info("處理完成統計:")
        logger.info(f"總計處理: {stats['total_processed']}")
        logger.info(f"新增: {stats['new_added']}")
        logger.info(f"跳過: {stats['skipped']}")
        logger.info("=" * 50)

        # 簡單搜尋示範
        search_query = "Neo4j"
        logger.info(f"搜尋知識圖譜: {search_query}")
        results = await client.search(search_query, num_results=5)

        logger.info("搜尋結果:")
        for i, edge in enumerate(results, 1):
            logger.info(f"{i}. {edge.fact}")
            if hasattr(edge, 'valid_at') and edge.valid_at:
                logger.info(f"   有效時間: {edge.valid_at.isoformat()}")

        # 顯示完成訊息
        logger.info("HTML 內容已成功處理並導入 Graphiti 知識圖譜！")
        logger.info("您可以透過 Neo4j Browser (http://localhost:7474) 查看圖形結構")
        
    except Exception as e:
        logger.error(f"主程序執行時發生錯誤: {e}")
    finally:
        # 正確關閉 Graphiti 客戶端
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
