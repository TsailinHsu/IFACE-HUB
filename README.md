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
currencyapi.com  ──HTTP──▶       sp-query/{name}
海關匯率 API     ──HTTP──▶       reply/{view}
                                 sp-query/{name}
                                 reply/{view}
                                 query/{view}
                                 named-query/{name}
```

各資料來源為獨立的 fetcher 容器，透過 HTTP 呼叫 `iface-db` API，不直接連接資料庫。

## 專案結構

```
iface-hub/
├── docker-compose.yml              Hub-level compose（主要部署入口）
├── run-job.sh                      Hub-level job runner
├── .env.a.example                  公司 A 完整環境設定範本
├── .env.b.example                  公司 B 完整環境設定範本
│
├── sql/                            MSSQL schema 參考文件
│   ├── 01-create-tables.sql        IFACE + IFACE_ERROR 資料表定義
│   └── 02-create-indexes.sql       效能索引
│
├── iface-initdb/                   資料庫初始化（init container，首次部署執行）
│   └── initdb/
│       ├── 01-create-tables.sql    建表（IF NOT EXISTS，冪等）
│       └── 02-create-indexes.sql   建索引（IF NOT EXISTS，冪等）
│
├── iface-db/                       核心 API 服務（長期運行）
├── iface-eip-fetcher/              EIP 電商平台（公司 A / B 共用，YAML 設定切換）
│   └── config/
│       ├── eip.yml                 公司 A 流程設定（MODULE=EIP）
│       └── eipll.yml               公司 B 流程設定（MODULE=LLEIP）
├── iface-retex-fetcher/            RETEX POS 系統（daily / cm_ax_import / so_import / so_query / doc_query）
├── iface-xdelivery-fetcher/        xdelivery 物流 / Super Landing
├── iface-currency-fetcher/         匯率資料（currency_api / customs_rate）
└── iface-client/                   共用 iface-db HTTP client（Python package）
```

## 多公司部署模型

**一組 `.env` = 一套完整公司環境。** 透過 `COMPOSE_PROJECT_NAME`，Docker Compose 自動建立隔離的 project 與 network，各公司容器互不干擾。

```
.env.a  →  COMPOSE_PROJECT_NAME=iface-a  →  network: iface-a_default
.env.b  →  COMPOSE_PROJECT_NAME=iface-b  →  network: iface-b_default
```

- **同一 project 內**，fetcher 永遠以 `http://iface-db:8000` 呼叫 iface-db（無需設定 `DB_API_URL`）
- **跨 project**，network 完全隔離，無需手動建立 Docker network
- **只有 `IFACE_DB_PORT`** 需要在各公司間不重複（對外 host port，供 Swagger UI / 人工查詢使用）
- **新增公司** = 新增 `.env.x`，zero code change

```
公司 A (.env.a)              公司 B (.env.b)
─────────────────────         ─────────────────────
iface-a-db       port:8100   iface-b-db       port:8101
iface-a-eip-fetcher          iface-b-eip-fetcher
iface-a-retex-fetcher        （公司 B 不使用）
iface-a-xdelivery-fetcher    （公司 B 不使用）
```

## 公司與資料來源對應

| | 公司 A | 公司 B (EIP LL) |
|---|---|---|
| EIP | ✓ `config/eip.yml` | ✓ `config/eipll.yml` |
| RETEX POS | ✓ | — |
| xdelivery | ✓ | — |
| currency（匯率） | ✓ | — |
| Cosmos ERP | `INSTANCE_A` | `INSTANCE_B` |
| iface-db port | `8100` | `8101` |

## 快速開始

### 1. 準備環境設定

```bash
cp .env.a.example .env.a && vim .env.a   # 公司 A
cp .env.b.example .env.b && vim .env.b   # 公司 B
```

最少需填寫：`IFACE_SERVER`、`IFACE_USER`、`IFACE_PWD`、各外部 API 金鑰。

### 2. 初始化資料庫（首次部署，各公司一次）

```bash
./run-job.sh -e .env.a init   # 建立 IFACE、IFACE_ERROR 資料表及索引（公司 A）
./run-job.sh -e .env.b init   # 公司 B
```

完成後 `iface-initdb` image 會自動移除（一次性任務，不需保留）。

### 3. 啟動 iface-db

```bash
# 公司 A
docker compose --env-file .env.a up -d --build

# 公司 B
docker compose --env-file .env.b up -d --build
```

