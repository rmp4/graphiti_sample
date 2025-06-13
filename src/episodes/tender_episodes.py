"""
政府採購資料 Episode 轉換模組

將解析後的招標資料轉換為 Graphiti Episodes，並建立自定義實體類型
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import re

class Episode(BaseModel):
    title: str
    content: str

class EntityData(BaseModel):
    """實體資料結構"""
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

def convert_tender_data_to_episodes(tender_data: Dict[str, Any]) -> List[Episode]:
    """
    將結構化招標資料轉換為多個 Episodes，使用自定義實體類型

    Args:
        tender_data (Dict[str, Any]): 解析後的招標資料字典

    Returns:
        List[Episode]: 轉換後的 Episode 列表
    """
    episodes = []

    # 主要招標案描述（簡化的 content）
    tender_name = tender_data.get('tender_name', '未知招標案')
    main_content = f"這是關於「{tender_name}」的政府採購案件。"
    
    # 如果有額外的描述性資訊，可以加入
    if tender_data.get('description'):
        main_content += f"\n描述：{tender_data.get('description')}"

    episodes.append(Episode(
        title=f"招標案_{tender_name}",
        content=main_content,
    ))

    # 建立實體關聯資訊 Episode
    entities_info = []
    
    # 招標機關實體
    if tender_data.get('agency'):
        entities_info.append(f"招標機關：{tender_data.get('agency')}")
    
    # 預算金額實體
    if tender_data.get('budget'):
        entities_info.append(f"預算金額：{tender_data.get('budget')}")
    
    # 開標時間實體
    if tender_data.get('open_date'):
        entities_info.append(f"開標時間：{tender_data.get('open_date')}")
    
    # 決標金額實體（如果有）
    if tender_data.get('award_amount'):
        entities_info.append(f"決標金額：{tender_data.get('award_amount')}")

    if entities_info:
        entities_content = "此招標案涉及以下相關實體：\n" + "\n".join(entities_info)
        episodes.append(Episode(
            title=f"招標實體關聯_{tender_name}",
            content=entities_content,
        ))

    return episodes

def create_tender_entities(tender_data: Dict[str, Any]) -> List[EntityData]:
    """
    從招標資料建立自定義實體

    Args:
        tender_data (Dict[str, Any]): 解析後的招標資料字典

    Returns:
        List[EntityData]: 實體資料列表
    """
    entities = []
    
    # 招標案實體
    tender_name = tender_data.get('tender_name')
    if tender_name:
        entities.append(EntityData(
            entity_type="TenderCase",
            name=str(tender_name),
            properties={
                "tender_id": tender_data.get('tender_id'),
                "tender_name": tender_name,
                "case_number": tender_data.get('case_number'),
            }
        ))
    
    # 機關實體
    agency = tender_data.get('agency')
    if agency:
        entities.append(EntityData(
            entity_type="Organization",
            name=str(agency),
            properties={
                "org_name": agency,
            }
        ))
    
    # 預算金額實體
    if tender_data.get('budget'):
        budget_value = extract_amount_value(tender_data.get('budget'))
        entities.append(EntityData(
            entity_type="Amount",
            name=f"預算金額_{tender_data.get('budget')}",
            properties={
                "amount_value": budget_value,
                "amount_text": tender_data.get('budget'),
                "amount_type": "預算金額",
                "currency": "TWD"
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
    
    # 開標日期實體
    if tender_data.get('open_date'):
        entities.append(EntityData(
            entity_type="Date",
            name=f"開標時間_{tender_data.get('open_date')}",
            properties={
                "date_value": tender_data.get('open_date'),
                "date_type": "開標時間",
                "date_format": "ROC"
            }
        ))
    
    return entities
