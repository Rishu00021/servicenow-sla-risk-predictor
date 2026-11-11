-- MySQL-compatible DDL for the ServiceNow SLA Risk Predictor.
-- The demo loads the same schema into SQLite via src/load_to_db.py,
-- but this file is written for MySQL so the SQL skill is visible.
-- All data is synthetic; no real employer or ticket data is used.

CREATE TABLE IF NOT EXISTS assignment_groups (
    group_name     VARCHAR(100) PRIMARY KEY,
    contact_email  VARCHAR(255),
    member_count   INT
);

CREATE TABLE IF NOT EXISTS sla_policy (
    priority     VARCHAR(10) PRIMARY KEY,
    target_hours DECIMAL(6, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id         VARCHAR(20) PRIMARY KEY,
    short_description TEXT NOT NULL,
    category          VARCHAR(50),
    subcategory       VARCHAR(50),
    priority          VARCHAR(10),
    channel           VARCHAR(50),
    assignment_group  VARCHAR(100),
    opened_at         DATETIME,
    resolved_at       DATETIME,
    resolution_hours  DECIMAL(8, 2),
    queue_hours       DECIMAL(8, 2),
    sla_breach        TINYINT(1) NOT NULL DEFAULT 0,
    FOREIGN KEY (assignment_group) REFERENCES assignment_groups (group_name),
    FOREIGN KEY (priority) REFERENCES sla_policy (priority),
    INDEX idx_priority (priority),
    INDEX idx_group (assignment_group),
    INDEX idx_opened (opened_at)
);
