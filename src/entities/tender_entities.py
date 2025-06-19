"""
政府採購網自定義實體類型定義

定義招標相關的結構化實體類型，包含招標案、機關、金額、日期等
擴展版本：增強日期處理、標的分類、關係定義等功能
"""

from typing import Optional, Dict, Any
from graphiti_core.nodes import EntityNode
from pydantic import BaseModel, Field

class TenderCaseEntity(BaseModel):
    """招標案實體 - 擴展版本"""
    entity_type: str = "TenderCase"
    
    # 原有基本欄位
    tender_id: Optional[str] = Field(None, description="招標案ID")
    case_number: Optional[str] = Field(None, description="標案案號")
    tender_name: Optional[str] = Field(None, description="招標案名稱")
    tender_status: Optional[str] = Field(None, description="招標狀態")
    tender_method: Optional[str] = Field(None, description="招標方式")
    procurement_type: Optional[str] = Field(None, description="採購性質")
    
    # 新增：決標相關
    decision_method: Optional[str] = Field(None, description="決標方式 (如: 準用最有利標)")
    is_multiple_award: Optional[bool] = Field(None, description="是否複數決標")
    has_reserve_price: Optional[bool] = Field(None, description="是否訂有底價")
    
    # 新增：招標狀態詳細資訊
    tender_stage: Optional[str] = Field(None, description="招標階段 (如: 第一次限制性招標)")
    announcement_sequence: Optional[str] = Field(None, description="公告傳輸次數")
    
    # 新增：特殊屬性
    subsequent_expansion: Optional[bool] = Field(None, description="是否有後續擴充")
    is_subsidized: Optional[bool] = Field(None, description="是否受機關補助")
    
    # 新增：文件相關
    document_fee: Optional[int] = Field(None, description="機關文件費")
    system_usage_fee: Optional[int] = Field(None, description="系統使用費")
    
    # 新增：履約相關
    performance_location: Optional[str] = Field(None, description="履約地點")
    performance_period: Optional[str] = Field(None, description="履約期限")

class OrganizationEntity(BaseModel):
    """機關實體 - 擴展版本"""
    entity_type: str = "Organization"
    
    # 原有基本欄位
    org_name: Optional[str] = Field(None, description="機關名稱")
    org_code: Optional[str] = Field(None, description="機關代碼")
    org_address: Optional[str] = Field(None, description="機關地址")
    contact_person: Optional[str] = Field(None, description="聯絡人")
    contact_phone: Optional[str] = Field(None, description="聯絡電話")
    
    # 新增：詳細聯絡資訊
    unit_name: Optional[str] = Field(None, description="單位名稱")
    contact_fax: Optional[str] = Field(None, description="傳真號碼")
    contact_email: Optional[str] = Field(None, description="電子郵件信箱")

class AmountEntity(BaseModel):
    """金額實體 - 支援多種金額類型"""
    entity_type: str = "Amount"
    
    # 原有基本欄位
    amount_value: Optional[float] = Field(None, description="金額數值")
    amount_text: Optional[str] = Field(None, description="金額文字")
    amount_type: Optional[str] = Field(None, description="金額類型")
    currency: str = Field("TWD", description="幣別")
    
    # 新增：具體金額類型
    budget_amount: Optional[float] = Field(None, description="預算金額")
    estimated_amount: Optional[float] = Field(None, description="預計金額")
    procurement_amount: Optional[float] = Field(None, description="採購金額")
    
    # 新增：稅務相關
    amount_with_tax: Optional[float] = Field(None, description="含稅金額")
    amount_without_tax: Optional[float] = Field(None, description="未稅金額")
    tax_included: Optional[bool] = Field(None, description="是否含稅")
    
    # 新增：金額公開性
    is_budget_public: Optional[bool] = Field(None, description="預算金額是否公開")
    is_estimated_public: Optional[bool] = Field(None, description="預計金額是否公開")

