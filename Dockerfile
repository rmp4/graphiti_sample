FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 pyproject.toml 以安裝依賴
COPY pyproject.toml ./

# 安裝 Python 依賴
RUN pip install --no-cache-dir -e .

# 複製源代碼
COPY . .

# 設定環境變數
ENV PYTHONPATH=/app/src:$PYTHONPATH

# 暴露端口 (LangGraph CLI 預設使用 8123)
EXPOSE 8123

# 啟動命令
CMD ["python", "-m", "langgraph", "up"]
