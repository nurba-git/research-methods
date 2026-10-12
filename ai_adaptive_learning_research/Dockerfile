FROM python:3.11.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --requirement requirements.txt
COPY configs ./configs
COPY data/sample ./data/sample
COPY src ./src
CMD ["python", "src/benchmark.py", "--config", "configs/config.yaml"]
