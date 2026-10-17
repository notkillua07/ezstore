FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.20 /uv /uvx /bin/

WORKDIR /code

# 先只裝依賴（利用 layer cache），再複製程式碼
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY quotation_agent ./quotation_agent
RUN uv sync --frozen --no-dev

ARG AGENT_VERSION=0.0.0
ENV AGENT_VERSION=${AGENT_VERSION} \
    PYTHONUNBUFFERED=1 \
    MCP_URL=http://mcp-server:8000/mcp

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=6 \
  CMD uv run --no-sync python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/list-apps', timeout=4).status == 200 else 1)"

CMD ["uv", "run", "--no-sync", "uvicorn", "quotation_agent.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
