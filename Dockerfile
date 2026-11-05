FROM python:3.11.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --requirement requirements.txt

COPY configs ./configs
COPY data ./data
COPY src ./src
COPY notebooks ./notebooks

# Default: full Task 3 pipeline (process raw log -> aggregate -> figures).
# Smoke test only: docker run --rm <image> python src/benchmark.py
CMD ["sh", "-c", "python src/process_data.py && python src/visualize.py"]
