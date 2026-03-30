# iface-hub

多資料來源整合平台，透過 Docker Compose 將各外部系統的交易資料匯入 Cosmos ERP（地端 MSSQL）。

## 架構概覽

```
外部系統                      iface-db（核心服務）            Cosmos ERP
─────────────────            ────────────────────────        ────────────
EIP API          ──HTTP──▶   FastAPI                         MSSQL
EIP LL API       ──HTTP──▶   └─ /api/v1/iface/*    ──SP──▶  XXIF_*
RETEX POS API    ──HTTP──▶       transactions               Stored Procedures
xdelivery API    ──HTTP──▶       status-update
Super Landing    ──HTTP──▶       sp/{name}
                                 reply/{view}
                                 query/{view}
                                 named-query/{name}
```

各資料來源為獨立的 fetcher 容器，透過 HTTP 呼叫 `iface-db` API，不直接連接資料庫。

## 專案結構

```
iface-hub/
├── sql/                            MSSQL schema 參考文件
│   ├── 01-create-tables.sql        IFACE + IFACE_ERROR 資料表定義
│   └── 02-create-indexes.sql       效能索引
│
├── iface-initdb/                   資料庫初始化（init container，一次性執行）
│   └── initdb/
│       ├── 01-create-tables.sql    建表（IF NOT EXISTS，冪等）
│       └── 02-create-indexes.sql   建索引（IF NOT EXISTS，冪等）
│
├── iface-db/                       核心 API 服務（長期運行）
├── iface-eip-fetcher/              EIP 電商平台（公司 A / B 共用，YAML 設定切換）
│   └── config/
│       ├── eip.yml                 公司 A 流程設定（MODULE=EIP）
│       └── eipll.yml               公司 B 流程設定（MODULE=LLEIP）
├── iface-retex-fetcher/            公司 A — RETEX POS 系統
└── iface-xdelivery-fetcher/        公司 A — xdelivery 物流 / Super Landing
```

## 公司與資料來源對應

| | 公司 A | 公司 B (EIP LL) |
|---|---|---|
| EIP | ✓ `.env` | ✓ `.env.ll` |
| RETEX POS | ✓ | — |
| xdelivery | ✓ | — |
| Cosmos ERP | `INSTANCE_A` | `INSTANCE_B` |
| iface-db port | `8100` | `8101` |

## 快速開始

### 前置作業

**1. 建立 Docker 網路（一次性）**

```bash
docker network create iface-net
```

**2. 初始化資料庫（一次性）**

```bash
cd iface-initdb
cp .env.example .env
# 填入 MSSQL 連線資訊
vim .env

# 執行初始化（自動建立 IFACE、IFACE_ERROR 資料表及索引）
docker compose run --rm iface-initdb

# 公司 B（另一個 MSSQL instance）
cp .env .env.ll && vim .env.ll
docker compose --env-file .env.ll run --rm iface-initdb
```

### 啟動 iface-db（公司 A）

```bash
cd iface-db
cp .env.example .env && vim .env
docker compose up -d --build
```

```bash
curl http://localhost:8100/health
# {"status": "ok"}
```

### 啟動 iface-db（公司 B）

```bash
# 複製目錄，調整連線至 INSTANCE_B
cp -r iface-db iface-db-ll
cd iface-db-ll

# .env: 修改 IFACE_SERVER 為 INSTANCE_B
# docker-compose.yml: container_name=iface-db-ll, ports="8101:8000"

docker compose up -d --build
```

### 建立 fetcher image

```bash
# EIP fetcher（公司 A + B 共用同一個 image）
cd iface-eip-fetcher
cp .env.example .env && vim .env          # 公司 A
cp .env.ll.example .env.ll && vim .env.ll # 公司 B
docker compose build

cd ../iface-retex-fetcher && cp .env.example .env && vim .env
docker compose build

cd ../iface-xdelivery-fetcher && cp .env.example .env && vim .env
docker compose build
```

### 設定 crontab

```bash
crontab -e
```

```cron
# 公司 A — EIP
0  7  * * *  /xxx/iface-hub/iface-eip-fetcher/run-job.sh order        >> /var/log/iface-eip-order.log 2>&1
30 7  * * *  /xxx/iface-hub/iface-eip-fetcher/run-job.sh payment       >> /var/log/iface-eip-payment.log 2>&1
0  8  * * *  /xxx/iface-hub/iface-eip-fetcher/run-job.sh pre_products  >> /var/log/iface-eip-pre-products.log 2>&1

# 公司 B — EIP LL
0  7  * * *  /xxx/iface-hub/iface-eip-fetcher/run-job.sh -e .env.ll order       >> /var/log/iface-eipll-order.log 2>&1
30 7  * * *  /xxx/iface-hub/iface-eip-fetcher/run-job.sh -e .env.ll payment      >> /var/log/iface-eipll-payment.log 2>&1
0  8  * * *  /xxx/iface-hub/iface-eip-fetcher/run-job.sh -e .env.ll pre_products >> /var/log/iface-eipll-pre-products.log 2>&1

# 公司 A — RETEX POS
30 6  * * *  /xxx/iface-hub/iface-retex-fetcher/run-job.sh daily >> /var/log/iface-retex.log 2>&1

# 公司 A — xdelivery
0  6  * * *  /xxx/iface-hub/iface-xdelivery-fetcher/run-job.sh order >> /var/log/iface-xdelivery-order.log 2>&1
0  9  * * *  /xxx/iface-hub/iface-xdelivery-fetcher/run-job.sh saas  >> /var/log/iface-xdelivery-saas.log 2>&1
```

