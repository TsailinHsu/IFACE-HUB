USE IFACE_SR
GO

CREATE OR ALTER VIEW IFACE_EIP_ORDER_Return_vw 
AS
/*
    EIP Order Return Viewer
	來源為 EIP 且未經處理 (STATUS = 0) 銷退相關單據 

	https://api-eip.speeding-rocket.com/order_returns.json
	
	source_type:

		return			-- # 退貨單
		change			-- # 換貨單
		refund			-- # 純退款
		orderReject		-- # 拒收 
	
	https://api-eip.speeding-rocket.com/order_problems.json	 # 遺失, 問題件

*/
SELECT
	APP_MODULE,
	APP_FUNCTION,
	DOC_ID,
	STATUS,
	ID,
	ISNULL(ORDER_ID, ORDER_ID2) ORDER_ID,
	CREATE_AT,
	RETURN_STATUS,
	CASE APP_FUNCTION
		WHEN N'orderReject'	THEN N'orderReject'
		WHEN N'orderProblem' THEN N'orderProblem'
		ELSE RETURN_TYPE
	END RETURN_TYPE,
	RECIPIENT,
	MOBILE,
	ADDRESS,
	CASE APP_FUNCTION
		WHEN N'orderProblem' THEN DESCR 
		ELSE REASON
	END REASON,
	AMOUNT,
	ISNULL(RETURN_AT, EXECUTED_AT) EXECUTED_AT,
	REFUNDED_AT,
	ERP_REF_ID,
	ERP_PAYMENT_ID,
	WH_ID,
	WH_CODE,
	WH_TITLE,
	ITEMS,
	REPOST_ITEMS,
	ORG_ID,
	ORG_ORDER_ID,
	ORG_ORDER_AT,
	ORG_ORDER_STATUS,
	ORG_ORDER_RET_TYPE,
	REPOST_ID,
	REPOST_ORDER_ID,
	REPOST_ORDER_AT,
	REPOST_ORDER_STATUS,
	INVOICE_ID,
	INVOICE_BY_EIP,
	INVOICE_NO,
	INVOICE_DATE,
	INVOICE_STATUS,
	INVOICE_TYPE,
	INVOICE_TARGET,
	INVOICE_BUYER_NAME,
	INVOICE_AMOUNT,
	INVOICE_SALES,
	INVOICE_TAX,
	ALLOWANCE_REMAINING,
	INV_TRANSACTION_ID,
	INV_RANDOM_NUMBER,
	INV_REASON,
	SOURCE_TYPE
FROM IFACE
	CROSS APPLY	OPENJSON (JSON_DOC, '$.data') WITH 
	(
		ID					NUMERIC			'$.id',
		ORDER_ID			NVARCHAR(100)	'$.global_id',
		ORDER_ID2			NVARCHAR(100)	'$.order_id',
		CREATE_AT			DATE			'$.created_at',
		RETURN_STATUS		NVARCHAR(100)	'$.status',
		RETURN_TYPE			NVARCHAR(100)	'$.return_type',
		RECIPIENT			NVARCHAR(100)	'$.recipient',
		MOBILE				NVARCHAR(100)	'$.mobile',
		ADDRESS				NVARCHAR(255)	'$.address',
		REASON				NVARCHAR(1000)	'$.reason',
		DESCR				NVARCHAR(1000)	'$.desc',
		AMOUNT				NUMERIC			'$.total_return_amount',
		RETURN_AT			DATE			'$.returned_at',
		EXECUTED_AT			DATE			'$.executed_at',
		REFUNDED_AT			DATE			'$.refunded_at',
		ERP_REF_ID			NVARCHAR(100)	'$.erp_ref_id',
		ERP_PAYMENT_ID		NVARCHAR(100)	'$.erp_payment_ref_id',
		WH_ID				NUMERIC			'$.storehouse.id',
		WH_CODE				NVARCHAR(100)	'$.storehouse.code',
		WH_TITLE			NVARCHAR(100)	'$.storehouse.title',
		ITEMS				NVARCHAR(MAX)	'$.items' AS JSON,
		REPOST_ITEMS		NVARCHAR(MAX)	'$.repost_items' AS JSON,
		ORG_ID				NUMERIC			'$.order.id',
		ORG_ORDER_ID		NVARCHAR(100)	'$.order.global_order_id',
		ORG_ORDER_AT		DATE			'$.order.order_created_date',
		ORG_ORDER_STATUS	NVARCHAR(100)	'$.order.shipping_status',
		ORG_ORDER_RET_TYPE	NVARCHAR(100)	'$.order.return_type',
		REPOST_ID			NUMERIC			'$.repost_order.id',
		REPOST_ORDER_ID		NVARCHAR(100)	'$.repost_order.global_order_id',
		REPOST_ORDER_AT		DATE			'$.repost_order.order_created_date',
		REPOST_ORDER_STATUS	NVARCHAR(100)	'$.repost_order.shipping_status',
		INVOICE_ID			NUMERIC			'$.invoice.id',
		INVOICE_BY_EIP		BIT				'$.invoice.by_eip',
		INVOICE_NO			NVARCHAR(100)	'$.invoice.invoice_no',
		INVOICE_DATE		DATE			'$.invoice.invoiced_date',
		INVOICE_STATUS		NVARCHAR(100)	'$.invoice.status',
		INVOICE_TYPE		NVARCHAR(100)	'$.invoice.create_type',
		INVOICE_TARGET		NVARCHAR(100)	'$.invoice.invoice_target',
		INVOICE_BUYER_NAME	NVARCHAR(100)	'$.invoice.buyer_name',
		INVOICE_AMOUNT		NUMERIC			'$.invoice.total_amount',
		INVOICE_SALES		NUMERIC			'$.invoice.sales',
		INVOICE_TAX			NUMERIC			'$.invoice.tax',
		ALLOWANCE_REMAINING	NUMERIC			'$.invoice.allowance_remain_amount',
		INV_TRANSACTION_ID	NVARCHAR(100)	'$.invoice.transaction_id',
		INV_RANDOM_NUMBER	NVARCHAR(4)		'$.invoice.random_number',
		INV_REASON			NVARCHAR(100)	'$.invoice.reason',
		SOURCE_TYPE			NVARCHAR(100)	'$.source_type'
	)
WHERE 1=1 
		AND STATUS = N'0'
		AND APP_MODULE = N'EIP'
		AND APP_FUNCTION IN (
			N'return',			-- # 退貨單
			N'change',			-- # 換貨單
			N'refund',			-- # 純退款
			N'orderReject',		-- # 拒收  
			N'orderProblem'		-- # 遺失, 問題件
		) 