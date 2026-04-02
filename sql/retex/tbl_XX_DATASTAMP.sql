USE [IFACE_SR]
GO

/*
    RETEX POS 使用 SQL Server TIMESTAMP 紀錄最後修改時間
    紀錄在 XX_DATASTAMP 資料表中, 大於這個值的交易顯示為最新修改

    此表紀錄該批資料最大的 TIMESTAMP 值
    每次批次更新資料後, 都會更新此表的值
*/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[XX_DATASTAMP](
	[DataStamp]     [numeric](18, 0) NULL
) ON [PRIMARY]
GO