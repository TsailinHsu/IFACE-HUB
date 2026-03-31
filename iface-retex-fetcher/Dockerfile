FROM python:3.14.3-slim-trixie

WORKDIR /app

# 安裝共用 iface-client package
COPY iface-client/ ./iface-client/
RUN pip install --no-cache-dir ./iface-client

# 安裝 fetcher 專屬套件
COPY iface-retex-fetcher/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY iface-retex-fetcher/app/ ./app/
