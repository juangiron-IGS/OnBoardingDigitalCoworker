-- Candidate follow-up, document check and payroll handoff (US-022, US-023, US-024).
-- Checkpoint data model "Document checklist". Synthetic content only.
CREATE TABLE IF NOT EXISTS document_checklist (
    id           BIGSERIAL   PRIMARY KEY,
    case_id      TEXT        NOT NULL REFERENCES cases (id),
    item         TEXT        NOT NULL,
    required_by  TEXT        NOT NULL,          -- rule ID or package line source
    status       TEXT        NOT NULL DEFAULT 'outstanding'
                 CHECK (status IN ('outstanding', 'pending_countersign', 'verified')),
    sent_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered_at TIMESTAMPTZ,
    verified_by  TEXT,
    verified_at  TIMESTAMPTZ,
    UNIQUE (case_id, item)
);

-- Reminders and escalations sent, at the simulated hour since the checklist went out.
CREATE TABLE IF NOT EXISTS followup_reminders (
    id        BIGSERIAL   PRIMARY KEY,
    case_id   TEXT        NOT NULL REFERENCES cases (id),
    kind      TEXT        NOT NULL CHECK (kind IN ('reminder', 'escalation')),
    at_hours  INTEGER     NOT NULL CHECK (at_hours >= 0),
    rule_id   TEXT        NOT NULL,
    sent_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The Onboarding Team approves the payroll handoff of one package version (FR-PAY-002).
CREATE TABLE IF NOT EXISTS payroll_handoffs (
    case_id         TEXT        NOT NULL REFERENCES cases (id),
    package_version INTEGER     NOT NULL,
    approved_by     TEXT        NOT NULL,
    approved_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (case_id, package_version)
);

-- Issues Payroll returns, each a task on its case (FR-PAY-003).
CREATE TABLE IF NOT EXISTS payroll_returns (
    id          BIGSERIAL   PRIMARY KEY,
    case_id     TEXT        NOT NULL REFERENCES cases (id),
    issue       TEXT        NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The payroll package sent to Payroll (Paychex, simulated). Written by the single
-- writer only, with the approval ID that authorized it.
CREATE TABLE IF NOT EXISTS mocks.payroll_packages (
    id          BIGSERIAL   PRIMARY KEY,
    case_id     TEXT        NOT NULL REFERENCES cases (id),
    approval_id TEXT        NOT NULL REFERENCES approvals (approval_id),
    data        JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
