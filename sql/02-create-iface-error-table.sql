USE [IFACE]
GO

/*
    Migration 02 — 建立 IFACE_ERROR quarantine 資料表
    目的：儲存處理失敗的資料列，供人工審查與重試

    當 IFACE.STATUS = 'E' 時，同步將資料複製至此表
    原始 IFACE 資料列保留（不刪除），以 ORIGINAL_DOC_ID 關聯
*/

IF NOT EXISTS (
    SELECT 1 FROM sys.objects
    WHERE object_id = OBJECT_ID(N'dbo.IFACE_ERROR')
      AND type = N'U'
)
BEGIN
    CREATE TABLE [dbo].[IFACE_ERROR] (
        [ERROR_ID]       [bigint]       IDENTITY(1,1)  NOT NULL,
        [ORIGINAL_DOC_ID][int]          NOT NULL,           -- FK to IFACE.DOC_ID
        [BATCH_ID]       [nvarchar](50) NULL,
        [CREATION_DATE]  [datetime]     NULL,               -- 原始寫入時間
        [API]            [nvarchar](100) NULL,
        [APP_MODULE]     [nvarchar](100) NULL,
        [APP_FUNCTION]   [nvarchar](100) NULL,
        [QUERY]          [nvarchar](1000) NULL,
        [JSON_DOC]       [nvarchar](max) NULL,
        [MERCHANT]       [nvarchar](max) NULL,
        [ERROR_MESSAGE]  [nvarchar](max) NULL,              -- CATCH 取得的錯誤訊息
        [RETRY_COUNT]    [int]          NOT NULL DEFAULT 0, -- 已重試次數
        [QUARANTINE_DATE][datetime]     NOT NULL DEFAULT GETDATE(), -- 進入 quarantine 時間
        [RESOLVED]       [bit]          NOT NULL DEFAULT 0, -- 是否已人工處理
        [RESOLVED_DATE]  [datetime]     NULL,
        [RESOLVED_BY]    [nvarchar](100) NULL,
        [RESOLVED_NOTE]  [nvarchar](max) NULL,

        CONSTRAINT [PK_IFACE_ERROR] PRIMARY KEY CLUSTERED ([ERROR_ID] ASC)
    );
    PRINT 'Created table: IFACE_ERROR';
END
ELSE
    PRINT 'Table already exists: IFACE_ERROR';
GO

-- 未解決的 quarantine 資料查詢索引
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.IFACE_ERROR')
      AND name = N'IX_IFACE_ERROR_RESOLVED'
)
BEGIN
    CREATE INDEX [IX_IFACE_ERROR_RESOLVED]
        ON [dbo].[IFACE_ERROR] ([RESOLVED], [QUARANTINE_DATE] DESC)
        INCLUDE ([APP_MODULE], [APP_FUNCTION], [ERROR_MESSAGE]);
    PRINT 'Created index: IX_IFACE_ERROR_RESOLVED';
END
GO

-- 來源追蹤索引
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.IFACE_ERROR')
      AND name = N'IX_IFACE_ERROR_ORIGINAL'
)
BEGIN
    CREATE INDEX [IX_IFACE_ERROR_ORIGINAL]
        ON [dbo].[IFACE_ERROR] ([ORIGINAL_DOC_ID]);
    PRINT 'Created index: IX_IFACE_ERROR_ORIGINAL';
END
GO

-- 驗證結果
SELECT
    c.name          AS column_name,
    t.name          AS data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns c
JOIN sys.types   t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID(N'dbo.IFACE_ERROR')
ORDER BY c.column_id;
GO
