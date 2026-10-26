-- Onboarding case: one row per person and start date (BR-004 blocks duplicates).
-- Intake fields that are not keys live in data (JSONB), keyed by field name.
CREATE TABLE IF NOT EXISTS cases (
    id                      TEXT        PRIMARY KEY,
    person_ref              TEXT        NOT NULL,
    start_date              DATE        NOT NULL,
    state                   TEXT        NOT NULL DEFAULT 'received',
    current_package_version INTEGER     NOT NULL DEFAULT 0,  -- 0 = no package yet
    recommended_owner       TEXT,                            -- set by Policy and Case Setup
    assigned_owner          TEXT,                            -- set only by a person (US-032)
    data                    JSONB       NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (person_ref, start_date)
);

-- One row per package version; earlier versions are kept (US-012 AC-002).
CREATE TABLE IF NOT EXISTS package_versions (
    case_id    TEXT        NOT NULL REFERENCES cases (id),
    version    INTEGER     NOT NULL CHECK (version >= 1),
    status     TEXT        NOT NULL CHECK (status IN ('ready', 'blocked', 'needs_clarification')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (case_id, version)
);

-- Each data point of a package version, with its label and source or rule ID (US-011).
CREATE TABLE IF NOT EXISTS package_lines (
    id                BIGSERIAL PRIMARY KEY,
    case_id           TEXT      NOT NULL,
    version           INTEGER   NOT NULL,
    field             TEXT      NOT NULL,
    value             TEXT,
    label             TEXT      NOT NULL CHECK (label IN ('source', 'inferred', 'recommended', 'exception')),
    source_or_rule_id TEXT      NOT NULL CHECK (source_or_rule_id <> ''),
    FOREIGN KEY (case_id, version) REFERENCES package_versions (case_id, version)
);

-- Every approve, return or reject decision (US-014). Only an approval gets an approval_id.
CREATE TABLE IF NOT EXISTS approvals (
    id              BIGSERIAL   PRIMARY KEY,
    case_id         TEXT        NOT NULL,
    package_version INTEGER     NOT NULL,
    decision        TEXT        NOT NULL CHECK (decision IN ('approve', 'return', 'reject')),
    approval_id     TEXT        UNIQUE,
    approver_role   TEXT        NOT NULL,
    comment         TEXT,
    decided_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (case_id, package_version) REFERENCES package_versions (case_id, version),
    CHECK ((decision = 'approve') = (approval_id IS NOT NULL))
);

-- Simulated actions already applied, keyed by approval ID and action, so a retry
-- never repeats a completed action (NFR-REL-005).
CREATE TABLE IF NOT EXISTS action_ledger (
    idempotency_key TEXT        PRIMARY KEY,
    approval_id     TEXT        NOT NULL REFERENCES approvals (approval_id),
    package_version INTEGER     NOT NULL,
    action          TEXT        NOT NULL,
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
