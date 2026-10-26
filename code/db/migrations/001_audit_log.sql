-- Every agent action, completed, refused or failed (US-018, checkpoint data model).
-- Append-only: no application role gets UPDATE, DELETE or TRUNCATE (db/roles/).
-- Restricted data is referenced by field name in data_refs, never by value.
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL   PRIMARY KEY,
    case_id         TEXT        NOT NULL,
    agent           TEXT        NOT NULL,          -- agent name or human role
    action          TEXT        NOT NULL,
    outcome         TEXT        NOT NULL CHECK (outcome IN ('completed', 'refused', 'failed')),
    approval_id     TEXT,
    package_version INTEGER,
    rule_ids        TEXT[]      NOT NULL DEFAULT '{}',  -- rules used, e.g. {R-PA-02}
    data_refs       JSONB       NOT NULL DEFAULT '{}',  -- field name -> source of the data used
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS audit_log_case_id_idx ON audit_log (case_id, id);
