-- 08_lift_vs_control_with_join.sql
-- Purpose: compare each group to the control using JOINs, like a real experiment reporting table.

WITH variant_info AS (                                              -- a small lookup table describing each variant
    SELECT *
    FROM (VALUES                                                    -- VALUES lets us type rows directly into SQL
        ('gate_30', 30, 'control'),                                 -- version, gate level, role
        ('gate_40', 40, 'treatment')
    ) AS v(version, gate_level, role)                               -- name the table and its columns
),
group_rates AS (                                                    -- one row per version with its D1 and D7 rates
    SELECT
        version,                                                    -- test group
        COUNT(*)                                   AS players,      -- players in the group
        AVG(CAST(retention_1 AS DOUBLE))           AS d1_rate,      -- share of TRUE values = D1 retention rate
        AVG(CAST(retention_7 AS DOUBLE))           AS d7_rate       -- share of TRUE values = D7 retention rate
    FROM players                                                    -- read from the players view
    GROUP BY version                                                -- one row per group
),
control_rates AS (                                                  -- pull out the control group's rates
    SELECT
        g.d1_rate AS control_d1_rate,                               -- control D1 rate
        g.d7_rate AS control_d7_rate                                -- control D7 rate
    FROM group_rates AS g                                           -- rates table, nicknamed g
    INNER JOIN variant_info AS v                                    -- INNER JOIN keeps rows that match in both tables
        ON g.version = v.version                                    -- match on the version name
    WHERE v.role = 'control'                                        -- keep only the control row
)
SELECT
    v.role,                                                         -- control or treatment
    v.gate_level,                                                   -- 30 or 40
    g.version,                                                      -- version name
    g.players,                                                      -- players
    ROUND(100 * g.d1_rate, 2)                                       AS d1_pct,               -- D1 rate in percent
    ROUND(100 * (g.d1_rate - c.control_d1_rate), 3)                 AS d1_diff_vs_control_pp, -- D1 difference in percentage points
    ROUND(100 * g.d7_rate, 2)                                       AS d7_pct,               -- D7 rate in percent
    ROUND(100 * (g.d7_rate - c.control_d7_rate), 3)                 AS d7_diff_vs_control_pp, -- D7 difference in percentage points
    ROUND(100 * (g.d7_rate - c.control_d7_rate) / c.control_d7_rate, 2) AS d7_relative_lift_pct  -- D7 change relative to control
FROM group_rates AS g                                               -- start from the rates table
INNER JOIN variant_info AS v                                        -- attach role and gate level
    ON g.version = v.version                                        -- match on version
CROSS JOIN control_rates AS c                                       -- CROSS JOIN attaches the single control row to every row
ORDER BY v.gate_level;                                              -- control first
