USE IFACE_SR
GO

CREATE OR ALTER VIEW IFACE_EIP_ORDER_vw
AS	
/*
    EIP Order Viewer
	來源為 EIP 且未經處理 (STATUS = 0) 銷貨相關單據 

	https://api-eip.speeding-rocket.com/orders.json 

	source_type: 

		super_landing	:	一頁商店
		shopee			:	蝦皮
		line_gift		:	LINE 禮物
		distributor		:	經銷商
		shopify			:	Shopify
		return_change	:	換貨(出貨)
		repost			:	補寄
*/
SELECT 
	APP_MODULE,
	APP_FUNCTION,
	DOC_ID,
	STATUS,
	ID,

	CASE SOURCE_TYPE
		WHEN N'distributor'	THEN	DISTRIBUTOR								-- 經銷商代號由 EIP 維護
		WHEN N'line_gift'					THEN N'MB3000042'				-- 零售客戶-Line禮物
		WHEN N'shopee'						THEN N'MB3000020'				-- 蝦皮 共用零售客戶
		-- 火箭快遞
		WHEN N'super_landing' THEN 
			CASE PAYMENT_METHOD 
				WHEN N'credit_card' THEN
					CASE PAYMENT_GATEWAY 
						WHEN N'ctbc'		THEN N'MB3000031'				-- 一頁商店共用零售客戶-CTBC信用卡
						WHEN N'paypal'		THEN N'FB20001002'				-- 一頁商店零售客戶-PAYPAL
						WHEN N'molpay'		THEN N'FB20001001'				-- 一頁商店共用零售客戶-RAZER
						WHEN N'funbiz'		THEN N'MB3000047'				-- 一頁商店共用零售客戶-豐收款
						ELSE N''
					END -- PAYMENT GATEWAY
				WHEN N'bank'	THEN
					IIF (SUBSTRING(ORDER_ID,1,3) = N'LSP',	N'MB3000035',	-- 一頁商店共用零售客戶-員購
					IIF (SUBSTRING(ORDER_ID,1,2) = N'SX',	N'MB3000035',	-- 一頁商店共用零售客戶-員購
						CASE PAYMENT_GATEWAY 
							WHEN N'newebpay'	THEN N'MB3000032'			-- 一頁商店共用零售客戶-Ezpay
							WHEN N'paypal'		THEN N'FB20001002'			-- 一頁商店零售客戶-PAYPAL
							WHEN N'molpay'		THEN N'FB20001001'			-- 一頁商店共用零售客戶-RAZER
							ELSE 					 N'MB3000030'		    -- 一頁商店共用零售客戶-銀行轉帳
						END
					))
				WHEN N'linepay'				THEN N'MB3000038'				-- 一頁商店零售客戶-Linepay
				WHEN N'cash_on_delivery' THEN					-- 到收
					IIF (SUBSTRING(ORDER_ID,1,3) = N'LSP',	N'MB3000035',	-- 一頁商店共用零售客戶-員購
					IIF (SUBSTRING(ORDER_ID,1,2) = N'SX',	N'MB3000035',	-- 一頁商店共用零售客戶-員購
						CASE SHIPPING_PROVIDER
							WHEN N'fami'	THEN N'MB3000033'				-- 一頁商店/SHOPLINE-全家代收
							WHEN N'tcat'	THEN N'MB3000034'				-- 一頁商店/SHOPLINE-黑貓代收
							WHEN N'hct'		THEN N'MB3000036'				-- 一頁商店-新竹物流代收
							WHEN N'unimart' THEN N'MB3000040'				-- SHOPLINE-綠界
							ELSE N''
						END -- SHIPPING_PROVIDER
					))	
				WHEN N'postpay'				THEN N'MB3000039'				-- 一頁商店零售客戶-AFTEE
			END			-- PAYMENT METHOD
		-- Shopify -- ver 7.4 Add
		WHEN N'shopify'	THEN
			CASE PAYMENT_METHOD
				WHEN N'linepay'				THEN N'MB3000044'				-- shopify-Linepay			
				WHEN N'credit_card'			THEN N'MB3000045'				-- shopify-CTBC信用卡
				WHEN N'cash_on_delivery'	THEN 
					CASE SHIPPING_PROVIDER
							WHEN N'fami'	THEN N'MB3000043'				-- shopify-全家代收			
							WHEN N'tcat'	THEN N'MB3000046'				-- shopify-黑貓代收
							WHEN N'hct'		THEN N''				
							WHEN N'unimart' THEN N''				
							ELSE N''
					END -- SHIPPING_PROVIDER
			END
		ELSE N''
	END  CUSTOMER_NO,	-- SOURCE_TYPE
		
	ORDER_ID,
	ORDER_DATE,
	TRACKING_CODE,
	SHIP_NO,
	REF_ID,
	SIGNED_STATUS,
	SOURCE_TYPE,
	PAYMENT_METHOD,
	PAYMENT_GATEWAY,
	PAID,
	PAYMENT_TRANSACTION_ID,
	SHIPPING_METHOD,
	SHIPPING_STATUS,
	SHIPPING_PROVIDER,
	ISNULL(SHIPPED_DATE, ORDER_DATE) SHIPPED_DATE, 
	RECIPIENT,
	MOBILE,
	COUNTRY,
	ADDR1,
	ADDR2,
	CITY,
	ZIPCODE,
	STATE,
	ADDRESS,
	ISNULL(NOTE, N'') NOTE,
	ISNULL(NOTE_SHIPPING, N'') NOTE_SHIPPING,
	ISNULL(NOTE_EIP, N'') NOTE_EIP,
	UPPER(CURRENCY) CURRENCY,
	TOTAL_ITEMS_COUNT,
	TOTAL_ITEMS_AMOUNT,
	SHIPPING_FEE,
	TOTAL_ORDER_AMOUNT,
	ITEMS,
	INVOICE_ID,
	INVOICE_NO,
	INVOICE_DATE,
	INVOICE_STATUS,
	INVOICE_TYPE,
	INVOICE_TARGET,
	INVOICE_BUYER,
	INVOICE_AMOUNT,
	INVOICE_SALES,
	INVOICE_TAX,
	ALLOWANCE_REMAIN_AMT,
	TRANSACTION_ID,
	RANDOM_NUMBER,
	INVOICE_ITEMS,
	DISTRIBUTOR,
	DIST_TITLE,
	STORE_CODE,
	STORE_TITLE,
	AMT_WITH_TAX,
	TAX_TYPE,
	TAX_AMOUNT