`iface-db` 預設不對外綁定 host port，fetcher 透過 Docker network 內部存取。
如需 Swagger UI 或外部 API 存取（開發用途），在 `.env.x` 設定 `IFACE_DB_PORT` 並疊加 override：

```bash
# 在 .env.a 取消 IFACE_DB_PORT=8100 的註解，然後：
docker compose --env-file .env.a -f docker-compose.yml -f docker-compose.ports.yml up -d

curl http://localhost:8100/health   # → {"status": "ok"}
```

### 4. 建立 fetcher image（一次性）

```bash
docker compose --env-file .env.a build
```

### 5. 設定 crontab

```bash
crontab -e
```

```cron
# 公司 A — EIP
0  7  * * *  /xxx/iface-hub/run-job.sh -e .env.a eip order        >> /var/log/iface-a-eip-order.log 2>&1
30 7  * * *  /xxx/iface-hub/run-job.sh -e .env.a eip payment       >> /var/log/iface-a-eip-payment.log 2>&1
0  8  * * *  /xxx/iface-hub/run-job.sh -e .env.a eip pre_products       >> /var/log/iface-a-eip-pre-products.log 2>&1
30 8  * * *  /xxx/iface-hub/run-job.sh -e .env.a eip product_incorrects >> /var/log/iface-a-eip-product-incorrects.log 2>&1

# 公司 A — RETEX POS
30 6  * * *  /xxx/iface-hub/run-job.sh -e .env.a retex daily       >> /var/log/iface-a-retex.log 2>&1
0  9  * * *  /xxx/iface-hub/run-job.sh -e .env.a retex cm_ax_import $(date -d "yesterday" +\%Y/\%m/\%d) $(date -d "yesterday" +\%Y/\%m/\%d)  >> /var/log/iface-a-retex-cm.log 2>&1

# 公司 A — xdelivery
0  6  * * *  /xxx/iface-hub/run-job.sh -e .env.a xdelivery order         >> /var/log/iface-a-xdelivery-order.log 2>&1
0  9  * * *  /xxx/iface-hub/run-job.sh -e .env.a xdelivery saas          >> /var/log/iface-a-xdelivery-saas.log 2>&1

# 公司 A — currency 匯率
0  8  * * 1  /xxx/iface-hub/run-job.sh -e .env.a currency currency_api   >> /var/log/iface-a-currency-api.log 2>&1
0  8  1,11,21 * *  /xxx/iface-hub/run-job.sh -e .env.a currency customs_rate  >> /var/log/iface-a-customs-rate.log 2>&1

# 公司 B — EIP LL
0  7  * * *  /xxx/iface-hub/run-job.sh -e .env.b eip order         >> /var/log/iface-b-eip-order.log 2>&1
30 7  * * *  /xxx/iface-hub/run-job.sh -e .env.b eip payment        >> /var/log/iface-b-eip-payment.log 2>&1
0  8  * * *  /xxx/iface-hub/run-job.sh -e .env.b eip pre_products   >> /var/log/iface-b-eip-pre-products.log 2>&1
```

## 程式異動後更新部署

### iface-db 或 iface-client 有異動

這兩個是所有 fetcher 共用的核心套件，異動後需重建 **所有** 相關 image：

```bash
# 重建並重啟 iface-db
docker compose --env-file .env.a up -d --build iface-db

# 重建所有 fetcher image（下次執行 job 時會使用新 image）
docker compose --env-file .env.a build
```

> `iface-client` 在 build time 以 `pip install ./iface-client` 安裝進各 fetcher image，
> 因此修改 `iface-client` 後必須重建 fetcher image，否則仍使用舊版。

### 只有單一 fetcher 有異動

```bash
# 只重建指定的 fetcher（例如 iface-eip-fetcher）
docker compose --env-file .env.a build iface-eip-fetcher
```

下次執行對應 job 時，Docker Compose 會自動使用新建的 image。

### 確認 image 是否已更新

```bash
# 查看各 service 使用的 image 建立時間
docker compose --env-file .env.a images
```

### 常見異動對應的重建範圍

