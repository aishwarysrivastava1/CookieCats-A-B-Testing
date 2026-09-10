-- 02_group_sizes.sql
-- Purpose: count players in each test group and their share of the total.

SELECT
    version,                                                  -- the test group: gate_30 (control) or gate_40 (treatment)
    COUNT(*)                                   AS players,    -- number of players in this group
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 3) AS share_pct  -- window function: this group's count / total of all groups
FROM players                                                  -- read from the players view
GROUP BY version                                              -- one output row per group
ORDER BY version;                                             -- gate_30 first, then gate_40
