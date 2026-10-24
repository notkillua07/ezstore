FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.20 /uv /uvx /bin/

WORKDIR /code

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY sales_advisor ./sales_advisor
COPY knowledge ./knowledge
COPY a2a ./a2a
RUN uv sync --frozen --no-dev

ENV PYTHONUNBUFFERED=1 \
    QUOTATION_AGENT_URL=http://agent:8080 \
    QUOTATION_AGENT_CARD=/code/a2a/quotation_agent_card.json

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=6 \
  CMD uv run --no-sync python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/list-apps', timeout=4).status == 200 else 1)"

CMD ["uv", "run", "--no-sync", "uvicorn", "sales_advisor.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
