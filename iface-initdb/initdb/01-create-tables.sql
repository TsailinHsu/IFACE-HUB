-- ================================================================
-- 01-create-tables.sql
-- 建立 IFACE 及 IFACE_ERROR 資料表（冪等，可重複執行）
--
-- STATUS 語義：
--   '0' = pending    (寫入待處理)
--   '5' = processing (SP 執行中)
--   '6' = complete   (處理完成)
--   'E' = error      (處理失敗)
-- ================================================================


-- ----------------------------------------------------------------
-- Table 1: IFACE — 主要訊息佇列
-- ----------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM sys.objects
    WHERE object_id = OBJECT_ID(N'dbo.IFACE') AND type = N'U'
)
BEGIN
    CREATE TABLE [dbo].[IFACE] (
        [DOC_ID]         [bigint]         IDENTITY(1,1)  NOT NULL,
        [BATCH_ID]       [nvarchar](50)   NULL,
        [CREATION_DATE]  [datetime2](3)   NOT NULL  DEFAULT SYSUTCDATETIME(),
        [PROCESSED_DATE] [datetime2](3)   NULL,
        [API]            [nvarchar](100)  NULL,
        [APP_MODULE]     [nvarchar](100)  NULL,
        [APP_FUNCTION]   [nvarchar](100)  NULL,
        [QUERY_PARAMS]   [nvarchar](1000) NULL,
        [STATUS]         [char](1)        NOT NULL,
        [JSON_DOC]       [nvarchar](max)  NOT NULL,
        [MERCHANT]       [nvarchar](200)  NULL,
        [ERROR_MESSAGE]  [nvarchar](2000) NULL,
        [RETRY_COUNT]    [int]            NOT NULL  DEFAULT 0,

        CONSTRAINT [PK_IFACE] PRIMARY KEY CLUSTERED ([DOC_ID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF,
                  IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON,
                  ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = ON)
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

    PRINT 'Created table: IFACE'
END
ELSE
    PRINT 'Table already exists: IFACE'
GO


-- ----------------------------------------------------------------
-- Table 2: IFACE_ERROR — 處理失敗 quarantine 資料表
-- 當 IFACE.STATUS = 'E' 時，複製資料列至此表供人工審查與重試
-- 原始 IFACE 資料列保留，以 ORIGINAL_DOC_ID 關聯
-- ----------------------------------------------------------------
IF NOT EXISTS (
    SELECT 1 FROM sys.objects
    WHERE object_id = OBJECT_ID(N'dbo.IFACE_ERROR') AND type = N'U'
)
BEGIN
    CREATE TABLE [dbo].[IFACE_ERROR] (
        [ERROR_ID]        [bigint]         IDENTITY(1,1)  NOT NULL,
        [ORIGINAL_DOC_ID] [bigint]         NOT NULL,           -- FK to IFACE.DOC_ID
        [BATCH_ID]        [nvarchar](50)   NULL,
        [CREATION_DATE]   [datetime2](3)   NULL,               -- 原始寫入時間
        [API]             [nvarchar](100)  NULL,
        [APP_MODULE]      [nvarchar](100)  NULL,
        [APP_FUNCTION]    [nvarchar](100)  NULL,
        [QUERY_PARAMS]    [nvarchar](1000) NULL,
        [JSON_DOC]        [nvarchar](max)  NULL,
        [MERCHANT]        [nvarchar](200)  NULL,
        [ERROR_MESSAGE]   [nvarchar](2000) NULL,               -- CATCH 取得的錯誤訊息
        [RETRY_COUNT]     [int]            NOT NULL  DEFAULT 0,
        [QUARANTINE_DATE] [datetime2](3)   NOT NULL  DEFAULT SYSUTCDATETIME(),
        [RESOLVED]        [bit]            NOT NULL  DEFAULT 0, -- 是否已人工處理
        [RESOLVED_DATE]   [datetime2](3)   NULL,
        [RESOLVED_BY]     [nvarchar](100)  NULL,
        [RESOLVED_NOTE]   [nvarchar](max)  NULL,

        CONSTRAINT [PK_IFACE_ERROR] PRIMARY KEY CLUSTERED ([ERROR_ID] ASC)
            WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF,
                  IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON,
                  ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = ON)
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

    PRINT 'Created table: IFACE_ERROR'
END
ELSE
    PRINT 'Table already exists: IFACE_ERROR'
GO