## 手動執行 Job

```bash
# EIP — 公司 A
cd iface-eip-fetcher
./run-job.sh order          # 訂單（銷貨、銷退、庫存異動）
./run-job.sh payment        # 請款單
./run-job.sh pre_products   # 品號申請
./run-job.sh inventory      # 庫存異動（補跑用）

# EIP — 公司 B（加 -e .env.ll）
./run-job.sh -e .env.ll order
./run-job.sh -e .env.ll payment
./run-job.sh -e .env.ll pre_products

# RETEX
cd iface-retex-fetcher
./run-job.sh daily          # 前一日全部單據

# xdelivery
cd iface-xdelivery-fetcher
./run-job.sh order          # 退貨（前 3 日）
./run-job.sh saas           # SaaS 服務費 / 簡訊儲值
```

## EIP Fetcher 流程設定

`iface-eip-fetcher` 的 job 流程定義於 `config/` 下的 YAML 檔，不寫死在程式碼中。
新增公司或修改 SP / View，只需編輯 YAML，不需異動 Python 程式碼。

```
iface-eip-fetcher/
├── config/
│   ├── eip.yml      # 公司 A：MODULE=EIP，SP/View 名稱清單
│   └── eipll.yml    # 公司 B：MODULE=LLEIP，SP/View 名稱清單
└── app/
    ├── pipeline.py  # 通用執行引擎（Fetch → SP → Reply → Status Update）
    ├── eip_client.py
    ├── iface_client.py
    └── main.py
```

每個 job 在 YAML 中定義四個步驟：

```yaml
jobs:
  order:
    fetch:      # 呼叫哪些 EIP API、帶什麼參數
    procedures: # 依序執行哪些 SP
    reply:      # 各回傳 View → EIP endpoint 對應
    status_functions: # 更新哪些 function 的狀態（5→6）
```

**新增公司 C 的步驟：**

1. 複製 `config/eip.yml` → `config/eipcc.yml`，修改 `module`、SP 名稱、View 名稱
2. 複製 `.env.example` → `.env.cc`，設定 `EIP_CONFIG=config/eipcc.yml`
3. 執行：`./run-job.sh -e .env.cc order`

## iface-db API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/health` | 服務健康狀態 |
| POST | `/api/v1/iface/transactions/` | 寫入外部 API 資料至 IFACE |
| POST | `/api/v1/iface/status-update/` | 更新 IFACE 資料狀態 |
| POST | `/api/v1/iface/sp/{name}` | 執行 Stored Procedure（白名單） |
| GET | `/api/v1/iface/reply/{view}` | 查詢 reply view（回寫外部 API 用） |
| GET | `/api/v1/iface/query/{view}` | 查詢參考資料 view |
| GET | `/api/v1/iface/named-query/{name}` | 執行具名參數查詢 |

API 文件（Swagger UI）：`http://localhost:8100/docs`

### IFACE STATUS 語義

| 值 | 狀態 | 說明 |
|----|------|------|
| `0` | pending | 資料寫入，等待處理 |
| `5` | processing | SP 執行中 |
| `6` | complete | 匯入完成 |
| `E` | error | 處理失敗，見 ERROR_MESSAGE |

## 環境變數

### iface-initdb

| 變數 | 說明 | 範例 |
|------|------|------|
| `IFACE_SERVER` | MSSQL 伺服器及 instance | `192.168.101.204\INSTANCE_A` |
| `IFACE_USER` | 資料庫帳號 | `mis` |
| `IFACE_PWD` | 資料庫密碼 | |
| `IFACE_DB` | 資料庫名稱 | `IFACE` |

### iface-db

| 變數 | 說明 | 範例 |
|------|------|------|
| `IFACE_SERVER` | MSSQL 伺服器及 instance | `192.168.101.204\INSTANCE_A` |
| `IFACE_USER` | 資料庫帳號 | `mis` |
| `IFACE_PWD` | 資料庫密碼 | |
| `IFACE_DB` | 資料庫名稱 | `IFACE` |
| `DB_POOL_SIZE` | 連線池大小（選用） | `5` |
| `DB_MAX_OVERFLOW` | 最大溢位連線（選用） | `10` |

### iface-eip-fetcher

| 變數 | 說明 | 範例 |
|------|------|------|
| `CONTAINER_NAME` | Docker container 名稱 | `iface-eip-fetcher` |
| `IMAGE_NAME` | Docker image 名稱 | `iface-eip-fetcher` |
| `EIP_CONFIG` | YAML 設定檔路徑 | `config/eip.yml` |
| `DB_API_URL` | iface-db 位址 | `http://iface-db:8000` |
| `EIP_BASE_URL` | EIP API 網址 | `https://api-eip.speeding-rocket.com` |
| `EIP_MODULE` | IFACE 模組代碼 | `EIP` |
| `EIP_ACCESS_KEY` | EIP 存取金鑰 | |

