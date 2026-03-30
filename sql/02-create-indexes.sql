USE [IFACE]
GO

-- ================================================================
-- 02-create-indexes.sql
-- 建立 IFACE 及 IFACE_ERROR 資料表索引
-- ================================================================


-- ----------------------------------------------------------------
-- IFACE 索引
-- ----------------------------------------------------------------

-- 索引 1：(STATUS, APP_MODULE, APP_FUNCTION)
-- 對應：SP 查詢 WHERE STATUS = '0' AND APP_MODULE = N'...'
--        ifaceStatusUpdate 的 WHERE 條件
--        iface-db /status-update 端點的查詢
CREATE NONCLUSTERED INDEX [IX_IFACE_STATUS_MODULE_FUNCTION]
    ON [dbo].[IFACE] ([STATUS] ASC, [APP_MODULE] ASC, [APP_FUNCTION] ASC)
    INCLUDE ([DOC_ID], [BATCH_ID], [CREATION_DATE])
    WITH (FILLFACTOR = 80, ONLINE = OFF)
GO

-- 索引 2：(STATUS, CREATION_DATE DESC)
-- 對應：reply view 查詢（WHERE STATUS = '6' ORDER BY CREATION_DATE）
--        歷史資料查詢與封存作業
CREATE NONCLUSTERED INDEX [IX_IFACE_STATUS_DATE]
    ON [dbo].[IFACE] ([STATUS] ASC, [CREATION_DATE] DESC)
    INCLUDE ([APP_MODULE], [APP_FUNCTION], [BATCH_ID])
    WITH (FILLFACTOR = 80, ONLINE = OFF)
GO

-- 索引 3：BATCH_ID
-- 對應：iface-db /transactions 端點以 BATCH_ID 查詢狀態
--        跨系統 batch 追蹤
CREATE NONCLUSTERED INDEX [IX_IFACE_BATCH_ID]
    ON [dbo].[IFACE] ([BATCH_ID] ASC)
    INCLUDE ([STATUS], [APP_MODULE], [APP_FUNCTION], [CREATION_DATE])
    WITH (FILLFACTOR = 90, ONLINE = OFF)
GO


-- ----------------------------------------------------------------
-- IFACE_ERROR 索引
-- ----------------------------------------------------------------

-- 索引 4：(RESOLVED, QUARANTINE_DATE DESC)
-- 對應：未解決的 quarantine 資料查詢
CREATE NONCLUSTERED INDEX [IX_IFACE_ERROR_RESOLVED]
    ON [dbo].[IFACE_ERROR] ([RESOLVED] ASC, [QUARANTINE_DATE] DESC)
    INCLUDE ([APP_MODULE], [APP_FUNCTION], [ERROR_MESSAGE])
GO

-- 索引 5：ORIGINAL_DOC_ID
-- 對應：來源追蹤，從 IFACE 找到對應的 IFACE_ERROR 記錄
CREATE NONCLUSTERED INDEX [IX_IFACE_ERROR_ORIGINAL]
    ON [dbo].[IFACE_ERROR] ([ORIGINAL_DOC_ID] ASC)
GO
