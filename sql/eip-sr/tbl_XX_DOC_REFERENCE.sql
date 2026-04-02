USE [IFACE_SR]
GO

/**

   紀錄原單據與 ERP 單據號碼對應, 紀錄執行結果

**/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[XX_DOC_REFERENCE](
	[DOC_TYPE]      [nvarchar](50) NULL,
	[DOC_NUMBER]    [nvarchar](50) NULL,
	[DOC_DATE]      [nvarchar](8) NULL,
	[REF_1]         [nvarchar](255) NULL,
	[REF_2]         [nvarchar](255) NULL,
	[REF_3]         [nvarchar](255) NULL,
	[REF_4]         [nvarchar](255) NULL,
	[REF_5]         [nvarchar](255) NULL,
	[REF_6]         [nvarchar](255) NULL,
	[REF_7]         [nvarchar](255) NULL,
	[REF_8]         [nvarchar](255) NULL,
	[REF_9]         [nvarchar](255) NULL,
	[REF_10]        [nvarchar](255) NULL,
	[DOC_BOOK]      [nvarchar](50) NULL
) ON [PRIMARY]
GO
