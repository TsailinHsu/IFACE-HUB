USE [IFACE]
GO

/*
    Migration 03 — 建立 IFACE 資料表索引
    目的：解決 SP 及 API 查詢的 full table scan 問題

    現況：IFACE 僅有 DOC_ID clustered PK，所有 WHERE 條件均為 table scan
    預期效益：
      - IX_IFACE_STATUS_MODULE_FUNCTION：SP 查詢效能提升（主要 WHERE 條件）
      - IX_IFACE_STATUS_DATE：狀態追蹤與歷史查詢
      - IX_IFACE_BATCH_ID：batch 追蹤查詢
*/

-- ---------------------------------------------------------------
-- 索引 1：複合索引 (STATUS, APP_MODULE, APP_FUNCTION)
-- 對應：所有 SP 的 WHERE STATUS = '0' AND APP_MODULE = N'...'
--        ifaceStatusUpdate 的 WHERE 條件
--        iface-db /status-update 端點的查詢
-- ---------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.IFACE')
      AND name = N'IX_IFACE_STATUS_MODULE_FUNCTION'
)
BEGIN
    CREATE NONCLUSTERED INDEX [IX_IFACE_STATUS_MODULE_FUNCTION]
        ON [dbo].[IFACE] ([STATUS] ASC, [APP_MODULE] ASC, [APP_FUNCTION] ASC)
        INCLUDE ([DOC_ID], [BATCH_ID], [CREATION_DATE])
        WITH (FILLFACTOR = 80, ONLINE = OFF);
    PRINT 'Created index: IX_IFACE_STATUS_MODULE_FUNCTION';
END
ELSE
    PRINT 'Index already exists: IX_IFACE_STATUS_MODULE_FUNCTION';
GO

-- ---------------------------------------------------------------
-- 索引 2：(STATUS, CREATION_DATE DESC)
-- 對應：reply view 查詢（WHERE STATUS = '6' ORDER BY CREATION_DATE）
--        歷史資料查詢與封存作業
-- ---------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.IFACE')
      AND name = N'IX_IFACE_STATUS_DATE'
)
BEGIN
    CREATE NONCLUSTERED INDEX [IX_IFACE_STATUS_DATE]
        ON [dbo].[IFACE] ([STATUS] ASC, [CREATION_DATE] DESC)
        INCLUDE ([APP_MODULE], [APP_FUNCTION], [BATCH_ID])
        WITH (FILLFACTOR = 80, ONLINE = OFF);
    PRINT 'Created index: IX_IFACE_STATUS_DATE';
END
ELSE
    PRINT 'Index already exists: IX_IFACE_STATUS_DATE';
GO

-- ---------------------------------------------------------------
-- 索引 3：BATCH_ID
-- 對應：iface-db /transactions 端點以 BATCH_ID 查詢狀態
--        跨系統 batch 追蹤
-- ---------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.IFACE')
      AND name = N'IX_IFACE_BATCH_ID'
)
BEGIN
    CREATE NONCLUSTERED INDEX [IX_IFACE_BATCH_ID]
        ON [dbo].[IFACE] ([BATCH_ID] ASC)
        INCLUDE ([STATUS], [APP_MODULE], [APP_FUNCTION], [CREATION_DATE])
        WITH (FILLFACTOR = 90, ONLINE = OFF);
    PRINT 'Created index: IX_IFACE_BATCH_ID';
END
ELSE
    PRINT 'Index already exists: IX_IFACE_BATCH_ID';
GO

-- ---------------------------------------------------------------
-- 驗證：列出 IFACE 所有索引
-- ---------------------------------------------------------------
SELECT
    i.name          AS index_name,
    i.type_desc,
    i.fill_factor,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS key_columns
FROM sys.indexes i
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
JOIN sys.columns       c  ON c.object_id  = ic.object_id AND c.column_id = ic.column_id
WHERE i.object_id = OBJECT_ID(N'dbo.IFACE')
  AND ic.is_included_column = 0
GROUP BY i.name, i.type_desc, i.fill_factor
ORDER BY i.index_id;
GO
