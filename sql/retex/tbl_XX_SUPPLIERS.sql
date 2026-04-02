USE [IFACE_SR]
GO

/***
    RETRX POS 系統 DEN_NO 與 ERP 供應上商對應表
    POS 系統供應商編號 DEN_NO 大部分與 ERP 供應商編號相同
    但有少部分不相同，故建立此對應表以利系統整合

**/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[XX_SUPPLIERS](
	[DEN_NO]        [nvarchar](50) NULL,
	[ERP_VENDOR_ID] [nvarchar](50) NULL,
	[VENDOR_NAME]   [nvarchar](250) NULL
) ON [PRIMARY]
GO
