# LangGraph + Graphiti 招標搜尋系統整合

## 概述

這個專案整合了 LangGraph 和 Graphiti，建立了一個智能招標搜尋系統，能夠理解自然語言查詢並提供精確的政府採購資訊。

## 架構設計

```
src/langgraph_integration/
├── tools/                     # 搜尋工具模組
│   ├── tender_search_tools.py # 招標搜尋工具
│   ├── result_formatter.py    # 結果格式化器
│   └── intent_analyzer.py     # 意圖分析器
├── workflow/                  # LangGraph 工作流程
│   ├── state_manager.py       # 狀態管理器
│   ├── node_functions.py      # 節點函數
│   └── tender_search_graph.py # 主要工作流程圖
├── demo/                      # 演示和測試
│   └── interactive_demo.py    # 互動演示
└── README.md                  # 本文件
```

## 核心功能

### 1. 意圖分析 (Intent Analysis)
- 自動識別查詢類型：機關、金額、類別、日期、綜合
- 提取查詢參數
- 提供信心度評分

### 2. 多策略搜尋 (Multi-Strategy Search)
- **機關搜尋**: 根據政府機關名稱搜尋
- **金額搜尋**: 依據預算範圍篩選
- **類別搜尋**: 按採購類別分類搜尋
- **日期搜尋**: 根據公告或截止日期搜尋
- **綜合搜尋**: 關鍵字全文搜尋

### 3. 智能結果處理 (Smart Result Processing)
- 結果品質評估
- 自動精煉和改善
- 多格式回應生成
- 搜尋建議提供

### 4. 對話式互動 (Conversational Interface)
- 上下文記憶
- 後續查詢處理
- 自然語言回應

## 使用方式

### 基本使用

```python
from langgraph_integration.workflow.tender_search_graph import search_tenders

# 簡單查詢
result = search_tenders("台電的電力設備招標")

print(result['response'])
print(f"找到 {result['result_count']} 個結果")
```

### 異步使用

```python
import asyncio
from langgraph_integration.workflow.tender_search_graph import search_tenders_async

async def main():
    result = await search_tenders_async("預算100萬以上的採購案")
    print(result['response'])

asyncio.run(main())
```

### 對話式使用

```python
from langgraph_integration.workflow.tender_search_graph import TenderSearchInterface

interface = TenderSearchInterface()

# 第一次查詢
response1 = interface.search("台電招標")
print(response1)

# 後續查詢（保持上下文）
response2 = interface.search("再找一些類似的")
print(response2)
```

## 演示程式

執行互動演示：

```bash
cd src/langgraph_integration/demo
python interactive_demo.py
```

演示功能：
- 互動式查詢介面
- 批次測試模式
- 系統資訊展示
- 對話歷史管理

## 查詢範例

### 機關搜尋
```
台電的電力設備招標
教育部最近的採購案
衛生局相關招標
```

### 金額搜尋
```
預算100萬以上的採購案
50萬到200萬的招標
超過500萬的工程案
```

### 類別搜尋
```
電腦設備相關採購
建築工程招標
醫療器材採購案
```

### 日期搜尋
```
最近一個月的招標
2024年的採購案
今年教育部的招標
```

### 綜合查詢
```
台電100萬以上的電力設備招標
教育部最近的建築工程案
衛生局醫療設備採購
```

## API 參考

### search_tenders(user_query, conversation_history=None)

執行招標搜尋。

**參數:**
- `user_query` (str): 使用者查詢字串
- `conversation_history` (list, optional): 對話歷史

**回傳:**
```python
{
    "response": str,              # 格式化回應
    "response_type": str,         # 回應類型
    "search_results": list,       # 原始搜尋結果
    "result_count": int,          # 結果數量
    "search_time_ms": int,        # 搜尋時間
    "result_quality": float,      # 結果品質 (0-1)
    "intent": str,                # 識別意圖
    "intent_confidence": float,   # 意圖信心度
    "status": str,                # 執行狀態
    "error": str,                 # 錯誤訊息
    "conversation_history": list  # 更新後的對話歷史
}
```

## 設定和配置

### 環境要求

```bash
# 安裝必要依賴
pip install langchain-core langgraph langchain-openai
pip install graphiti-core
```

### 環境變數

確保設定以下環境變數：

```bash
# OpenAI API (用於 LLM 功能)
OPENAI_API_KEY=your_openai_key

# Graphiti 資料庫設定
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

## 開發狀態

### ✅ 已完成 (第一階段)

- [x] 基礎工具架構
- [x] 意圖分析系統
- [x] 搜尋工具實作
- [x] 結果格式化器
- [x] 狀態管理系統
- [x] LangGraph 工作流程
- [x] 互動演示程式

### 🚧 進行中 (第二階段)

- [ ] 實際 Graphiti 整合
- [ ] LangChain 依賴項整合
- [ ] 完整測試套件
- [ ] 效能優化

### 📋 待辦 (後續階段)

- [ ] 上下文記憶增強
- [ ] 多語言支援
- [ ] 進階搜尋策略
- [ ] 結果快取機制
- [ ] 監控和分析

## 故障排除

### 常見問題

1. **Import 錯誤**
   ```
   ImportError: No module named 'langchain_core'
   ```
   解決方案：安裝 langchain 依賴項
   ```bash
   pip install langchain-core langgraph
   ```

2. **Graphiti 連線失敗**
   ```
   ConnectionError: Could not connect to Neo4j
   ```
   解決方案：檢查 Neo4j 服務狀態和連線設定

3. **搜尋結果為空**
   - 檢查 Graphiti 資料庫是否有資料
   - 確認搜尋關鍵字正確
   - 查看系統日誌了解詳細錯誤

### 除錯模式

啟用詳細日誌：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 貢獻指南

1. 遵循現有的程式碼風格
2. 為新功能添加測試
3. 更新相關文檔
4. 提交前執行測試套件

## 授權

本專案採用 MIT 授權條款。

## 聯絡資訊

如有問題或建議，請參考 task.md 中的詳細開發計劃。
