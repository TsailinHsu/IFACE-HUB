USE [IFACE]
GO

/*
    Migration 01 — 新增 IFACE 資料表欄位
    目的：增加處理追蹤與錯誤記錄能力

    STATUS 語義：
      '0' = pending    (寫入待處理，現有)
      '5' = processing (SP 執行中，現有)
      '6' = complete   (處理完成，現有)
      'E' = error      (處理失敗，新增)

    執行前確認：
      - IFACE 資料表存在
      - 欄位 PROCESSED_DATE, ERROR_MESSAGE, RETRY_COUNT 不存在
*/

-- 檢查並新增 PROCESSED_DATE
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.IFACE')
      AND name = N'PROCESSED_DATE'
)
BEGIN
    ALTER TABLE [dbo].[IFACE]
        ADD [PROCESSED_DATE] [datetime] NULL;
    PRINT 'Added column: PROCESSED_DATE';
END
ELSE
    PRINT 'Column already exists: PROCESSED_DATE';
GO

-- 檢查並新增 ERROR_MESSAGE
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.IFACE')
      AND name = N'ERROR_MESSAGE'
)
BEGIN
    ALTER TABLE [dbo].[IFACE]
        ADD [ERROR_MESSAGE] [nvarchar](max) NULL;
    PRINT 'Added column: ERROR_MESSAGE';
END
ELSE
    PRINT 'Column already exists: ERROR_MESSAGE';
GO

-- 檢查並新增 RETRY_COUNT
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.IFACE')
      AND name = N'RETRY_COUNT'
)
BEGIN
    ALTER TABLE [dbo].[IFACE]
        ADD [RETRY_COUNT] [int] NOT NULL DEFAULT 0;
    PRINT 'Added column: RETRY_COUNT';
END
ELSE
    PRINT 'Column already exists: RETRY_COUNT';
GO

-- STATUS 欄位現為 NVARCHAR(1)，'E' 仍為單一字元，無需修改型別
-- 驗證結果
SELECT
    c.name          AS column_name,
    t.name          AS data_type,
    c.max_length,
    c.is_nullable,
    c.column_id
FROM sys.columns c
JOIN sys.types   t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID(N'dbo.IFACE')
ORDER BY c.column_id;
GO
