USE IFACE_SR
GO

CREATE OR ALTER VIEW IFACE_EIP_INVENTORY_vw
AS	
/*
	EIP Inventory Transaction Viewer
	來源為 EIP 且未經處理 (STATUS = 0) 庫存相關單據

	1. https://api-eip.speeding-rocket.com/orders.json 
		source_type = requisit		

	2. https://api-eip.speeding-rocket.com/transfers.json
	3. https://api-eip.speeding-rocket.com/inventory_changes.json

*/

SELECT 
	APP_MODULE,
	APP_FUNCTION,
	DOC_ID,
	STATUS,
	ID,				
	ISNULL(ORDER_ID, GLOBAL_ID)			ORDER_ID,
	ISNULL(ORDER_DATE, CREATE_DATE)		ORDER_DATE,
	ISNULL(TRACKING_CODE, N'')			TRACKING_CODE,
	SHIP_NO,
	ISNULL(SOURCE_TYPE, APP_FUNCTION)	SOURCE_TYPE,
	ISNULL(SHIPPED_DATE, ISNULL(EXECUTE_DATE, UPDATED_DATE)) SHIPPED_DATE,
	ISNULL(CHANGE_TYPE, N'')			CHANGE_TYPE,
	ISNULL(REASON_TYPE, N'')			REASON_TYPE,
	ISNULL(RECIPIENT, N'')				RECIPIENT,		
	ISNULL(NOTE, N'')					NOTE,
	ISNULL(NOTE_SHIPPING, N'')			NOTE_SHIPPING,
	ISNULL(NOTE_EIP, N'')				NOTE_EIP,		
	ITEMS,		
	ISNULL(STORE_CODE, SOURCE_CODE)		SOURCE_CODE,
	ISNULL(STORE_TITLE, SOURCE_TITLE)	SOURCE_TITLE,
	ISNULL(TARGET_CODE, N'')			TARGET_CODE,
	ISNULL(TARGET_TITLE, N'')			TARGET_TITLE,
	ISNULL(APPLIER_NAME, N'')			APPLIER_NAME,
	ISNULL(APPLIER_NO, N'')				APPLIER_NO,
	ISNULL(DEPT_TITLE, N'')				DEPT_TITLE,
	ISNULL(DEPT_LEVEL, N'')				DEPT_LEVEL,
	ISNULL(EXPENSE, N'')				EXPENSE,
	ISNULL(REQUISIT_NOTE, N'')			REQUISIT_NOTE
FROM IFACE
	CROSS APPLY
	OPENJSON (JSON_DOC, '$.data') WITH 
	(
		ID				NUMERIC			'$.id',
		ORDER_ID		NVARCHAR(255)	'$.global_order_id',
		GLOBAL_ID		NVARCHAR(100)	'$.global_id',				-- transfers, inventoryChange
		ORDER_DATE		DATE			'$.order_created_date',
		CREATE_DATE		DATE			'$.created_at',
		TRACKING_CODE	NVARCHAR(255)	'$.tracking_code',
		SHIP_NO			NVARCHAR(255)	'$.xdelivery_ship_no',
		SOURCE_TYPE		NVARCHAR(255)	'$.source_type',				
		SHIPPED_DATE	DATE			'$.shipped_at',
		EXECUTE_DATE	DATE			'$.exexuted_at',

		UPDATED_DATE	DATE			'$.updated_at',				-- inventoryChange
		CHANGE_TYPE		NVARCHAR(255)	'$.change_type',			-- inventoryChange, ChangeType: deduct(扣庫存), add(加庫存)
		REASON_TYPE		NVARCHAR(255)	'$.reason_type',			-- inventoryChange, ReasonType: 
																	--		not_for_sale(商品無法再銷售), adjustment(庫存調整), stock_diff(盤差調整), other(其他)
		RECIPIENT		NVARCHAR(255)	'$.recipient',				
		NOTE			NVARCHAR(255)	'$.note',
		NOTE_SHIPPING	NVARCHAR(255)	'$.note_shipping',
		NOTE_EIP		NVARCHAR(255)	'$.note_eip',				
		ITEMS			NVARCHAR(MAX)	'$.items' AS JSON,			
		STORE_CODE		NVARCHAR(255)	'$.storehouse.code',
		STORE_TITLE		NVARCHAR(255)	'$.storehouse.title',
		SOURCE_ID		NUMERIC			'$.source.id',				-- transfers
		SOURCE_CODE		NVARCHAR(100)	'$.source.code',			-- transfers
		SOURCE_TITLE	NVARCHAR(100)	'$.source.title',			-- transfers
		TARGET_ID		NUMERIC			'$.target.id',				-- transfers
		TARGET_CODE		NVARCHAR(100)	'$.target.code',			-- transfers
		TARGET_TITLE	NVARCHAR(100)	'$.target.title',			-- transfers
		APPLIER_NAME	NVARCHAR(255)	'$.requisit.applier_name',
		APPLIER_NO		NVARCHAR(255)	'$.requisit.applier_no',
		DEPT_TITLE		NVARCHAR(255)	'$.requisit.dept_title',
		DEPT_LEVEL		NVARCHAR(255)	'$.requisit.dept_level_name',
		EXPENSE			NVARCHAR(255)	'$.requisit.expense',
		REQUISIT_NOTE	NVARCHAR(255)	'$.requisit.notes'
	)
WHERE 1=1 
	AND STATUS = '0'
	AND APP_MODULE = N'EIP'
	AND APP_FUNCTION IN (
		N'transfers',		-- 轉倉單
		N'requisit',		-- 公關品, 領料單
		N'inventoryChange'	-- 庫存異動
	)
;