| 異動檔案 | 需重建的 image |
|----------|---------------|
| `iface-db/app/**` | `iface-db` |
| `iface-client/iface_client.py` | 所有 fetcher（`build` 不指定 service） |
| `iface-eip-fetcher/app/**` | `iface-eip-fetcher` |
| `iface-retex-fetcher/app/**` | `iface-retex-fetcher` |
| `iface-xdelivery-fetcher/app/**` | `iface-xdelivery-fetcher` |
| `iface-currency-fetcher/app/**` | `iface-currency-fetcher` |
| `iface-eip-fetcher/config/*.yml` | `iface-eip-fetcher`（YAML 是 COPY 進 image，非 volume-mount） |

---

## 手動執行 Job

```bash
# 語法：./run-job.sh -e <env_file> <fetcher> <job>

# 公司 A
./run-job.sh -e .env.a eip order          # EIP 訂單
./run-job.sh -e .env.a eip payment        # EIP 請款單
./run-job.sh -e .env.a eip pre_products        # EIP 品號申請
./run-job.sh -e .env.a eip product_incorrects  # EIP 料號基本資料不一致修正
./run-job.sh -e .env.a eip inventoryChange     # EIP 庫存異動（補跑用）
./run-job.sh -e .env.a eip inventoryTransfer  # EIP 庫存移轉（補跑用）
./run-job.sh -e .env.a retex daily        # RETEX POS 前一日全部單據
./run-job.sh -e .env.a retex cm_ax_import 2026/04/01 2026/04/14   # RETEX CM 針對 A000/A118 通知單匯出及回傳 POS（指定日期區間）
./run-job.sh -e .env.a retex doc_query ST 2026/04/01 2026/04/14   # RETEX ST/BO/MO/ME 補跑查詢並寫入 IFACE（不執行 SP）
./run-job.sh -e .env.a retex so_query  2025/01/01 2025/01/31  # RETEX SO 銷貨補跑查詢並寫入 IFACE（不執行 SP）
./run-job.sh -e .env.a retex so_import 2025/01/01 2025/01/31  # RETEX SO 銷貨補跑（指定日期區間）
./run-job.sh -e .env.a xdelivery order    # xdelivery 退貨（前 1 日）
./run-job.sh -e .env.a xdelivery saas     # xdelivery SaaS 服務費
./run-job.sh -e .env.a currency currency_api   # 對美金匯率（currencyapi.com）
./run-job.sh -e .env.a currency customs_rate   # 海關三旬匯率

# 公司 B（換 -e .env.b，其餘相同）
./run-job.sh -e .env.b eip order
./run-job.sh -e .env.b eip payment
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
    fetch:            # 呼叫哪些 EIP API、帶什麼參數
    procedures:       # 依序執行哪些 SP
    reply:            # 各回傳 View → EIP endpoint 對應
    status_functions: # 更新哪些 function 的狀態（5→6）
```

**新增公司 C（使用 EIP）：**

1. 複製 `iface-eip-fetcher/config/eip.yml` → `config/eipcc.yml`，修改 `module`、SP 名稱、View 名稱
2. 複製 `.env.a.example` → `.env.c`，設定 `EIP_CONFIG=config/eipcc.yml`、`IFACE_DB_PORT=8102`
3. 執行：`./run-job.sh -e .env.c init` + `docker compose --env-file .env.c up -d`

## iface-db API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/health` | 服務健康狀態 |
| POST | `/api/v1/iface/transactions/` | 寫入外部 API 資料至 IFACE |
| POST | `/api/v1/iface/status-update/` | 更新 IFACE 資料狀態 |
| POST | `/api/v1/iface/sp/{name}` | 執行 Stored Procedure（白名單，不回傳結果集） |
| POST | `/api/v1/iface/sp-query/{name}` | 執行 SP 並回傳結果集（`ALLOWED_SP_QUERIES` 白名單） |
| GET | `/api/v1/iface/reply/{view}` | 查詢 reply view（回寫外部 API 用） |
| GET | `/api/v1/iface/query/{view}` | 查詢參考資料 view |
| GET | `/api/v1/iface/named-query/{name}` | 執行具名參數查詢 |

API 文件（Swagger UI）：`http://localhost:${IFACE_DB_PORT}/docs`

### IFACE STATUS 語義

| 值 | 狀態 | 說明 |
|----|------|------|
| `0` | pending | 資料寫入，等待 SP 處理 |
| `5` | imported | SP 執行完成，ERP 資料已匯入；等待回傳確認（reply） |
| `6` | complete | 回傳完成，整筆交易結束；或無資料需匯入（直接標記，不經 SP） |
| `E` | error | 處理失敗，見 `ERROR_MESSAGE`；同步寫入 `IFACE_ERROR` |

