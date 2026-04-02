USE [IFACE_SR]
GO

/***

    紀錄 POS 門市訂單資料, 用於未來產生移倉單使用
    POS 門市訂單運作類似採購作業, 但, 門市屬於同一公司, ERP 應該產生移倉單
    這個表紀錄主要用於倉別對應關係

**/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[XX_POS_CM_HIST](
	[DOC_ID]    [int] IDENTITY(1,1) NOT NULL,
	[DocNo]     [nvarchar](100) NULL,
	[DocTyNo]   [nvarchar](100) NULL,
	[DocCla]    [nvarchar](100) NULL,
	[DocDate]   [date] NULL,
	[ShopNo]    [nvarchar](100) NULL,
	[DocRem]    [nvarchar](255) NULL,
	[DenNo]     [nvarchar](100) NULL,
	[SignEmpNo] [nvarchar](100) NULL,
	[AmtTot]    [numeric](18, 0) NULL,
	[DataStamp] [numeric](18, 0) NULL,
	[DocDetial] [nvarchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO