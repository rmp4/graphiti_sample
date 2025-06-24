"""
政府採購資料 Episode 轉換模組

將解析後的招標資料轉換為 Graphiti Episodes，並建立自定義實體類型
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import re
import json
from datetime import datetime

# 使用 Graphiti 原生格式
from graphiti_core.nodes import EpisodeType

# 導入統一的實體定義
from src.entities.tender_entities import (
    TenderCaseEntity, OrganizationEntity, AmountEntity, 
    DateEntity, CategoryEntity, ContractorEntity, TechnologyEntity
)

class EntityData(BaseModel):
    """實體資料結構 - 保留向後兼容性"""
    entity_type: str
    name: str
    properties: Dict[str, Any]

def extract_amount_value(amount_text: Optional[str]) -> Optional[float]:
    """從金額文字中提取數值"""
    if not amount_text:
        return None
    
    # 移除逗號和非數字字符，保留數字和小數點
    cleaned = re.sub(r'[^\d.]', '', amount_text.replace(',', ''))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def create_graphiti_episode(tender_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    建立符合 Graphiti 格式的 JSON episode
    
    Args:
        tender_data (Dict[str, Any]): 解析後的招標資料字典
    
    Returns:
        Dict[str, Any]: Graphiti episode 配置
    """
    tender_name = tender_data.get('tender_name', '未知招標案')
    
    # 結構化 episode 內容
    episode_content = {
        'tender_info': {
            'name': tender_data.get('tender_name'),
            'agency': tender_data.get('agency'),
            'case_number': tender_data.get('case_number'),
            'tender_method': tender_data.get('tender_method'),
            'decision_method': tender_data.get('decision_method'),
            'procurement_type': tender_data.get('procurement_type'),
            'tender_stage': tender_data.get('tender_stage'),
            'performance_location': tender_data.get('performance_location'),
            'performance_period': tender_data.get('performance_period')
        },
        'dates': {
            'announcement_date': tender_data.get('announcement_date'),
            'bid_deadline': tender_data.get('bid_deadline'),
            'bid_opening_time': tender_data.get('bid_opening_time'),
            'contract_period': tender_data.get('contract_period')
        },
        'amounts': {
            'budget': tender_data.get('budget'),
            'estimated_amount': tender_data.get('estimated_amount'),
            'award_amount': tender_data.get('award_amount'),
            'document_fee': tender_data.get('document_fee'),
            'system_usage_fee': tender_data.get('system_usage_fee')
        },
        'agency_info': tender_data.get('agency_info', {}),
        'category_info': tender_data.get('category_info', {}),
        'contractor': tender_data.get('contractor'),
        'description': tender_data.get('description'),
        'requirement': tender_data.get('requirement'),
        'scope': tender_data.get('scope')
    }
    
    # 移除空值以保持資料乾淨
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items() if v is not None and v != {} and v != []}
        elif isinstance(d, list):
            return [clean_dict(item) for item in d if item is not None]
        else:
            return d
    
    episode_content = clean_dict(episode_content)
    
    return {
        'name': f"tender_{tender_name}",
        'episode_body': episode_content,
        'source': EpisodeType.json,
        'source_description': f"政府採購案 - {tender_data.get('agency', '未知機關')}",
        'reference_time': datetime.now()
    }

def convert_tender_data_to_episodes(tender_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    將結構化招標資料轉換為 Graphiti Episodes
    
    Args:
        tender_data (Dict[str, Any]): 解析後的招標資料字典
    
    Returns:
        List[Dict[str, Any]]: 轉換後的 Graphiti Episode 列表
    """
    episodes = []
    
    # 建立主要的招標案 episode
    main_episode = create_graphiti_episode(tender_data)
    episodes.append(main_episode)
    
    return episodes

def extract_technology_keywords(text: str) -> List[str]:
    """
    從文字中提取技術關鍵字，特別針對大數據相關技術
    
    Args:
        text (str): 要分析的文字
        
    Returns:
        List[str]: 找到的技術關鍵字列表
    """
    if not text:
        return []
    
    # 大數據和 AI 相關關鍵字字典
    technology_keywords = {
        "大數據": ["大數據", "Big Data", "巨量資料", "海量資料"],
        "人工智慧": ["人工智慧", "AI", "Artificial Intelligence", "機器學習", "Machine Learning", "深度學習", "Deep Learning"],
        "資料科學": ["資料科學", "Data Science", "數據分析", "資料分析", "Data Analytics"],
        "雲端運算": ["雲端", "Cloud", "雲端運算", "Cloud Computing", "雲端服務"],
        "資料倉儲": ["資料倉儲", "Data Warehouse", "數據倉儲", "ETL"],
        "商業智慧": ["商業智慧", "BI", "Business Intelligence", "決策支援"],
        "物聯網": ["物聯網", "IoT", "Internet of Things", "感測器"],
        "區塊鏈": ["區塊鏈", "Blockchain", "分散式帳本"],
        "資料庫": ["資料庫", "Database", "MySQL", "PostgreSQL", "MongoDB", "NoSQL"],
        "視覺化": ["視覺化", "Visualization", "圖表", "Dashboard", "儀表板"],
        "預測分析": ["預測分析", "Predictive Analytics", "預測模型", "統計分析"],
        "自然語言處理": ["自然語言處理", "NLP", "Natural Language Processing", "文字探勘"],
    }
    
    found_keywords = []
    text_lower = text.lower()
    
    for main_keyword, variations in technology_keywords.items():
        for variation in variations:
            if variation.lower() in text_lower:
                found_keywords.append(main_keyword)
                break  # 找到一個就跳出，避免重複
    
    return list(set(found_keywords))  # 去重

def create_tender_entities(tender_data: Dict[str, Any]) -> List[EntityData]:
    """
    從招標資料建立自定義實體，支援擴展的實體類型
    包含新的日期類型、分類實體和增強的屬性

    Args:
        tender_data (Dict[str, Any]): 解析後的招標資料字典

    Returns:
        List[EntityData]: 實體資料列表
    """
    entities = []
    
    # 招標案實體 - 擴展版本
    tender_name = tender_data.get('tender_name')
    if tender_name:
        entities.append(EntityData(
            entity_type="TenderCase",
            name=str(tender_name),
            properties={
                "tender_id": tender_data.get('tender_id'),
                "tender_name": tender_name,
                "case_number": tender_data.get('case_number'),
                "tender_method": tender_data.get('tender_method'),
                "decision_method": tender_data.get('decision_method'),
                "procurement_type": tender_data.get('procurement_type'),
                "tender_stage": tender_data.get('tender_stage'),
                "announcement_sequence": tender_data.get('announcement_sequence'),
                "is_multiple_award": tender_data.get('is_multiple_award'),
                "has_reserve_price": tender_data.get('has_reserve_price'),
                "subsequent_expansion": tender_data.get('subsequent_expansion'),
                "is_subsidized": tender_data.get('is_subsidized'),
                "document_fee": tender_data.get('document_fee'),
                "system_usage_fee": tender_data.get('system_usage_fee'),
                "performance_location": tender_data.get('performance_location'),
                "performance_period": tender_data.get('performance_period')
            }
        ))
    
    # 機關實體 - 擴展版本
    agency = tender_data.get('agency')
    if agency:
        agency_info = tender_data.get('agency_info', {})
        entities.append(EntityData(
            entity_type="Organization",
            name=str(agency),
            properties={
                "org_name": agency,
                "org_code": agency_info.get('org_code'),
                "org_address": agency_info.get('org_address'),
                "contact_person": agency_info.get('contact_person'),
                "contact_phone": agency_info.get('contact_phone'),
                "unit_name": agency_info.get('unit_name'),
                "contact_fax": agency_info.get('contact_fax'),
                "contact_email": agency_info.get('contact_email')
            }
        ))
    
    # 預算金額實體 - 擴展版本
    if tender_data.get('budget'):
        budget_value = extract_amount_value(tender_data.get('budget'))
        entities.append(EntityData(
            entity_type="Amount",
            name=f"預算金額_{tender_data.get('budget')}",
            properties={
                "amount_value": budget_value,
                "amount_text": tender_data.get('budget'),
                "amount_type": "預算金額",
                "currency": "TWD",
                "budget_amount": budget_value,
                "is_budget_public": tender_data.get('is_budget_public', True),
                "tax_included": True
            }
        ))
    
    # 預計金額實體（如果與預算金額不同）
    if tender_data.get('estimated_amount') and tender_data.get('estimated_amount') != tender_data.get('budget'):
        estimated_value = extract_amount_value(tender_data.get('estimated_amount'))
        entities.append(EntityData(
            entity_type="Amount",
            name=f"預計金額_{tender_data.get('estimated_amount')}",
            properties={
                "amount_value": estimated_value,
                "amount_text": tender_data.get('estimated_amount'),
                "amount_type": "預計金額",
                "currency": "TWD",
                "estimated_amount": estimated_value,
                "is_estimated_public": tender_data.get('is_estimated_public', True),
                "tax_included": True
            }
        ))
    
    # 決標金額實體（如果有）
    if tender_data.get('award_amount'):
        award_value = extract_amount_value(tender_data.get('award_amount'))
        entities.append(EntityData(
            entity_type="Amount",
            name=f"決標金額_{tender_data.get('award_amount')}",
            properties={
                "amount_value": award_value,
                "amount_text": tender_data.get('award_amount'),
                "amount_type": "決標金額",
                "currency": "TWD"
            }
        ))
    
    # 日期實體 - 擴展版本，支援多種日期類型
    
    # 公告日期
    if tender_data.get('announcement_date'):
        entities.append(EntityData(
            entity_type="Date",
            name=f"公告日期_{tender_data.get('announcement_date')}",
            properties={
                "date_value": tender_data.get('announcement_date'),
                "date_type": "公告日期",
                "announcement_date": tender_data.get('announcement_date'),
                "date_format": "ROC",
                "has_time_component": False,
                "timezone": "Asia/Taipei"
            }
        ))
    
    # 截止投標日期時間
    if tender_data.get('bid_deadline'):
        entities.append(EntityData(
            entity_type="Date",
            name=f"截止投標_{tender_data.get('bid_deadline')}",
            properties={
                "date_value": tender_data.get('bid_deadline'),
                "date_type": "截止投標",
                "bid_deadline": tender_data.get('bid_deadline'),
                "date_format": "ROC",
                "has_time_component": ":" in str(tender_data.get('bid_deadline', '')),
                "timezone": "Asia/Taipei"
            }
        ))
    
    # 開標時間
    if tender_data.get('bid_opening_time'):
        entities.append(EntityData(
            entity_type="Date",
            name=f"開標時間_{tender_data.get('bid_opening_time')}",
            properties={
                "date_value": tender_data.get('bid_opening_time'),
                "date_type": "開標時間",
                "bid_opening_time": tender_data.get('bid_opening_time'),
                "date_format": "ROC",
                "has_time_component": ":" in str(tender_data.get('bid_opening_time', '')),
                "timezone": "Asia/Taipei"
            }
        ))
    
    # 履約期限
    if tender_data.get('contract_period'):
        entities.append(EntityData(
            entity_type="Date",
            name=f"履約期限_{tender_data.get('contract_period')}",
            properties={
                "date_value": tender_data.get('contract_period'),
                "date_type": "履約期限",
                "contract_period_text": tender_data.get('contract_period'),
                "date_format": "ROC",
                "timezone": "Asia/Taipei"
            }
        ))
    
    # 新增：分類實體
    if tender_data.get('category_info'):
        category_info = tender_data.get('category_info', {})
        category_name = category_info.get('category_name', '未分類')
        
        entities.append(EntityData(
            entity_type="Category",
            name=f"分類_{category_name}",
            properties={
                "procurement_type": category_info.get('procurement_type'),
                "category_code": category_info.get('category_code'),
                "category_name": category_name,
                "full_category_description": category_info.get('full_description'),
                "procurement_nature": category_info.get('procurement_nature'),
                "amount_level": category_info.get('amount_level'),
                "is_electronic_bidding": category_info.get('is_electronic_bidding'),
                "is_commercial_item": category_info.get('is_commercial_item'),
                "is_package_deal": category_info.get('is_package_deal')
            }
        ))
    
    # 技術關鍵字實體 - 保持原有功能
    all_text = " ".join([
        str(tender_data.get('tender_name', '')),
        str(tender_data.get('description', '')),
        str(tender_data.get('requirement', '')),
        str(tender_data.get('scope', ''))
    ])
    
    tech_keywords = extract_technology_keywords(all_text)
    for keyword in tech_keywords:
        entities.append(EntityData(
            entity_type="Technology",
            name=keyword,
            properties={
                "technology_name": keyword,
                "category": "資訊科技",
                "domain": "大數據與AI" if keyword in ["大數據", "人工智慧", "資料科學", "機器學習"] else "資訊技術"
            }
        ))
    
    # 承包商實體（如果有決標資訊）
    if tender_data.get('contractor'):
        entities.append(EntityData(
            entity_type="Contractor",
            name=str(tender_data.get('contractor')),
            properties={
                "contractor_name": tender_data.get('contractor'),
                "contract_type": "得標廠商"
            }
        ))
    
    return entities

async def add_tender_episode_to_graphiti(graphiti_client, tender_data: Dict[str, Any]):
    """
    將招標 episode 添加到 Graphiti 使用正確的格式
    
    Args:
        graphiti_client: Graphiti 客戶端實例
        tender_data (Dict[str, Any]): 解析後的招標資料字典
    """
    episode_config = create_graphiti_episode(tender_data)
    
    await graphiti_client.add_episode(
        name=episode_config['name'],
        episode_body=episode_config['episode_body'],
        source=episode_config['source'],
        source_description=episode_config['source_description'],
        reference_time=episode_config['reference_time']
    )

async def add_multiple_tender_episodes(graphiti_client, tender_data_list: List[Dict[str, Any]]):
    """
    批量添加多個招標 episodes
    
    Args:
        graphiti_client: Graphiti 客戶端實例
        tender_data_list (List[Dict[str, Any]]): 招標資料列表
    """
    episodes = []
    for tender_data in tender_data_list:
        episode_config = create_graphiti_episode(tender_data)
        episodes.append(episode_config)
    
    # 使用批量操作提高效能
    await graphiti_client.add_episode_bulk(episodes)

def create_enhanced_fact_triples_entities(tender_data: Dict[str, Any]) -> List[EntityData]:
    """
    使用增強的實體創建邏輯，專門為 Fact Triples 方法準備
    基於政府採購網實際資料結構（如台電大數據平台案例）

    Args:
        tender_data (Dict[str, Any]): 解析後的招標資料字典

    Returns:
        List[EntityData]: 優化的實體資料列表
    """
    entities = create_tender_entities(tender_data)
    
    # 為 Fact Triples 方法優化實體屬性
    for entity in entities:
        # 確保所有屬性都不是 None，避免 Graphiti 處理問題
        cleaned_properties = {}
        for key, value in entity.properties.items():
            if value is not None:
                cleaned_properties[key] = value
        entity.properties = cleaned_properties
    
    return entities

def to_json_string(episode_config: Dict[str, Any]) -> str:
    """
    將 Graphiti episode 配置轉換為 JSON 字串
    
    Args:
        episode_config (Dict[str, Any]): Graphiti episode 配置
    
    Returns:
        str: JSON 字串
    """
    # 轉換非 JSON 可序列化的物件
    json_ready_config = episode_config.copy()
    
    # 處理 datetime 物件
    if 'reference_time' in json_ready_config:
        json_ready_config['reference_time'] = json_ready_config['reference_time'].isoformat()
    
    # 處理 EpisodeType 物件
    if 'source' in json_ready_config:
        if hasattr(json_ready_config['source'], 'value'):
            json_ready_config['source'] = json_ready_config['source'].value
        else:
            json_ready_config['source'] = str(json_ready_config['source'])
    
    return json.dumps(json_ready_config, ensure_ascii=False, indent=2)

# 示範使用方法
def example_usage():
    """
    示範如何使用新的 Graphiti 格式
    """
    # 範例招標資料
    sample_tender_data = {
        'tender_name': '台灣電力公司大數據平台建置案',
        'agency': '台灣電力公司',
        'budget': 'NT$5,000,000',
        'case_number': 'TPC-2024-001',
        'announcement_date': '113/01/15',
        'bid_deadline': '113/02/15 17:00'
    }
    
    # 建立 Graphiti episode
    episode_config = create_graphiti_episode(sample_tender_data)
    
    # 轉換為 JSON 字串
    json_string = to_json_string(episode_config)
    print(json_string)
    
    # 如果有 Graphiti 客戶端，可以這樣使用：
    # await add_tender_episode_to_graphiti(graphiti_client, sample_tender_data)
    
    return episode_config
