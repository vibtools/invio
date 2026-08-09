from __future__ import annotations

DOMAIN_SCHEMA_VERSION = 5

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    name TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    credential_ref TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS customer_lists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customer_emails (
    list_id TEXT NOT NULL REFERENCES customer_lists(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    email TEXT NOT NULL,
    PRIMARY KEY (list_id, ordinal),
    UNIQUE (list_id, email)
);

CREATE TABLE IF NOT EXISTS invoice_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    currency TEXT NOT NULL,
    days_until_due INTEGER NOT NULL,
    memo TEXT NOT NULL,
    footer TEXT NOT NULL,
    automatic_tax INTEGER NOT NULL,
    reuse_customer INTEGER NOT NULL,
    invoice_title TEXT NOT NULL,
    invoice_subtitle TEXT NOT NULL,
    invoice_type TEXT NOT NULL,
    customer_note TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoice_template_items (
    template_id TEXT NOT NULL REFERENCES invoice_templates(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity TEXT NOT NULL,
    unit_amount TEXT NOT NULL,
    tax_rate TEXT NOT NULL,
    PRIMARY KEY (template_id, ordinal)
);

CREATE TABLE IF NOT EXISTS invoice_template_terms (
    template_id TEXT NOT NULL REFERENCES invoice_templates(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    term TEXT NOT NULL,
    PRIMARY KEY (template_id, ordinal)
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    customer_list_id TEXT NOT NULL REFERENCES customer_lists(id),
    customer_list_name TEXT NOT NULL,
    invoice_template_id TEXT NOT NULL REFERENCES invoice_templates(id),
    invoice_template_name TEXT NOT NULL,
    status TEXT NOT NULL,
    total INTEGER NOT NULL,
    success INTEGER NOT NULL,
    failed INTEGER NOT NULL,
    processed INTEGER NOT NULL,
    last_message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_accounts (
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    account_name TEXT NOT NULL,
    PRIMARY KEY (task_id, ordinal),
    UNIQUE (task_id, account_id)
);

CREATE TABLE IF NOT EXISTS account_reservations (
    account_id TEXT PRIMARY KEY REFERENCES accounts(id),
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE
);
"""

MIGRATION_V1_TO_V2 = """
ALTER TABLE accounts ADD COLUMN last_verification_at TEXT NOT NULL DEFAULT '';
ALTER TABLE accounts ADD COLUMN verification_error_summary TEXT NOT NULL DEFAULT '';
"""

MIGRATION_V2_TO_V3 = """
ALTER TABLE customer_emails ADD COLUMN name TEXT NOT NULL DEFAULT '';
ALTER TABLE customer_emails ADD COLUMN country TEXT NOT NULL DEFAULT '';
"""

MIGRATION_V3_TO_V4 = """
CREATE TABLE task_execution_snapshots (
    task_id TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
    snapshot_state TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    assignment_strategy TEXT NOT NULL
);

CREATE TABLE task_snapshot_customers (
    task_id TEXT NOT NULL REFERENCES task_execution_snapshots(task_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    PRIMARY KEY (task_id, ordinal),
    UNIQUE (task_id, email)
);

CREATE TABLE task_snapshot_template (
    task_id TEXT PRIMARY KEY REFERENCES task_execution_snapshots(task_id) ON DELETE CASCADE,
    template_id TEXT NOT NULL,
    name TEXT NOT NULL,
    currency TEXT NOT NULL,
    days_until_due INTEGER NOT NULL,
    memo TEXT NOT NULL,
    footer TEXT NOT NULL,
    automatic_tax INTEGER NOT NULL,
    reuse_customer INTEGER NOT NULL,
    invoice_title TEXT NOT NULL,
    invoice_subtitle TEXT NOT NULL,
    invoice_type TEXT NOT NULL,
    customer_note TEXT NOT NULL
);

CREATE TABLE task_snapshot_template_items (
    task_id TEXT NOT NULL REFERENCES task_execution_snapshots(task_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity TEXT NOT NULL,
    unit_amount TEXT NOT NULL,
    tax_rate TEXT NOT NULL,
    PRIMARY KEY (task_id, ordinal)
);

CREATE TABLE task_snapshot_template_terms (
    task_id TEXT NOT NULL REFERENCES task_execution_snapshots(task_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    term TEXT NOT NULL,
    PRIMARY KEY (task_id, ordinal)
);

INSERT INTO task_execution_snapshots (task_id, snapshot_state, provider_id, assignment_strategy)
SELECT id, 'LegacyUnavailable', provider_id, 'recipient_ordinal_round_robin_v1'
FROM tasks;
"""

MIGRATION_V4_TO_V5 = """
CREATE TABLE task_delivery_runs (
    run_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    task_name TEXT NOT NULL,
    run_number INTEGER NOT NULL,
    provider_id TEXT NOT NULL,
    execution_mode TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL DEFAULT '',
    UNIQUE (task_id, run_number)
);

CREATE TABLE task_delivery_recipients (
    run_id TEXT NOT NULL REFERENCES task_delivery_runs(run_id) ON DELETE CASCADE,
    recipient_ordinal INTEGER NOT NULL,
    recipient_email TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    primary_account_id TEXT NOT NULL,
    primary_account_name TEXT NOT NULL,
    assigned_account_id TEXT NOT NULL DEFAULT '',
    assigned_account_name TEXT NOT NULL DEFAULT '',
    stage TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Pending',
    attempt_number INTEGER NOT NULL DEFAULT 0,
    provider_customer_id TEXT NOT NULL DEFAULT '',
    provider_invoice_id TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    finished_at TEXT NOT NULL DEFAULT '',
    error_class TEXT NOT NULL DEFAULT '',
    error_code TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    final_result TEXT NOT NULL DEFAULT 'Pending',
    PRIMARY KEY (run_id, recipient_ordinal),
    UNIQUE (run_id, recipient_email)
);

CREATE TABLE task_delivery_operations (
    run_id TEXT NOT NULL REFERENCES task_delivery_runs(run_id) ON DELETE CASCADE,
    recipient_ordinal INTEGER NOT NULL,
    attempt_number INTEGER NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT NOT NULL DEFAULT '',
    provider_reference TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL DEFAULT '',
    error_class TEXT NOT NULL DEFAULT '',
    error_code TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (run_id, recipient_ordinal, attempt_number, stage),
    FOREIGN KEY (run_id, recipient_ordinal)
        REFERENCES task_delivery_recipients(run_id, recipient_ordinal) ON DELETE CASCADE
);

CREATE INDEX idx_task_delivery_runs_task ON task_delivery_runs(task_id, run_number);
CREATE INDEX idx_task_delivery_recipients_email ON task_delivery_recipients(recipient_email);
CREATE INDEX idx_task_delivery_operations_status ON task_delivery_operations(status);
"""

APPLICATION_TABLES = {
    "accounts",
    "customer_lists",
    "customer_emails",
    "invoice_templates",
    "invoice_template_items",
    "invoice_template_terms",
    "tasks",
    "task_accounts",
    "account_reservations",
    "task_execution_snapshots",
    "task_snapshot_customers",
    "task_snapshot_template",
    "task_snapshot_template_items",
    "task_snapshot_template_terms",
    "task_delivery_operations",
    "task_delivery_recipients",
    "task_delivery_runs",
}
