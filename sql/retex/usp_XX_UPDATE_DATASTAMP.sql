USE IFACE_SR;
GO

IF OBJECT_ID ( 'XX_UPDATE_DATASTAMP', 'P' ) IS NOT NULL   
    DROP PROCEDURE XX_UPDATE_DATASTAMP;  

GO  

CREATE PROCEDURE XX_UPDATE_DATASTAMP  
AS

DECLARE @XX_DOC_HEADERS TABLE (
	DOC_ID			NVARCHAR(100),
	DocNo			NVARCHAR(100),
	DocTyNo			NVARCHAR(100),
	DocCla			NVARCHAR(100),
	DocDate			DATE,
	ShopNo			NVARCHAR(100),
	DocRem			NVARCHAR(255),
	DenNo			NVARCHAR(100),
	SignEmpNo		NVARCHAR(100),
	AmtTot			NUMERIC,
	DataStamp		NUMERIC,
	DocDetial		NVARCHAR(MAX)

)

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
	AND STATUS = '5'
	AND APP_FUNCTION IN ( N'CM', N'ST', N'BO', N'MO', N'ME') AND APP_MODULE = N'RETEX';

UPDATE XX_DATASTAMP 
SET DataStamp = (SELECT MAX(DataStamp) MaxDataStamp FROM @XX_DOC_HEADERS);