完整生命週期：`0 → 5（SP 匯入）→ 6（reply 確認）`，失敗則轉為 `E`。

## 環境變數（`.env.x` 完整清單）

| 變數 | 說明 | 範例 |
|------|------|------|
| `COMPOSE_PROJECT_NAME` | Compose project 名稱（決定 network 與 container 命名空間） | `iface-a` |
| `IFACE_SERVER` | MSSQL 伺服器及 instance | `192.168.101.204\INSTANCE_A` |
| `IFACE_USER` | 資料庫帳號 | `mis` |
| `IFACE_PWD` | 資料庫密碼 | |
| `IFACE_DB` | 資料庫名稱 | `IFACE` |
| `EIP_CONFIG` | EIP YAML 設定檔路徑 | `config/eip.yml` |
| `EIP_BASE_URL` | EIP API 網址 | `https://api-eip.speeding-rocket.com` |
| `EIP_MODULE` | IFACE 模組代碼 | `EIP` |
| `EIP_ACCESS_KEY` | EIP 存取金鑰 | |
| `RETEX_BASE_URL` | RETEX POS API 網址 | `http://pos.speeding-rocket.io:82` |
| `RETEX_TOKEN` | API Token（Base64） | |
| `RETEX_API_KEY` | AES 加密金鑰（Base64） | |
| `RETEX_API_IV` | AES IV（Base64） | |
| `RETEX_SALT_KEY` | SHA-512 Salt | |
| `XDELIVERY_ACCESS_KEY` | xdelivery 存取金鑰 | |
| `XDELIVERY_MERCHANT_ID` | 商家 ID | `1` |
| `XDELIVERY_MERCHANT_NAME` | 商家名稱 | `光速火箭有限公司` |
| `CM_QUERY_OUTPUT_DIR` | RETEX CM XLS 輸出目錄（Host 路徑，掛載至 container `/output`） | `./output/retex_CM_xls` |
| `CURRENCY_API_KEY` | currencyapi.com API 金鑰 | |

不使用的 fetcher，對應變數留空即可。

`IFACE_DB_PORT`（選用）：僅在需要對外開放 iface-db 時設定，搭配 `docker-compose.ports.yml` 使用。部署在同一 Host 的多公司，各自設定不重複的 port。

## 資料流程

### EIP / EIP LL 訂單

```
EIP API → eip_client（分頁抓取）
        → 有資料：iface_client.iface_import()    寫入 IFACE（STATUS=0）
                  iface_client.run_procedure()   執行 SP（由 YAML 設定）
                  eip_client.reply()             查 reply view → POST EIP /ok.json
                  iface_client.status_update()   STATUS 5→6
        → 無資料：iface_client.iface_import()    寫入 IFACE（STATUS=6，直接完成）
```

### RETEX POS 每日排程（`daily`）

```
1. iface_client.query_view("XX_DATASTAMP")   取得最新 DataStamp
2. retex_client.query_docs()                 查詢各單據類型
     → ResultNo=00：寫入 IFACE（STATUS=0）
     → 無資料：    寫入 IFACE（STATUS=6，直接完成）
3. retex_client.query_sales()                查詢銷貨 SO（同上）
4. iface_client.run_procedure(XXIF_RETEX_*)  各類型匯入 Cosmos ERP
5. iface_client.named_query("RETEX_CM_GET_ORDERS")  查詢 CM 採購單
   retex_client.doc_update()                回傳 POS ErpDocUpdate
6. iface_client.run_procedure("XX_UPDATE_DATASTAMP") 紀錄最新 DataStamp
```

### RETEX SO 銷貨補跑查詢（`so_query`）

指定日期區間查詢 SO 並寫入 IFACE，**不執行匯入 SP**。適用於需要先將資料寫入 IFACE、由人工確認後再手動執行 SP 的情境。

```
retex_client.query_sales(StDate, EdDate)     查詢指定區間 SO
  → ResultNo=00：寫入 IFACE（STATUS=0）
  → 無資料：    寫入 IFACE（STATUS=6，直接完成）
  ※ 不呼叫 XXIF_RETEX_SO_Import
```

用法：