公司 B（`.env.ll`）：`EIP_CONFIG=config/eipll.yml`、`EIP_MODULE=LLEIP`、`DB_API_URL=http://iface-db-ll:8000`

### iface-retex-fetcher

| 變數 | 說明 | 範例 |
|------|------|------|
| `DB_API_URL` | iface-db 位址 | `http://iface-db:8000` |
| `RETEX_BASE_URL` | RETEX POS API 網址 | `http://pos.speeding-rocket.io:82` |
| `RETEX_TOKEN` | API Token（Base64） | |
| `RETEX_API_KEY` | AES 加密金鑰（Base64） | |
| `RETEX_API_IV` | AES IV（Base64） | |
| `RETEX_SALT_KEY` | SHA-512 Salt | |

### iface-xdelivery-fetcher

| 變數 | 說明 | 範例 |
|------|------|------|
| `DB_API_URL` | iface-db 位址 | `http://iface-db:8000` |
| `XDELIVERY_ACCESS_KEY` | xdelivery 存取金鑰 | |
| `XDELIVERY_MERCHANT_ID` | 商家 ID | `1` |
| `XDELIVERY_MERCHANT_NAME` | 商家名稱 | `光速火箭有限公司` |

## 資料流程

### EIP / EIP LL 訂單

```
EIP API → eip_client（分頁抓取）
        → iface_client.iface_import()    寫入 IFACE（STATUS=0）
        → iface_client.run_procedure()   執行 SP（由 YAML 設定）
        → eip_client.reply()             查 reply view → POST EIP /ok.json
        → iface_client.status_update()   STATUS 5→6
```

### RETEX POS 每日排程

```
1. iface_client.query_view("XX_DATASTAMP")   取得最新 DataStamp
2. retex_client.query_docs()                 查詢各單據類型 → 寫入 IFACE
3. retex_client.query_sales()                查詢銷貨 SO → 寫入 IFACE
4. iface_client.run_procedure(XXIF_RETEX_*)  各類型匯入 Cosmos ERP
5. iface_client.named_query("RETEX_CM_GET_ORDERS")  查詢 CM 採購單
   retex_client.doc_update()                回傳 POS ErpDocUpdate
6. iface_client.run_procedure("XX_UPDATE_DATASTAMP") 更新高水位
```

### xdelivery SaaS

```
xdelivery_client.saas()         抓取服務費 / 儲值 → 寫入 IFACE
iface_client.run_procedure()    XXIF_COPTG_SaaS_Import → Cosmos ERP
xdelivery_client.saas_reply()   查 COPTG_SaaS_APPLY_vw → POST /ok.json
```

## 安全設計

### SP 白名單

`iface-db` 只允許執行 `config.ALLOWED_PROCEDURES` 中列出的 stored procedures，
任何不在白名單的名稱將回傳 `403 Forbidden`。

新增 SP 時，在 [iface-db/app/core/config.py](iface-db/app/core/config.py) 的 `ALLOWED_PROCEDURES` 加入名稱。

### View 白名單

Reply / Query 端點同樣限制於 `config.ALLOWED_VIEWS`，防止任意資料表被查詢。

### 認證

各外部 API 的認證金鑰存放於各 fetcher 的 `.env`，不寫入程式碼。

| 外部系統 | 認證方式 |
|----------|----------|
| EIP / EIP LL | HTTP Bearer Token（access_key） |
| RETEX POS | Timestamp + AES-256 加密 + SHA-512 簽章 |
| xdelivery | HTTP Bearer Token（access_key） |
| Super Landing | HTTP Bearer Token（access_key） |

## 錯誤處理

失敗的資料會在 IFACE 資料表的 `ERROR_MESSAGE` 欄位記錄原因，並同步寫入 `IFACE_ERROR` quarantine 資料表。

查詢未解決的失敗記錄：

```sql
SELECT * FROM IFACE_ERROR
WHERE RESOLVED = 0
ORDER BY QUARANTINE_DATE DESC;
```

人工確認處理後標記：

```sql
UPDATE IFACE_ERROR
SET RESOLVED = 1, RESOLVED_DATE = GETDATE(), RESOLVED_BY = 'mis', RESOLVED_NOTE = '已手動補匯'
WHERE ERROR_ID = 123;
```

## 移轉至 Business Central

當某家公司移轉至 BC 雲端 ERP 時：

1. 在 `iface-db` 新增 BC OData 客戶端（參考 `integration-hub` 的 `bc/` 目錄）
2. 在資料庫新增 `company_erp_target` 設定表
3. `iface-db` 依公司代碼路由至 Cosmos ERP SP 或 BC OData
4. Fetcher 容器不需異動

## 相關專案

- `iface/` — 原始 Python crontab 版本（封存，供參考）
- `integration-hub/` — BC 雲端 ERP 整合平台（FastAPI + PostgreSQL）