FROM IFACE
	CROSS APPLY
	OPENJSON (JSON_DOC, '$.data') WITH 
		(
			ID				NUMERIC			'$.id',
			ORDER_ID		NVARCHAR(255)	'$.global_order_id',
			ORDER_DATE		DATE			'$.order_created_date',
			TRACKING_CODE	NVARCHAR(255)	'$.tracking_code',
			SHIP_NO			NVARCHAR(255)	'$.xdelivery_ship_no',
			REF_ID			NVARCHAR(255)	'$.ref_id',
			SIGNED_STATUS	NVARCHAR(255)	'$.signed_status',
			SOURCE_TYPE		NVARCHAR(255)	'$.source_type',
			PAYMENT_METHOD	NVARCHAR(255)	'$.payment_method',
			PAYMENT_GATEWAY	NVARCHAR(255)	'$.payment_gateway',
			PAID			NVARCHAR(255)	'$.paid',
			PAYMENT_TRANSACTION_ID	NVARCHAR(MAX)	'$.payment_transaction_id' AS JSON,
			SHIPPING_METHOD	NVARCHAR(255)	'$.shipping_method',
			SHIPPING_STATUS	NVARCHAR(255)	'$.shipping_status',
			SHIPPING_PROVIDER	NVARCHAR(255)	'$.shipping_provider',
			SHIPPED_DATE	DATE			'$.shipped_at',
			RECIPIENT		NVARCHAR(255)	'$.recipient',
			MOBILE			NVARCHAR(255)	'$.mobile',
			COUNTRY			NVARCHAR(255)	'$.country',
			ADDR1			NVARCHAR(255)	'$.addr1',
			ADDR2			NVARCHAR(255)	'$.addr2',
			CITY			NVARCHAR(255)	'$.city',
			ZIPCODE			NVARCHAR(255)	'$.zipcode',
			STATE			NVARCHAR(255)	'$.state',
			ADDRESS			NVARCHAR(255)	'$.address',
			NOTE			NVARCHAR(255)	'$.note',
			NOTE_SHIPPING	NVARCHAR(255)	'$.note_shipping',
			NOTE_EIP		NVARCHAR(255)	'$.note_eip',
			CURRENCY		NVARCHAR(255)	'$.currency',
			TOTAL_ITEMS_COUNT	NUMERIC		'$.total_items_count',
			TOTAL_ITEMS_AMOUNT	NUMERIC		'$.total_items_amount',
			SHIPPING_FEE		NUMERIC		'$.shipping_fee',
			TOTAL_ORDER_AMOUNT	NUMERIC		'$.total_order_amount',
			ITEMS			NVARCHAR(MAX)	'$.items' AS JSON,
			INVOICE_ID		NUMERIC			'$.invoice.id',
			INVOICE_NO		NVARCHAR(255)	'$.invoice.invoice_no',
			INVOICE_DATE	DATE			'$.invoice.invoiced_date',
			INVOICE_STATUS	NVARCHAR(255)	'$.invoice.status',
			INVOICE_TYPE	NVARCHAR(255)	'$.invoice.create_type',
			INVOICE_TARGET	NVARCHAR(255)	'$.invoice.invoice_target',
			INVOICE_BUYER	NVARCHAR(255)	'$.invoice.buyer_name',
			INVOICE_AMOUNT	NUMERIC			'$.invoice.total_amount',
			INVOICE_SALES	NUMERIC			'$.invoice.sales',
			INVOICE_TAX		NUMERIC			'$.invoice.tax',
			ALLOWANCE_REMAIN_AMT	NUMERIC	'$.invoice.allowance_remain_amount',
			TRANSACTION_ID	NVARCHAR(255)	'$.invoice.transaction_id',
			RANDOM_NUMBER	NVARCHAR(255)	'$.invoice.random_number',
			INVOICE_ITEMS	NVARCHAR(MAX)	'$.invoice.items' AS JSON,
			DISTRIBUTOR		NVARCHAR(255)	'$.distributor.code',
			DIST_TITLE		NVARCHAR(255)	'$.distributor.title',
			STORE_CODE		NVARCHAR(255)	'$.storehouse.code',
			STORE_TITLE		NVARCHAR(255)	'$.storehouse.title',
			AMT_WITH_TAX	BIT				'$.amount_with_tax',
			TAX_TYPE		NVARCHAR(100)	'$.tax.type',
			TAX_AMOUNT		NUMERIC			'$.tax.amount'
		)
WHERE 1=1 
	AND STATUS = N'0'
	AND APP_MODULE = N'EIP'
	AND APP_FUNCTION IN (
		N'super_landing', 
		N'shopee', 
		N'line_gift',
		N'distributor', 
		N'shopify',  
		N'return_change', 
		N'repost'
	)
;