```bash
./run-job.sh -e .env.a retex so_query <start_date> <end_date>
# 日期格式 YYYY/MM/DD
./run-job.sh -e .env.a retex so_query 2025/01/01 2025/01/31
```

### RETEX SO 銷貨補跑（`so_import`）

指定日期區間手動補跑銷貨資料並立即執行匯入 SP，適用於每日排程失敗或需要重跑歷史資料的情境。

```
retex_client.query_sales(StDate, EdDate)     查詢指定區間 SO
  → ResultNo=00：寫入 IFACE（STATUS=0）
  → 無資料：    寫入 IFACE（STATUS=6，直接完成）
iface_client.run_procedure("XXIF_RETEX_SO_Import")  匯入 Cosmos ERP
```

用法：

```bash
./run-job.sh -e .env.a retex so_import <start_date> <end_date>
# 日期格式 YYYY/MM/DD
./run-job.sh -e .env.a retex so_import 2025/01/01 2025/01/31
```

### RETEX 單據補跑查詢（`doc_query`）

指定單據類型（ST/BO/MO/ME）與日期區間，直接查詢並寫入 IFACE，**不執行任何匯入 SP**。
適用於需要補跑資料、但由人工確認後再手動執行對應 SP 的情境。與 `daily` 的差異在於不傳 DataStamp，以 StDate/EdDate 為唯一過濾條件。

```
retex_client.query_docs(DocTyNo, StDate, EdDate)   # 不傳 DataStamp
  → ResultNo=00：寫入 IFACE（STATUS=0）
  → 無資料：    寫入 IFACE（STATUS=6，直接完成）
  ※ 不呼叫任何匯入 SP
```

用法：

```bash
./run-job.sh -e .env.a retex doc_query <DocTyNo> <start_date> <end_date>
# DocTyNo：ST | BO | MO | ME
# 日期格式：YYYY/MM/DD
./run-job.sh -e .env.a retex doc_query ST 2026/04/01 2026/04/14
./run-job.sh -e .env.a retex doc_query BO 2026/04/01 2026/04/14
```

### RETEX CM 通知單匯出（`cm_ax_import`）

此類 CM 單為通知倉庫出貨的通知單（非一般補貨採購），不走 `XXIF_RETEX_CM_Import` 產生採購單，而是直接呼叫 `XXIF_RETEX_CM_AX_QUERY` 輸出 `.xls` 通知倉庫。
完成後執行 `XXIF_RETEX_CM_A000_Import` 將 A000/A118 單據寫入歷史表，供後續 ST 驗收匯入時查詢倉庫來源。

> **未來規劃**：視 WMS 系統建置進度，XLS 輸出將改為直接呼叫 WMS API 傳送通知單，毋需人工轉檔。

```
retex_client.query_docs(DocTyNo="CM", DataStamp=0, StDate, EdDate)
  → ResultNo=00：寫入 IFACE（STATUS=0）
  → 無資料：    寫入 IFACE（STATUS=6，直接完成）
  ※ 不呼叫 XXIF_RETEX_CM_Import（非採購單流程）

for (DenNo, ShopNo) in task_list:
    iface_client.sp_query("XXIF_RETEX_CM_AX_QUERY", {ShopNo, DenNo})
      → 有資料：寫出 YYYYMMDD_DenNo_ShopNo.xls 至 CM_QUERY_OUTPUT_DIR（預設 /output）
      → 無資料：略過

iface_client.run_procedure("XXIF_RETEX_CM_A000_Import")
  → 將 A000/A118 CM 單據記錄至 XX_POS_CM_HIST（STATUS 0→5）
  → 供 XXIF_RETEX_ST_Import 處理進貨驗收時查詢倉庫來源
```

用法：

```bash
./run-job.sh -e .env.a retex cm_ax_import <start_date> <end_date>
# 日期格式 YYYY/MM/DD
./run-job.sh -e .env.a retex cm_ax_import 2026/04/01 2026/04/14
```

輸出目錄透過 volume mount 寫到 Host，不保留在 container 內：

```yaml
# docker-compose.yml
volumes:
  - ${CM_QUERY_OUTPUT_DIR:-./output/retex_CM_xls}:/output
```

### EIP 料號基本資料不一致修正（`product_incorrects`）