class DateEntity(BaseModel):
    """擴展的日期實體 - 支援政府採購網的各種日期類型"""
    entity_type: str = "Date"
    
    # 原有基本欄位
    date_value: Optional[str] = Field(None, description="日期值")
    date_type: Optional[str] = Field(None, description="日期類型")
    date_format: str = Field("ROC", description="日期格式")
    
    # 新增：政府採購網特定日期欄位
    announcement_date: Optional[str] = Field(None, description="公告日期 (如: 114/06/06)")
    bid_deadline: Optional[str] = Field(None, description="截止投標日期時間 (如: 114/07/07 17:00)")
    bid_opening_time: Optional[str] = Field(None, description="開標時間 (如: 114/07/08 13:30)")
    contract_start_date: Optional[str] = Field(None, description="履約開始日期")
    contract_end_date: Optional[str] = Field(None, description="履約結束日期")
    contract_period_text: Optional[str] = Field(None, description="履約期限文字描述")
    
    # 新增：日期處理相關欄位
    has_time_component: Optional[bool] = Field(None, description="是否包含時間資訊")
    timezone: str = Field("Asia/Taipei", description="時區")
    roc_year: Optional[int] = Field(None, description="民國年")
    gregorian_date: Optional[str] = Field(None, description="西元年日期")

class CategoryEntity(BaseModel):
    """採購標的分類實體 - 對應政府採購網標準分類"""
    entity_type: str = "Category"
    
    # 主要分類資訊
    procurement_type: Optional[str] = Field(None, description="採購類型 (工程類/財物類/勞務類)")
    category_code: Optional[str] = Field(None, description="分類代碼 (如: 849)")
    category_name: Optional[str] = Field(None, description="分類名稱 (如: 其他電腦服務)")
    full_category_description: Optional[str] = Field(None, description="完整分類描述")
    
    # 採購性質
    procurement_nature: Optional[str] = Field(None, description="採購性質 (如: 非屬財物之工程或勞務)")
    
    # 金額相關分類
    amount_level: Optional[str] = Field(None, description="金額級距 (巨額/查核金額等)")
    
    # 特殊屬性
    is_electronic_bidding: Optional[bool] = Field(None, description="是否採用電子競價")
    is_commercial_item: Optional[bool] = Field(None, description="是否為商業財物或服務")
    is_package_deal: Optional[bool] = Field(None, description="是否屬統包")

class ContractorEntity(BaseModel):
    """廠商實體"""
    entity_type: str = "Contractor"
    contractor_name: Optional[str] = Field(None, description="廠商名稱")
    contractor_id: Optional[str] = Field(None, description="廠商統編")
    award_amount: Optional[float] = Field(None, description="得標金額")

class TechnologyEntity(BaseModel):
    """技術實體"""
    entity_type: str = "Technology"
    technology_name: Optional[str] = Field(None, description="技術名稱")
    category: Optional[str] = Field(None, description="技術分類")
    domain: Optional[str] = Field(None, description="技術領域")
    description: Optional[str] = Field(None, description="技術描述")

# 新增：關係類型定義
class RelationshipTypes:
    """定義實體間的關係類型"""
    
    # 機關與標案關係
    ORG_TENDER_RELATIONS = [
        "hosts",           # 主辦
        "organizes",       # 辦理  
        "supervises",      # 監督
        "participates_in"  # 參與
    ]
    
    # 標案與分類關係  
    TENDER_CATEGORY_RELATIONS = [
        "belongs_to_category",  # 屬於分類
        "has_procurement_type", # 具有採購類型
        "classified_as"         # 被分類為
    ]
    
    # 標案與日期關係
    TENDER_DATE_RELATIONS = [
        "announced_on",         # 公告於
        "opens_bid_on",        # 開標於
        "deadline_on",         # 截止於
        "contract_period",     # 履約期間
        "starts_on",           # 開始於
        "ends_on"              # 結束於
    ]
    
    # 標案與金額關係
    TENDER_AMOUNT_RELATIONS = [
        "has_budget",          # 具有預算
        "has_estimated_cost",  # 具有預計金額
        "awarded_for"          # 決標金額
    ]
