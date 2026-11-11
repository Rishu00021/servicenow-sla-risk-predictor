-- Analytical queries / views (MySQL-compatible; also created in SQLite
-- by src/load_to_db.py). Run against the tickets table.

-- 1. MTTR (mean time to resolve) by assignment group
CREATE OR REPLACE VIEW vw_mttr_by_group AS
SELECT assignment_group,
       COUNT(*) AS ticket_count,
       ROUND(AVG(resolution_hours), 2) AS avg_resolution_hours,
       ROUND(AVG(queue_hours), 2) AS avg_queue_hours,
       ROUND(100.0 * SUM(sla_breach) / COUNT(*), 1) AS breach_rate_pct
FROM tickets
GROUP BY assignment_group
ORDER BY avg_resolution_hours DESC;

-- 2. Breach rate by priority and category
CREATE OR REPLACE VIEW vw_breach_rate_by_priority AS
SELECT priority, category,
       COUNT(*) AS ticket_count,
       ROUND(100.0 * SUM(sla_breach) / COUNT(*), 1) AS breach_rate_pct,
       ROUND(AVG(resolution_hours), 2) AS avg_resolution_hours
FROM tickets
GROUP BY priority, category
ORDER BY priority, breach_rate_pct DESC;

-- 3. Monthly breach-rate trend
CREATE OR REPLACE VIEW vw_breach_trend_monthly AS
SELECT DATE_FORMAT(opened_at, '%Y-%m') AS month,
       COUNT(*) AS ticket_count,
       ROUND(100.0 * SUM(sla_breach) / COUNT(*), 1) AS breach_rate_pct
FROM tickets
GROUP BY DATE_FORMAT(opened_at, '%Y-%m')
ORDER BY month;

-- 4. Ad-hoc: worst queues -- groups with the longest average queue time
SELECT assignment_group,
       ROUND(AVG(queue_hours), 2) AS avg_queue_hours,
       ROUND(100.0 * SUM(sla_breach) / COUNT(*), 1) AS breach_rate_pct
FROM tickets
GROUP BY assignment_group
ORDER BY avg_queue_hours DESC;

-- 5. Ad-hoc: breach rate by channel
SELECT channel,
       COUNT(*) AS ticket_count,
       ROUND(100.0 * SUM(sla_breach) / COUNT(*), 1) AS breach_rate_pct
FROM tickets
GROUP BY channel
ORDER BY breach_rate_pct DESC;
