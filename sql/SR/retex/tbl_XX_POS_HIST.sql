USE [IFACE_SR]
GO

/***

    紀錄 POS 門市銷售訂單資料,
    因為百貨門市銷售資料較多, 受限於 ERP 效能, 無法以明細匯入, 故以此表紀錄完整訂單資料
    主要用於判斷是否重複匯入

**/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[XX_POS_HIST](
	[EcrHdKey]  [nvarchar](100) NULL,
	[ShopNo]    [nvarchar](100) NULL,
	[BDate]     [datetime] NULL,
	[HDate]     [datetime] NULL,
	[HTime]     [nvarchar](100) NULL,
	[HHD_VLD]   [nvarchar](100) NULL,
	[VipNo]     [nvarchar](100) NULL,
	[Amount]    [numeric](18, 0) NULL,
	[TraceHdKey]    [nvarchar](100) NULL,
	[SalesDetail]   [nvarchar](max) NULL,
	[SalesPayment]  [nvarchar](max) NULL,
	[SalesReceipt]  [nvarchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO