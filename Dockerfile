FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev && rm -rf /root/.cache/uv

COPY src/ src/
COPY data/ data/

EXPOSE 8000 8501

COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh
ENV DOCKER=1
CMD ["bash", "/app/run.sh"]
