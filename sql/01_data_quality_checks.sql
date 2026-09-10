-- 01_data_quality_checks.sql
-- Purpose: confirm the table loaded correctly before any analysis.

SELECT
    COUNT(*)                                   AS total_rows,          -- how many rows exist in the table
    COUNT(DISTINCT userid)                     AS distinct_players,    -- how many unique players exist
    COUNT(*) - COUNT(DISTINCT userid)          AS duplicate_rows,      -- rows minus unique players = duplicates
    COUNT(*) - COUNT(userid)                   AS null_userid,         -- COUNT(column) skips NULLs, so the gap = NULLs
    COUNT(*) - COUNT(version)                  AS null_version,        -- NULL check for version
    COUNT(*) - COUNT(sum_gamerounds)           AS null_gamerounds,     -- NULL check for game rounds
    COUNT(*) - COUNT(retention_1)              AS null_retention_1,    -- NULL check for day-1 retention
    COUNT(*) - COUNT(retention_7)              AS null_retention_7,    -- NULL check for day-7 retention
    MIN(sum_gamerounds)                        AS min_rounds,          -- smallest game rounds value
    MAX(sum_gamerounds)                        AS max_rounds,          -- largest game rounds value
    CAST(SUM(CASE WHEN sum_gamerounds = 0 THEN 1 ELSE 0 END) AS INTEGER) AS zero_round_players  -- players who installed but never played
FROM players;                                                           -- 'players' is the view we create in Python
