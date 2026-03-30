FROM python:3.14.3-slim-trixie

WORKDIR /app

# pymssql 需要 freetds-dev 編譯
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        freetds-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY init.py .
COPY initdb/ ./initdb/

CMD ["python", "init.py"]
