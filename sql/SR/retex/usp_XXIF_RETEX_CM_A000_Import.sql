USE IFACE_SR
GO

IF OBJECT_ID ( 'XXIF_RETEX_CM_A000_Import', 'P' ) IS NOT NULL
    DROP PROCEDURE XXIF_RETEX_CM_A000_Import;

GO

CREATE PROCEDURE XXIF_RETEX_CM_A000_Import
AS


/*
	POS 門市訂單轉展店採購單

	v1.1 2023/08/23 IFACE 狀態碼匯入後變更為 "7", 與一般門市訂單作區別
	v1.2 2023/09/27 排除已匯入
	v1.3 2023/10/13 變更 CREATOR 為 API (原 T0031)

	v2.0 2024/02/20 移除 A001, 只留 A000
		因為 A000, A001 訂單有分別處理的需要

	v2.1 2024/06/26 門市對照表 XX_COUNTERS 新增門市狀態資訊 ACTIVE_CODE
		'Y'	營業中門市
		'N'	已失效(門市已停止營業)

	v2.2 新增 A118, 指定光速火箭出貨倉別為 A118 群豐欣業
	v2.3 2025/12/12 加上終止日, 避免誤用

	v4.0 光速展店合併至光速火箭
		CM 門市訂單資料複製到 XX_POS_CM_HIST,
		模擬採購紀錄, 用於驗收入庫後轉倉作業倉庫來源/目的資料

	v4.1 加入 TRY/CATCH, PROCESSED_DATE, IFACE_ERROR 支援
		搭配 cm_query.py 執行：先產生 .xls 後再執行此 SP 記錄 CM 歷史
*/

DECLARE @ErrMsg NVARCHAR(2000)

DECLARE @XX_DOC_HEADERS TABLE (
	DOC_ID		BIGINT,
	DocNo		NVARCHAR(100),
	DocTyNo		NVARCHAR(100),
	DocCla		NVARCHAR(100),
	DocDate		DATE,
	ShopNo		NVARCHAR(100),
	DocRem		NVARCHAR(255),
	DenNo		NVARCHAR(100),
	SignEmpNo	NVARCHAR(100),
	AmtTot		NUMERIC,
	DataStamp	NUMERIC,
	DocDetial	NVARCHAR(MAX)
)

BEGIN TRY

INSERT INTO @XX_DOC_HEADERS (
	DOC_ID,
	DocNo,
	DocTyNo,
	DocCla,
	DocDate,
	ShopNo,
	DocRem,
	DenNo,
	SignEmpNo,
	AmtTot,
	DataStamp,
	DocDetial
)
SELECT
	DOC_ID,
	DocNo,
	DocTyNo,
	DocCla,
	DocDate,
	ShopNo,
	DocRem,
	DenNo,
	SignEmpNo,
	AmtTot,
	DataStamp,
	DocDetial
FROM IFACE
	CROSS APPLY
	OPENJSON (JSON_DOC, '$.DocData') WITH (
		DocNo		NVARCHAR(100)	'$.DocNo',
		DocTyNo		NVARCHAR(100)	'$.DocTyNo',
		DocCla		NVARCHAR(100)	'$.DocCla',
		DocDate		DATE			'$.DocDate',
		ShopNo		NVARCHAR(100)	'$.ShopNo',
		DocRem		NVARCHAR(255)	'$.DocRem',
		DenNo		NVARCHAR(100)	'$.DenNo',
		SignEmpNo	NVARCHAR(100)	'$.SignEmpNo',
		AmtTot		NUMERIC			'$.AmtTot',
		DataStamp	NUMERIC			'$.DataStamp',
		DocDetial	NVARCHAR(MAX)	'$.DocDetial' AS JSON
	) AS h
WHERE 1=1
	AND STATUS = '0'
	AND APP_FUNCTION = N'CM'			-- CM  門市補貨訂單
	AND DenNo IN (N'A000', N'A118')
	AND DocDate >= '2026/01/01 00:00:00'
	AND NOT EXISTS (SELECT 'X' FROM XX_POS_CM_HIST t WHERE t.DocNo = h.DocNo);

INSERT INTO XX_POS_CM_HIST (
	DocNo,
	DocTyNo,
	DocCla,
	DocDate,
	ShopNo,
	DocRem,
	DenNo,
	SignEmpNo,
	AmtTot,
	DataStamp,
	DocDetial
)
SELECT
	DocNo,
	DocTyNo,
	DocCla,
	DocDate,
	ShopNo,
	DocRem,
	DenNo,
	SignEmpNo,
	AmtTot,
	DataStamp,
	DocDetial
FROM @XX_DOC_HEADERS;

UPDATE IFACE
	SET STATUS         = N'5',
	    PROCESSED_DATE = SYSUTCDATETIME()
WHERE DOC_ID IN (SELECT DOC_ID FROM @XX_DOC_HEADERS);

END TRY
BEGIN CATCH

	SET @ErrMsg = LEFT(ERROR_MESSAGE(), 2000);

	UPDATE IFACE
		SET STATUS        = N'E',
		    ERROR_MESSAGE = @ErrMsg,
		    RETRY_COUNT   = RETRY_COUNT + 1
	WHERE DOC_ID IN (SELECT DOC_ID FROM @XX_DOC_HEADERS);

	INSERT INTO IFACE_ERROR (
		ORIGINAL_DOC_ID, BATCH_ID, CREATION_DATE, API, APP_MODULE, APP_FUNCTION,
		QUERY_PARAMS, JSON_DOC, MERCHANT, ERROR_MESSAGE, RETRY_COUNT
	)
	SELECT
		DOC_ID, BATCH_ID, CREATION_DATE, API, APP_MODULE, APP_FUNCTION,
		QUERY_PARAMS, JSON_DOC, MERCHANT, @ErrMsg, RETRY_COUNT
	FROM IFACE
	WHERE DOC_ID IN (SELECT DOC_ID FROM @XX_DOC_HEADERS);

	THROW;

END CATCH
