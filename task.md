# Graphiti HTML 內容處理與 Neo4j Docker Compose 範例任務

## 任務目標
建立一個簡單可運行的 Graphiti 專案範例，實現以下功能：
- 使用 Docker Compose 啟動 Neo4j
- 讀取並解析範例 HTML 內容
- 將解析後的內容導入 Graphiti 知識圖譜
- 顯示基本的知識圖譜結構與搜索結果
- 提供詳細的任務檢查清單，完成後可打勾確認

---

## 任務內容

### 1. 建立專案結構與環境設定
- [x] 建立 `docker-compose.yml`，包含 Neo4j 服務設定
- [x] 建立 `.env.example`，包含必要環境變數範例（如 OPENAI_API_KEY）
- [x] 建立 `requirements.txt`，列出必要 Python 依賴
- [x] 建立 `sample_data/sample.html`，包含測試用 HTML 內容

### 2. 實作核心功能
- [x] 實作 `src/main.py`，包含以下功能：
  - 連接 Neo4j 與 Graphiti
  - 讀取並解析 `sample_data/sample.html`，提取標題與段落
  - 將解析內容轉換為 Graphiti Episodes
  - 執行簡單的知識圖譜搜索並輸出結果
- [x] 使用異步架構實現，並包含基本錯誤處理與日誌輸出

### 3. 測試與驗證
- [x] 使用 Docker Compose 啟動 Neo4j
- [x] 安裝 Python 依賴
- [x] 設定環境變數（複製 `.env.example` 並填寫）
- [x] 執行 `src/main.py`，確認能成功導入 HTML 內容並顯示結果

### 4. 文件與規範
- [x] 撰寫 README.md，說明如何啟動環境與執行範例
- [x] 建立 `.cline_rules`，包含基本的程式碼風格與架構規範
- [x] 任務完成後，依據檢查清單逐項打勾確認

---

## 範例 HTML 內容 (sample_data/sample.html)

```html
<html>
<head><title>測試文章</title></head>
<body>
    <h1>Graphiti 知識圖譜測試</h1>
    <p>這是第一段內容，介紹 Graphiti 的基本概念。</p>
    <p>這是第二段內容，說明如何使用 Neo4j 儲存知識圖譜。</p>
    <h2>技術特點</h2>
    <p>Graphiti 支援多種 LLM 提供商，包括 OpenAI 和 Anthropic。</p>
</body>
</html>
```

---

## Docker Compose 範例 (docker-compose.yml)

```yaml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.26.0
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data

volumes:
  neo4j_data:
```

---

## Python 依賴 (requirements.txt)

```
graphiti-core
beautifulsoup4
aiohttp
lxml
html2text
pydantic
```

---

## 執行流程簡述

1. 啟動 Neo4j 容器：`docker-compose up -d`
2. 使用 Poetry 安裝依賴：`poetry install`
3. 複製 `.env.example` 為 `.env`，並填入您的 OPENAI_API_KEY
4. 使用 uv 執行主程式：`uv run src/main.py`

---

## 預期結果

- 成功連接 Neo4j
- 讀取並解析 HTML 範例內容
- 將內容轉換為 Graphiti Episodes 並存入 Neo4j
- 顯示知識圖譜節點與關係數量
- 輸出簡單的搜索結果示例

---

此任務文件將作為後續開發與驗證的依據，請依照檢查清單逐步完成並打勾確認。

---

# 政府採購資料知識圖譜處理任務

## 任務目標
建立一個完整的政府採購資料處理系統，實現以下功能：
- 爬取政府採購網招標資料
- 結構化解析採購資訊
- 建立多層次的知識圖譜
- 實現廠商關係、預算分析、採購趨勢等深度分析
- 提供完整的任務檢查清單，完成後可打勾確認

---

## 第一階段：基礎架構建立

### 1.1 資料爬取模組
- [x] 建立 `src/scrapers/tender_scraper.py`
  - [x] 實作政府採購網頁面爬取功能
  - [x] 處理動態載入內容（如需要）
  - [x] 實作反爬蟲機制應對
  - [x] 添加請求間隔與重試機制
