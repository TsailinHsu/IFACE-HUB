USE IFACE_SR;
GO

IF OBJECT_ID ( 'XXIF_RETEX_CM_AX_QUERY', 'P' ) IS NOT NULL   
    DROP PROCEDURE XXIF_RETEX_CM_AX_QUERY;  

GO  

CREATE PROCEDURE XXIF_RETEX_CM_AX_QUERY  
(
	@ShopNo	NVARCHAR(100) = NULL,
	@DenNo	NVARCHAR(100) = NULL
)
AS

DECLARE @XX_DOC_OUTPUT TABLE (
	DenNo			NVARCHAR(100),
	ShopNo			NVARCHAR(100),
	DocNo			NVARCHAR(100),
	DocDate			DATE,
	ME002			NVARCHAR(100),
	SignEmpNo		NVARCHAR(100),
	DocOrd			NUMERIC,
	TITLE			NVARCHAR(100),
	CODE			NVARCHAR(100),
	MB013			NVARCHAR(100),
	MB001			NVARCHAR(100),
	PckQty			NUMERIC
);

SET NOCOUNT ON;

WITH XX_DOC_HEADERS AS (
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
			DocNo			NVARCHAR(100)	'$.DocNo',
			DocTyNo			NVARCHAR(100)	'$.DocTyNo',
			DocCla			NVARCHAR(100)	'$.DocCla',
			DocDate			DATE			'$.DocDate',
			ShopNo			NVARCHAR(100)	'$.ShopNo',
			DocRem			NVARCHAR(255)	'$.DocRem',
			DenNo			NVARCHAR(100)	'$.DenNo',
			SignEmpNo		NVARCHAR(100)	'$.SignEmpNo',
			AmtTot			NUMERIC			'$.AmtTot',
			DataStamp		NUMERIC			'$.DataStamp',
			DocDetial		NVARCHAR(MAX)	'$.DocDetial' AS JSON
		) AS h
	WHERE 1=1 
		AND STATUS = '0'
		AND APP_FUNCTION = N'CM' -- 門市補貨訂單
)

INSERT INTO @XX_DOC_OUTPUT (
	DenNo,
	ShopNo,
	DocNo,
	DocDate,
	ME002,
	SignEmpNo,
	DocOrd,
	TITLE,
	CODE,
	MB013,
	MB001,
	PckQty
)

SELECT 
	DenNo,
	ShopNo,
	DocNo,
	DocDate,
	ME002,	
	SignEmpNo,	
	DocOrd,
	-- p.TITLE,
	i.MB002 TITLE,
	-- p.CODE,
	i.MB080 CODE,
	i.MB013,
	i.MB001,
	PckQty 
FROM XX_DOC_HEADERS h 
	INNER JOIN XX_COUNTERS x ON x.CODE = h.ShopNo AND ACTIVE_CODE = N'Y'
	INNER JOIN SR.dbo.CMSME c ON c.ME001 = ERP_CODE
	CROSS APPLY (SELECT * FROM OPENJSON (h.DocDetial) WITH (
		DocOrd			NUMERIC			'$.DocOrd',
		GdsNo			NVARCHAR(100)	'$.GdsNo',
		PckQty			NUMERIC			'$.PckQty',
		BUnit			NVARCHAR(100)	'$.BUnit',
		PckPrc			NUMERIC			'$.PckPrc',
		PckStt			NUMERIC			'$.PckStt',
		TagNo			NVARCHAR(100)	'$.TagNo',
		DocDetRem		NVARCHAR(100)	'$.DocDetRem'
	)) AS l 
	LEFT JOIN SR.dbo.INVMB i ON i.MB001 = l.GdsNo 
WHERE 1=1 
	AND DocTyNo = N'CM' 
	AND DenNo IN ('A000', 'A118', 'A119', 'M100009')
	AND PckQty > 0
	-- AND NOT EXISTS (SELECT 'X' FROM SR..PURTC WHERE TC079 = DocNo AND TC039 = N'RETEX_POS')
;

IF ( @DenNo IN (N'A118', N'A119', N'M100009') )
	BEGIN
		SELECT 
			DocNo		進貨單號碼,
			N''			自訂單號,
			DocDate		建立日期,
			N'進貨單'    種類,
			ME002		分店,
			N'新開單'	 貨單狀態,
			SignEmpNo	進貨人員,
			N'未到貨'	 到貨狀態,
			TITLE		商品名稱,
			N''			商品規格,
			CODE		商品貨號,
			MB013		商品條碼,
			MB001		商品編碼,
			PckQty		進貨數量
		FROM @XX_DOC_OUTPUT
		WHERE DenNo = @DenNo		
	END
ELSE
	BEGIN 
		SELECT 
			DocNo		進貨單號碼,
			N''			自訂單號,
			DocDate		建立日期,
			N'進貨單'	 種類,
			ME002		分店,
			N'新開單'	 貨單狀態,
			SignEmpNo	進貨人員,
			N'未到貨'	 到貨狀態,
			N''			入庫人員,
			0			點收數量,
			0			預期成本,
			0			實際成本,
			0			其他費用,
			N''			預定到貨日期,
			N''			完成進貨日期,
			N''			備註,	
			TITLE		商品名稱,
			N''			商品規格,
			CODE		商品貨號,
			MB013		商品條碼,
			PckQty		進貨數量,
			0			點收數量,
			0			價格,
			0			成本,
			0			總成本 
		FROM @XX_DOC_OUTPUT
		WHERE ShopNo = @ShopNo AND DenNo = @DenNo
		ORDER BY ShopNo, DocOrd
	END

GO