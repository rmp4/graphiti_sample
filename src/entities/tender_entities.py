"""
政府採購網自定義實體類型定義

定義招標相關的結構化實體類型，包含招標案、機關、金額、日期等
"""

from typing import Optional, Dict, Any
from graphiti_core.nodes import EntityNode
from pydantic import BaseModel, Field

class TenderCaseEntity(BaseModel):
    """招標案實體"""
    entity_type: str = "TenderCase"
    tender_id: Optional[str] = Field(None, description="招標案ID")
    case_number: Optional[str] = Field(None, description="標案案號")
    tender_name: Optional[str] = Field(None, description="招標案名稱")
    tender_status: Optional[str] = Field(None, description="招標狀態")
    tender_method: Optional[str] = Field(None, description="招標方式")
    procurement_type: Optional[str] = Field(None, description="採購性質")

class OrganizationEntity(BaseModel):
    """機關實體"""
    entity_type: str = "Organization"
    org_name: Optional[str] = Field(None, description="機關名稱")
    org_code: Optional[str] = Field(None, description="機關代碼")
    org_address: Optional[str] = Field(None, description="機關地址")
    contact_person: Optional[str] = Field(None, description="聯絡人")
    contact_phone: Optional[str] = Field(None, description="聯絡電話")

class AmountEntity(BaseModel):
    """金額實體"""
    entity_type: str = "Amount"
    amount_value: Optional[float] = Field(None, description="金額數值")
    amount_text: Optional[str] = Field(None, description="金額文字")
    amount_type: Optional[str] = Field(None, description="金額類型")  # 預算金額、決標金額等
    currency: str = Field("TWD", description="幣別")

class DateEntity(BaseModel):
    """日期實體"""
    entity_type: str = "Date"
    date_value: Optional[str] = Field(None, description="日期值")
    date_type: Optional[str] = Field(None, description="日期類型")  # 開標日期、截止投標日期等
    date_format: str = Field("ROC", description="日期格式")  # 民國年格式

class ContractorEntity(BaseModel):
    """廠商實體"""
    entity_type: str = "Contractor"
    contractor_name: Optional[str] = Field(None, description="廠商名稱")
    contractor_id: Optional[str] = Field(None, description="廠商統編")
    award_amount: Optional[float] = Field(None, description="得標金額")
