USE [IFACE_LL]
GO

/*
    ERP 會計科目對應表, 用於 ACPTA 系統科目與單據蕾別對照
*/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[XX_ACPTA_ACCOUNT_MAP](
	[COMPANY]       [nvarchar](10) NOT NULL,
	[ACCOUNT]       [nvarchar](10) NOT NULL,
	[ACCOUNT_DESC]  [nvarchar](50) NULL,
	[DOC_TYPE]      [nvarchar](10) NOT NULL,
	[DOC_NAME]      [nvarchar](50) NULL,
	[DESCRIPTION] [nvarchar](255) NULL
) ON [PRIMARY]
GO