- [ ] 建立 `src/models/tender_models.py`
  - [ ] 定義招標基本資訊 `TenderBasic` 模型
  - [ ] 定義招標規格 `TenderSpecification` 模型
  - [ ] 定義投標結果 `BiddingResult` 模型
  - [ ] 定義廠商資訊 `VendorInfo` 模型

### 1.2 資料解析與清理
- [x] 建立 `src/parsers/tender_parser.py`
  - [x] 實作招標資訊表格解析
  - [x] 處理金額格式標準化
  - [x] 日期格式統一處理
  - [x] 廠商名稱標準化
- [ ] 建立 `src/utils/data_cleaner.py`
  - [ ] 重複資料檢測與清理
  - [ ] 資料完整性驗證
  - [ ] 異常值檢測與處理

---

## 第二階段：知識圖譜設計

### 2.1 Episode 架構設計
- [x] 建立 `src/episodes/tender_episodes.py`
  - [x] 實作核心資訊層 Episodes
    - [x] `招標基本資訊` Episode 類型
    - [ ] `決標結果` Episode 類型
  - [ ] 實作詳細資訊層 Episodes
    - [ ] `招標規格需求` Episode 類型
    - [ ] `投標廠商資訊` Episode 類型
  - [ ] 實作分析資訊層 Episodes
    - [ ] `預算執行分析` Episode 類型
    - [ ] `廠商競爭模式` Episode 類型
    - [ ] `採購趨勢分析` Episode 類型

### 2.2 分組與優先級策略
- [ ] 實作分組管理機制
  - [ ] `tender_basic` - 基本招標資訊群組
  - [ ] `tender_detail` - 詳細招標內容群組
  - [ ] `vendor_analysis` - 廠商關係分析群組
  - [ ] `budget_analysis` - 預算執行分析群組
  - [ ] `trend_analysis` - 採購趨勢分析群組
- [ ] 實作優先級權重系統
  - [ ] 定義 Episode 重要性權重
  - [ ] 實作智能去重邏輯
  - [ ] 建立關聯性評分機制

---

## 第三階段：批次處理系統

### 3.1 資料處理管線
- [ ] 建立 `src/pipelines/tender_pipeline.py`
  - [ ] 實作分階段處理流程
    - [ ] Phase 1: 核心資料建立
    - [ ] Phase 2: 詳細資訊補充
    - [ ] Phase 3: 關係分析建立
  - [ ] 實作批次處理管理
  - [ ] 建立進度追蹤與恢復機制
  - [ ] 添加錯誤處理與日誌記錄

### 3.2 效能優化
- [ ] 實作平行處理機制
  - [ ] 多執行緒爬取
  - [ ] 非同步資料處理
  - [ ] 批次資料庫操作
- [ ] 建立快取機制
  - [ ] 爬取結果快取
  - [ ] 解析結果快取
  - [ ] 圖譜查詢快取

---

## 第四階段：分析與查詢功能

### 4.1 廠商關係分析
- [ ] 建立 `src/analyzers/vendor_analyzer.py`
  - [ ] 廠商競爭關係分析
  - [ ] 廠商合作模式識別
  - [ ] 市場集中度分析
  - [ ] 廠商勝率統計
- [ ] 實作廠商網絡可視化
  - [ ] 生成廠商關係圖
  - [ ] 識別關鍵廠商節點
  - [ ] 分析廠商影響力

### 4.2 預算與採購模式分析
- [ ] 建立 `src/analyzers/budget_analyzer.py`
  - [ ] 預算執行效率分析
  - [ ] 決標金額與預算比較
  - [ ] 採購單價趨勢分析
  - [ ] 異常採購案件識別
- [ ] 建立 `src/analyzers/trend_analyzer.py`
  - [ ] 時間序列採購趨勢
  - [ ] 季節性採購模式
  - [ ] 機關採購行為分析
  - [ ] 市場變化趨勢預測

### 4.3 智能查詢與搜尋
- [ ] 建立 `src/queries/tender_queries.py`
  - [ ] 複合條件查詢功能
  - [ ] 語義化搜尋介面
  - [ ] 關聯推薦系統
  - [ ] 異常案件檢測查詢

---

## 第五階段：使用者介面與報告

### 5.1 命令列介面
- [ ] 建立 `src/cli/tender_cli.py`
  - [ ] 爬取任務管理指令
  - [ ] 資料分析查詢指令
  - [ ] 圖譜狀態檢查指令
  - [ ] 報告生成指令

### 5.2 分析報告生成
- [ ] 建立 `src/reports/report_generator.py`
  - [ ] 廠商競爭力報告
  - [ ] 採購效率分析報告
  - [ ] 市場趨勢預測報告
  - [ ] 異常案件調查報告
- [ ] 實作多格式輸出
  - [ ] PDF 報告生成
  - [ ] Excel 數據匯出
  - [ ] HTML 互動報告
  - [ ] JSON API 介面

---

## 第六階段：系統整合與部署

### 6.1 系統整合測試
- [ ] 建立完整測試套件
  - [ ] 單元測試覆蓋率 > 80%
  - [ ] 整合測試案例
  - [ ] 效能壓力測試
  - [ ] 資料品質驗證測試
- [ ] 建立持續整合管線
  - [ ] 自動化測試流程
  - [ ] 程式碼品質檢查
  - [ ] 自動化部署腳本

### 6.2 生產環境部署
- [ ] 建立 Docker 容器化
  - [ ] 應用程式容器化
  - [ ] 資料庫容器配置
  - [ ] 反向代理設定
- [ ] 建立監控與維護
  - [ ] 系統監控儀表板
  - [ ] 錯誤追蹤機制
  - [ ] 資料備份策略
  - [ ] 定期維護腳本

---

## 專案檔案結構

```
src/
├── scrapers/
│   ├── __init__.py
│   ├── tender_scraper.py
│   └── scraper_utils.py
├── parsers/
│   ├── __init__.py
│   ├── tender_parser.py
│   └── data_validator.py
├── models/
│   ├── __init__.py
│   ├── tender_models.py
│   └── episode_models.py
├── episodes/
│   ├── __init__.py
│   ├── tender_episodes.py
│   └── episode_factory.py
├── pipelines/
│   ├── __init__.py
│   ├── tender_pipeline.py
│   └── pipeline_manager.py
├── analyzers/
│   ├── __init__.py
│   ├── vendor_analyzer.py
│   ├── budget_analyzer.py
│   └── trend_analyzer.py
├── queries/
│   ├── __init__.py
│   ├── tender_queries.py
│   └── query_builder.py
├── reports/
│   ├── __init__.py
│   ├── report_generator.py
│   └── templates/
├── cli/
│   ├── __init__.py
│   └── tender_cli.py
├── utils/
│   ├── __init__.py
│   ├── data_cleaner.py
│   ├── config_manager.py
│   └── logger.py
└── main.py
```

---

## 執行優先順序建議

### 第一週：基礎架構
- 完成第一階段所有任務
- 建立基本的爬取與解析功能
- 驗證資料品質

### 第二週：知識圖譜
- 完成第二階段核心任務
- 實作基本的 Episode 架構
- 測試小規模資料處理

### 第三週：批次處理
- 完成第三階段批次系統
- 實作效能優化
- 大規模資料測試

### 第四週：分析功能
- 完成第四階段分析功能
- 實作各種分析器
- 驗證分析結果準確性

### 第五六週：介面與部署
- 完成使用者介面
- 系統整合測試
- 生產環境部署

---

## 成功標準

### 功能性指標
- [ ] 能夠爬取並處理至少 1000 筆招標資料
- [ ] 知識圖譜包含完整的實體關係
- [ ] 分析功能產生有意義的洞察
- [ ] 查詢回應時間 < 5 秒

### 品質指標
- [ ] 資料準確率 > 95%
- [ ] 系統可用性 > 99%
- [ ] 測試覆蓋率 > 80%
- [ ] 文件完整性 100%

---

此政府採購資料處理任務將建立一個完整的智能分析系統，請按照檢查清單逐步完成並打勾確認進度。
