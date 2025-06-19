"""Define the configurable parameters for the tender search agent."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Annotated

from langchain_core.runnables import ensure_config
from langgraph.config import get_config

@dataclass(kw_only=True)
class Configuration:
    """The configuration for the tender search agent."""

    system_prompt: str = field(
        default="""你是一個專業的政府招標案搜尋助手。

你的任務是幫助用戶搜尋和查詢政府招標案資訊。你可以：

1. 搜尋特定關鍵字相關的招標案
2. 根據機關名稱查詢招標案
3. 按金額範圍搜尋招標案
4. 按類別搜尋招標案
5. 按日期範圍搜尋招標案

請使用繁體中文回答，並提供清晰、有用的資訊。當找到招標案時，請包含：
- 招標案名稱
- 主辦機關
- 預算金額（如果有）
- 簡要描述

當前系統時間：{system_time}

如果沒有找到相關招標案，請建議用戶嘗試其他搜尋關鍵字或條件。""",
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the tender search agent."
        },
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4",
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    max_search_results: int = field(
        default=10,
        metadata={
            "description": "The maximum number of search results to return for each search query."
        },
    )

    @classmethod
    def from_context(cls) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        try:
            config = get_config()
        except RuntimeError:
            config = None
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})