```
EIP API /products/incorrects.json → eip_client（分頁抓取）
        → 有資料：iface_client.iface_import()    寫入 IFACE（STATUS=0，APP_FUNCTION=INVINC）
                  iface_client.run_procedure()   XXIF_INVMB_EIP_INCORRECT
                                                 → 依 EIP 回傳的 manual_* 欄位修正 INVMB
                  iface_client.status_update()   STATUS 5→6（無 reply 回傳步驟）
        → 無資料：iface_client.iface_import()    寫入 IFACE（STATUS=6，直接完成）
```

### currency 匯率

```
# currency_api — 對美金匯率（currencyapi.com）
GET https://api.currencyapi.com/v3/latest
  → iface_client.iface_import()       寫入 IFACE（MODULE=currencyAPI, FUNCTION=RATE）
  → iface_client.run_procedure()      XXIF_CURRENCY_Rate_Import → XX_TO_USD_RATE

# customs_rate — 海關三旬匯率（portal.sw.nat.gov.tw）
GET https://portal.sw.nat.gov.tw/.../CURRENT_JSON
  → iface_client.iface_import()       寫入 IFACE（MODULE=CUSTOMS, FUNCTION=RATE）
  → iface_client.run_procedure()      XXIF_CUSTOMS_Rate_Import → XX_CUSTOMS_RATE
```

### xdelivery SaaS

```
xdelivery_client.saas()         抓取服務費 / 儲值
  → 有資料：寫入 IFACE（STATUS=0）
  → 無資料：寫入 IFACE（STATUS=6，直接完成）
iface_client.run_procedure()    XXIF_COPTG_SaaS_Import → Cosmos ERP
xdelivery_client.saas_reply()   查 COPTG_SaaS_APPLY_vw → POST /ok.json
```

## 安全設計

### SP 白名單

`iface-db` 只允許執行 `config.ALLOWED_PROCEDURES` 中列出的 stored procedures，
任何不在白名單的名稱將回傳 `403 Forbidden`。

新增 SP 時，在 [iface-db/app/core/config.py](iface-db/app/core/config.py) 的 `ALLOWED_PROCEDURES` 加入名稱。

### SP Query 白名單

`sp-query` 端點（回傳結果集）使用獨立的 `ALLOWED_SP_QUERIES` 白名單，
每筆設定包含 SP 名稱與目標資料庫：

```python
ALLOWED_SP_QUERIES: dict = {
    "XXIF_RETEX_CM_AX_QUERY": {"database": "IFACE_SR"},
}
```

### View 白名單

Reply / Query 端點同樣限制於 `config.ALLOWED_VIEWS`，防止任意資料表被查詢。

### 認證

各外部 API 的認證金鑰存放於 `.env.x`，不寫入程式碼。

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

## 新增 Fetcher 模板

每個 fetcher 封裝一個外部系統的資料抓取邏輯，結構固定，可依模板快速建立。

### Fetcher 職責

```
外部 API → xxx_client.py（抓取資料）
         → 有資料：iface_client.iface_import()   寫入 IFACE（STATUS=0）
                   iface_client.run_procedure()  執行 SP，匯入 Cosmos ERP
                   xxx_client reply（選用）       查 reply view，回寫外部系統
                   iface_client.status_update()  STATUS 5→6
         → 無資料：iface_client.iface_import()   寫入 IFACE（STATUS=6，直接完成）
```

fetcher **不直接連接資料庫**，所有 DB 操作透過 `iface-db` HTTP API。
`iface_client` 已封裝為共用 package，直接 `from iface_client import ...` 使用。

### 目錄結構

```
iface-xxx-fetcher/
├── Dockerfile
├── requirements.txt          # 不含 requests（由 iface-client 管理）
├── app/
│   ├── main.py               # JOBS dict + argv dispatch
│   ├── xxx_client.py         # 外部 API 呼叫邏輯
│   └── job_a.py              # 各 job 的 run() 函式
└── .env.example
```

### 各檔案模板

**`app/main.py`**

```python
"""
iface-xxx-fetcher 入口
用法：python app/main.py <job>
"""
import sys
import job_a
import job_b

JOBS = {
    "job_a": job_a.run,
    "job_b": job_b.run,
}

def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in JOBS:
        print(f"用法: python app/main.py [{' | '.join(JOBS)}]")
        sys.exit(1)
    job_name = sys.argv[1]
    print(f"--- xxx fetcher: {job_name} ---")
    JOBS[job_name]()
    print(f"--- xxx fetcher: {job_name} 完成 ---")

if __name__ == "__main__":
    main()
```

