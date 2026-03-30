FROM python:3.14.3-slim-trixie

WORKDIR /app

# pymssql 需要 freetds-dev 編譯；curl 供 healthcheck 使用
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        freetds-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
