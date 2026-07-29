from functools import lru_cache
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    IFACE_SERVER: str
    IFACE_USER:   str
    IFACE_PWD:    str
    IFACE_DB:     str = "IFACE"

    # Connection pool
    DB_POOL_SIZE:     int = 5
    DB_MAX_OVERFLOW:  int = 10
    DB_POOL_TIMEOUT:  int = 30
    DB_QUERY_TIMEOUT: int = 360  # pymssql command timeout (seconds); must exceed HTTP _TIMEOUT_LONG

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mssql+pymssql://{self.IFACE_USER}:{self.IFACE_PWD}"
            f"@{self.IFACE_SERVER}/{self.IFACE_DB}"
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ---------------------------------------------------------------
    # SP 白名單：僅允許執行以下 stored procedures
    # 新增 SP 時，在此列表加入名稱
    # ---------------------------------------------------------------
    ALLOWED_PROCEDURES: frozenset[str] = frozenset({
        # EIP
        "XXIF_COPTG_EIP_Import",           # 銷貨（含 return_change, repost, requisit）
        "XXIF_COPTI_EIP_Import",           # 銷退（含 orderReject, orderProblem）
        "XXIF_INVTA_EIP_Import",           # 庫存異動（含 transfers, inventoryChange）
        "XXIF_INVMB_EIP_INCORRECT",        # 品號不一致修正
        "XXIF_INVMB_Import",               # 品號基本資料
        "XXIF_ACPTA_Import",               # 請款單
        # xdelivery
        "XXIF_COPTG_SaaS_Import",          # xdelivery SaaS 費用
        # Currency
        "XXIF_CURRENCY_Rate_Import",       # 即期匯率
        "XXIF_CUSTOMS_Rate_Import",        # 海關三旬匯率
        # RETEX 
        "XXIF_RETEX_SO_Import",            # 銷售訂單
        "XXIF_RETEX_BO_Import",            # 進貨退回
        "XXIF_RETEX_CM_Import",            # 調貨單
        "XXIF_RETEX_CM_A000_Import",       # 調貨單（A000 總倉）
        "XXIF_RETEX_ST_Import",            # 收貨驗收
        "XXIF_RETEX_MO_Import",            # 移倉出
        "XXIF_RETEX_ME_Import",            # 庫存調整
        "XX_UPDATE_DATASTAMP",             # 更新 DataStamp 高水位
    })

    # ---------------------------------------------------------------
    # View 白名單：reply / query 端點允許查詢的 view 名稱
    # ---------------------------------------------------------------
    ALLOWED_VIEWS: frozenset[str] = frozenset({
        # EIP reply views — 訂單
        "COPTG_EIP_ORDER_APPLY_vw",        # 銷貨單回傳
        "COPTG_EIP_SuperLanding_APPLY_vw", # 一頁商店回傳
        "COPTG_EIP_Requisit_APPLY_vw",     # 領料單回傳
        "COPTI_EIP_APPLY_vw",              # 銷退單回傳
        "COPTI_EIP_Reject_APPLY_vw",       # 拒收回傳
        "COPTI_EIP_Problem_APPLY_vw",      # 遺失回傳
        # EIP reply views — 庫存
        "INVTA_Transfer_EIP_APPLY_vw",     # 移倉單回傳
        "INVTA_Change_EIP_APPLY_vw",       # 庫存異動回傳
        # EIP reply views — 請款
        "ACPTA_EIP_APPLY_vw",              # 請款單回傳
        # 品號申請回傳（INVMB_EIP_APPLY_vw）已轉由 integration_hub 負責，不再由此處呼叫
        # RETEX query views
        "XX_DATASTAMP",                    # RETEX DataStamp 高水位查詢
        # xdelivery reply views
        "COPTG_SaaS_APPLY_vw",             # SaaS 服務費 / 簡訊儲值回傳
    })


    # ---------------------------------------------------------------
    # SP Query 白名單：執行並回傳結果集的 SP（非純寫入用途）
    # ---------------------------------------------------------------
    ALLOWED_SP_QUERIES: dict = {
        "XXIF_RETEX_CM_AX_QUERY": {"database": "IFACE_SR"},
    }

    # ---------------------------------------------------------------
    # Named queries：需要帶參數查詢 MSSQL 且非 View 的情境
    # 主要用於 RETEX CM 採購單回傳 POS
    # ---------------------------------------------------------------
    NAMED_QUERIES: dict = {
        "RETEX_CM_GET_ORDERS": {
            "database": "SR",
            "sql": """
                SELECT (
                    SELECT
                        TC079                            ErpDocNo,
                        N'V2S'                           ErpDocTyNo,
                        CONVERT(VARCHAR, CONVERT(DATETIME, TC003), 111) ErpDocDate,
                        TC009   DocNo,
                        TC080   DenNo,
                        TC040   ShopNo,
                        N'ED'   DocStatus,
                        TC060   DocRem,
                        (
                            SELECT
                                CONVERT(NUMERIC, TD003) DocOrd,
                                RTRIM(TD004)            GdsNo,
                                CONVERT(NUMERIC, TD008) PckQty
                            FROM PURTD
                            WHERE TD001=TC001 AND TD002=TC002
                            FOR JSON PATH
                        ) AS DocDetail
                    FROM PURTC
                    WHERE TC039 = N'RETEX_POS'
                      AND CREATE_DATE = :create_date
                      AND TC080 NOT IN (N'A000', N'A001', N'A118', N'A119')
                    FOR JSON PATH, ROOT('DocData')
                ) AS jsonResult
            """,
        },
        "RETEX_CM_A000_GET_ORDERS": {
            "database": "IFACE_SR",
            "sql": """
                WITH XX_ORDER AS (
                    SELECT DocNo, DocDate, ShopNo, DocRem, DenNo, DocDetial
                    FROM IFACE
                    CROSS APPLY OPENJSON(JSON_DOC, '$.DocData') WITH (
                        DocNo      NVARCHAR(100) '$.DocNo',
                        DocDate    DATE          '$.DocDate',
                        ShopNo     NVARCHAR(100) '$.ShopNo',
                        DocRem     NVARCHAR(255) '$.DocRem',
                        DenNo      NVARCHAR(100) '$.DenNo',
                        DocDetial  NVARCHAR(MAX) '$.DocDetial' AS JSON
                    ) AS h
                    WHERE STATUS = '5'
                      AND APP_FUNCTION = N'CM'
                      AND DenNo IN (N'A000', N'A118', N'A119')
                ),
                XX_LINES AS (
                    SELECT h.DocNo, DocOrd, GdsNo, PckQty
                    FROM XX_ORDER h
                    CROSS APPLY (
                        SELECT * FROM OPENJSON(h.DocDetial) WITH (
                            DocOrd NUMERIC         '$.DocOrd',
                            GdsNo  NVARCHAR(100)   '$.GdsNo',
                            PckQty NUMERIC         '$.PckQty'
                        )
                    ) AS l
                    WHERE l.PckQty != 0
                )
                SELECT (
                    SELECT
                        DocNo   ErpDocNo,
                        N'V2S'  ErpDocTyNo,
                        DocDate ErpDocDate,
                        DocNo   DocNo,
                        N'M01001' DenNo,
                        ShopNo  ShopNo,
                        N'ED'   DocStatus,
                        DocRem,
                        (
                            SELECT DocOrd, GdsNo, PckQty
                            FROM XX_LINES l WHERE l.DocNo = h.DocNo
                            FOR JSON PATH
                        ) AS DocDetail
                    FROM XX_ORDER h
                    FOR JSON PATH, ROOT('DocData')
                ) AS jsonResult
            """,
        },
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
