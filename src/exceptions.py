"""
自訂異常類別定義

定義專案特定的異常類別以改善錯誤處理和偵錯
"""

class GraphitiSampleError(Exception):
    """專案基礎異常類別"""
    pass

class ConfigurationError(GraphitiSampleError):
    """配置相關錯誤"""
    pass

class DataIntegrityError(GraphitiSampleError):
    """資料完整性錯誤"""
    pass

class GraphitiConnectionError(GraphitiSampleError):
    """Graphiti 連接錯誤"""
    pass

class ParsingError(GraphitiSampleError):
    """資料解析錯誤"""
    pass

class ValidationError(GraphitiSampleError):
    """資料驗證錯誤"""
    pass

class ExternalServiceError(GraphitiSampleError):
    """外部服務錯誤（如 OpenAI API）"""
    pass

class TenderDataError(GraphitiSampleError):
    """招標資料相關錯誤"""
    pass