**`app/xxx_client.py`**

```python
"""XXX API 客戶端"""
import os
import requests
from iface_client import iface_import, get_reply

_BASE_URL   = os.getenv("XXX_BASE_URL", "")
_ACCESS_KEY = os.getenv("XXX_ACCESS_KEY", "")
_MODULE     = os.getenv("XXX_MODULE", "XXX")   # IFACE.APP_MODULE 值


def fetch_something(begin_date: str, end_date: str) -> None:
    """抓取資料並寫入 IFACE，無資料時以 STATUS='6' 標記已完成。"""
    url  = f"{_BASE_URL}/something.json"
    resp = requests.get(url, params={"access_key": _ACCESS_KEY,
                                     "begin_date": begin_date,
                                     "end_date":   end_date}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("data"):
        iface_import(url, data, {"begin_date": begin_date}, _MODULE, "something")
    else:
        iface_import(url, data, {"begin_date": begin_date}, _MODULE, "something", initial_status="6")


def reply_something() -> None:
    """查 reply view，回寫外部系統。"""
    items = get_reply("SOMETHING_APPLY_vw")
    for item in items:
        url = f"{_BASE_URL}/something/{item['ID']}/ok.json"
        requests.post(url, params={"access_key": _ACCESS_KEY,
                                   "erp_ref_id": item["RefId"]}, timeout=30)
```

**`app/job_a.py`**

```python
"""Job A — 每日主排程"""
from datetime import datetime, timedelta
import xxx_client
from iface_client import run_procedure, status_update

def run() -> None:
    begin_date = datetime.strftime(datetime.now() - timedelta(1), "%Y/%m/%d")
    end_date   = begin_date

    # 1. 抓取外部資料，寫入 IFACE
    xxx_client.fetch_something(begin_date, end_date)

    # 2. 執行 SP，匯入 Cosmos ERP
    run_procedure("XXIF_XXX_Import")

    # 3. 回寫外部系統（若有 reply）
    xxx_client.reply_something()

    # 4. 更新狀態
    status_update("XXX", "something", "5", "6")
```

**`Dockerfile`**（build context = hub root）

```dockerfile
FROM python:3.14.3-slim-trixie

WORKDIR /app

COPY iface-client/ ./iface-client/
RUN pip install --no-cache-dir ./iface-client

COPY iface-xxx-fetcher/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY iface-xxx-fetcher/app/ ./app/
```

**`requirements.txt`**

```
python-dotenv==1.2.1
# 加入外部 API 所需的套件（requests 已由 iface-client 管理，不需重複列出）
```

### 加入 docker-compose.yml

在 hub-level `docker-compose.yml` 新增 service：

```yaml
iface-xxx-fetcher:
  build:
    context: .
    dockerfile: iface-xxx-fetcher/Dockerfile
  container_name: ${COMPOSE_PROJECT_NAME}-xxx-fetcher
  environment:
    DB_API_URL:     http://iface-db:8000
    XXX_BASE_URL:   ${XXX_BASE_URL}
    XXX_MODULE:     ${XXX_MODULE:-XXX}
    XXX_ACCESS_KEY: ${XXX_ACCESS_KEY}
  restart: "no"
  depends_on:
    iface-db:
      condition: service_healthy
  profiles: [xxx]
```

### 加入 .env.x

```bash
# ── XXX 外部系統 ──────────────────────────────────────────────
XXX_BASE_URL=https://api.xxx.example.com
XXX_MODULE=XXX
XXX_ACCESS_KEY=your_access_key
```

### 加入 run-job.sh 的 crontab

```cron
0 8 * * *  /xxx/iface-hub/run-job.sh -e .env.a xxx job_a >> /var/log/iface-a-xxx-job_a.log 2>&1
```

### iface-db SP 白名單

新的 SP 需加入 `iface-db` 白名單才能被呼叫：

```python
# iface-db/app/core/config.py → ALLOWED_PROCEDURES
"XXIF_XXX_Import",
```

reply view 同樣需加入 `ALLOWED_VIEWS`：

```python
# iface-db/app/core/config.py → ALLOWED_VIEWS
"SOMETHING_APPLY_vw",
```

---

## 相關專案

- `iface/` — 原始 Python crontab 版本（封存，供參考）
- `integration-hub/` — BC 雲端 ERP 整合平台（FastAPI + PostgreSQL）
