-- 04_engagement_distribution.sql
-- Purpose: understand how skewed game rounds are, and find extreme players.

WITH ranked AS (                                               -- CTE that ranks players inside each group
    SELECT
        userid,                                                -- player id
        version,                                               -- test group
        sum_gamerounds,                                        -- rounds played
        ROW_NUMBER() OVER (PARTITION BY version ORDER BY sum_gamerounds DESC) AS rank_in_group  -- 1 = most rounds in that group
    FROM players                                               -- read from the players view
)
SELECT
    version,                                                   -- test group
    rank_in_group,                                             -- position inside the group
    userid,                                                    -- player id
    sum_gamerounds                                             -- rounds played
FROM ranked                                                    -- read from the ranking CTE
WHERE rank_in_group <= 5                                       -- keep only the top 5 players per group
ORDER BY version, rank_in_group;                               -- tidy ordering
