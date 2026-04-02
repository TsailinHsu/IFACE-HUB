USE [IFACE_SR]
GO

/*

    建立 RETEX POS 門市代號對應 ERP 門市代號資料表

*/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[XX_COUNTERS](
	[COUNTER]       [nvarchar](255) NULL,
	[ADDRESS]       [nvarchar](255) NULL,
	[CODE]          [nvarchar](255) NULL,
	[DEPARTMENT]    [nvarchar](255) NULL,
	[INVENTORY]     [nvarchar](255) NULL,
	[CUSTOMER_CODE] [nvarchar](255) NULL,
	[DISCOUNT]      [numeric](18, 4) NULL,
	[CUST_FNAME]    [nvarchar](255) NULL,
	[ERP_CODE]      [nvarchar](255) NULL,
	[RATE_TYPE]     [nvarchar](1) NULL,
	[DOC_TYPE]      [nvarchar](255) NULL,
	[RDOC_TYPE]     [nvarchar](255) NULL,
	[END_DATE]      [date] NULL,
	[START_DATE]    [date] NULL,
	[ACTIVE_CODE]   [nchar](1) NULL,
	[SR_CUSTOMER_CODE] [nvarchar](255) NULL,
	[SR_CUST_NAME]  [nvarchar](255) NULL,
	[SR_DOC_TYPE]   [nvarchar](255) NULL,
	[SR_RDOC_TYPE]  [nvarchar](255) NULL
) ON [PRIMARY]
GO