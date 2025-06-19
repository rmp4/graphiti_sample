"""
配置載入器

從 JSON 配置文件載入內容過濾和處理設定
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigLoader:
    """配置載入器"""
    
    def __init__(self, config_path: str = "config/content_filter_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            # 嘗試從多個位置載入配置文件
            possible_paths = [
                self.config_path,
                os.path.join(os.path.dirname(__file__), "..", self.config_path),
                os.path.join(os.getcwd(), self.config_path)
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    logger.info(f"成功載入配置文件: {path}")
                    return config
            
            logger.warning(f"找不到配置文件，使用預設配置")
            return self._get_default_config()
            
        except Exception as e:
            logger.error(f"載入配置文件時發生錯誤: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """取得預設配置"""
        return {
            "content_filter": {
                "enabled": True,
                "blacklist_keywords": [
                    "密碼", "password", "secret", "token", "key",
                    "個人資料", "身分證", "電話", "地址"
                ],
                "allowed_agencies": [],  # 空清單表示允許所有機關
                "content_limits": {
                    "min_length": 10,
                    "max_length": 10000
                }
            },
            "preview": {
                "enabled": True,
                "auto_approve_safe_content": False,
                "show_content_preview_length": 200
            },
            "processing": {
                "force_update": False,
                "batch_size": 10,
                "max_retries": 3
            },
            "logging": {
                "level": "INFO",
                "show_stats": True,
                "detailed_errors": True
            }
        }
    
    def get_content_filter_config(self) -> Dict[str, Any]:
        """取得內容過濾配置"""
        return self.config.get("content_filter", {})
    
    def get_preview_config(self) -> Dict[str, Any]:
        """取得預覽配置"""
        return self.config.get("preview", {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """取得處理配置"""
        return self.config.get("processing", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """取得日誌配置"""
        return self.config.get("logging", {})
    
    def is_content_filter_enabled(self) -> bool:
        """檢查內容過濾是否啟用"""
        return self.get_content_filter_config().get("enabled", True)
    
    def is_preview_enabled(self) -> bool:
        """檢查預覽是否啟用"""
        return self.get_preview_config().get("enabled", True)
    
    def get_blacklist_keywords(self) -> List[str]:
        """取得黑名單關鍵詞"""
        return self.get_content_filter_config().get("blacklist_keywords", [])
    
    def get_allowed_agencies(self) -> List[str]:
        """取得允許的機關清單"""
        return self.get_content_filter_config().get("allowed_agencies", [])
    
    def get_content_limits(self) -> Dict[str, int]:
        """取得內容長度限制"""
        return self.get_content_filter_config().get("content_limits", {
            "min_length": 10,
            "max_length": 10000
        })
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """儲存配置到文件"""
        try:
            save_path = config_path or self.config_path
            
            # 確保目錄存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已儲存到: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"儲存配置時發生錯誤: {e}")
            return False
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """更新配置值"""
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            logger.info(f"更新配置: {section}.{key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"更新配置時發生錯誤: {e}")
            return False
    
    def add_blacklist_keyword(self, keyword: str) -> bool:
        """新增黑名單關鍵詞"""
        try:
            keywords = self.get_blacklist_keywords()
            if keyword not in keywords:
                keywords.append(keyword)
                self.update_config("content_filter", "blacklist_keywords", keywords)
                return True
            return False
        except Exception as e:
            logger.error(f"新增黑名單關鍵詞時發生錯誤: {e}")
            return False
    
    def add_allowed_agency(self, agency: str) -> bool:
        """新增允許的機關"""
        try:
            agencies = self.get_allowed_agencies()
            if agency not in agencies:
                agencies.append(agency)
                self.update_config("content_filter", "allowed_agencies", agencies)
                return True
            return False
        except Exception as e:
            logger.error(f"新增允許機關時發生錯誤: {e}")
            return False
    
    def print_config(self):
        """列印當前配置"""
        logger.info("=== 當前配置 ===")
        logger.info(f"內容過濾: {'啟用' if self.is_content_filter_enabled() else '停用'}")
        logger.info(f"預覽功能: {'啟用' if self.is_preview_enabled() else '停用'}")
        
        limits = self.get_content_limits()
        logger.info(f"內容長度限制: {limits['min_length']} - {limits['max_length']}")
        
        keywords = self.get_blacklist_keywords()
        logger.info(f"黑名單關鍵詞: {len(keywords)} 個")
        
        agencies = self.get_allowed_agencies()
        if agencies:
            logger.info(f"允許的機關: {len(agencies)} 個")
        else:
            logger.info("允許的機關: 全部")

# 全域配置實例
config_loader = ConfigLoader()
