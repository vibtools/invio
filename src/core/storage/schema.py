from __future__ import annotations

DOMAIN_SCHEMA_VERSION = 1

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
}
