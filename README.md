# Graphiti HTML 內容處理與 Neo4j Docker Compose 範例

這是一個簡單的 Graphiti 專案範例，展示如何使用 Docker Compose 啟動 Neo4j，並將 HTML 內容解析後導入 Graphiti 知識圖譜。

## 功能特色

- 使用 Docker Compose 管理 Neo4j 資料庫
- 解析 HTML 檔案並提取標題與段落
- 將內容轉換為 Graphiti Episodes
- 執行知識圖譜搜尋並顯示結果
- 顯示圖譜統計資訊

## 環境需求

- Python 3.10+
- Docker 和 Docker Compose
- OpenAI API 金鑰

## 快速開始

### 1. 啟動 Neo4j

```bash
docker-compose up -d
```

### 2. 安裝依賴

```bash
uv sync
```

### 3. 設定環境變數

複製環境變數範例檔案並填入您的 API 金鑰：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，填入您的 `OPENAI_API_KEY`。

### 4. 執行範例

```bash
uv run src/main.py
```

## 預期輸出

程式執行後，您將看到：

- Neo4j 連線成功訊息
- HTML 檔案解析結果
- Episodes 建立過程
- 知識圖譜搜尋結果
- 節點與關係數量統計

範例輸出：
```
INFO:__main__:連接 Graphiti
INFO:__main__:讀取 HTML 檔案: sample_data/sample.html
INFO:__main__:解析出 2 個 Episodes
INFO:__main__:新增 Episode: Graphiti 知識圖譜測試
INFO:__main__:新增 Episode: 技術特點
INFO:__main__:搜尋知識圖譜: Graphiti
INFO:__main__:搜尋結果:
INFO:__main__:- Graphiti 是一個知識圖譜建構工具
INFO:__main__:- 支援多種 LLM 提供商
INFO:__main__:知識圖譜節點數量: 8
INFO:__main__:知識圖譜關係數量: 12
```

## 專案結構

```
graphiti_sample/
├── src/                     # 原始碼目錄
│   ├── __init__.py
│   └── main.py             # 主程式
├── sample_data/            # 範例資料
│   └── sample.html         # 範例 HTML 檔案
├── docker-compose.yml      # Docker Compose 設定
├── pyproject.toml          # 專案配置與依賴
├── .env.example           # 環境變數範例
├── .env                   # 環境變數（需自行建立）
└── README.md              # 專案說明
```

## 環境變數說明

在 `.env` 檔案中設定以下變數：

- `OPENAI_API_KEY`: OpenAI API 金鑰（必填）
- `NEO4J_URI`: Neo4j 連線 URI（預設: bolt://localhost:7687）
- `NEO4J_USER`: Neo4j 使用者名稱（預設: neo4j）
- `NEO4J_PASSWORD`: Neo4j 密碼（預設: password）

## 技術架構

- **資料庫**: Neo4j 5.26.0
- **Python 框架**: 異步 asyncio
- **HTML 解析**: BeautifulSoup4
- **知識圖譜**: Graphiti Core
- **資料驗證**: Pydantic

## 後續擴展

您可以基於此範例進行以下擴展：

1. 支援更多 HTML 標籤類型
2. 批量處理多個 HTML 檔案
3. 新增網頁爬取功能
4. 整合其他 LLM 提供商
5. 建立 Web 介面

## 疑難排解

### 常見問題

1. **Neo4j 連線失敗**
   - 確認 Docker 容器已正常啟動
   - 檢查埠號是否被占用

2. **OpenAI API 錯誤**
   - 驗證 API 金鑰是否正確
   - 確認帳戶有足夠額度

3. **模組導入錯誤**
   - 執行 `uv sync` 重新安裝依賴
   - 確認 Python 版本符合需求

## 授權

此專案僅供學習與範例用途。
