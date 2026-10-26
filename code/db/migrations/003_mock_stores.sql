-- Simulated enterprise systems written by the JobDiva and Workflow server only.
-- They live in the same PostgreSQL instance as the audit log, so an action and its
-- audit entry commit together (NFR-REL-002). Every row carries the approval ID
-- that authorized it (US-034 AC-003).
CREATE SCHEMA IF NOT EXISTS mocks;

-- The simulated JobDiva case created after approval (never the real JobDiva, BR-014).
CREATE TABLE IF NOT EXISTS mocks.jobdiva_cases (
    id          BIGSERIAL   PRIMARY KEY,
    case_id     TEXT        NOT NULL REFERENCES cases (id),
    approval_id TEXT        NOT NULL REFERENCES approvals (approval_id),
    data        JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The onboarding task list for the Onboarding Team.
CREATE TABLE IF NOT EXISTS mocks.task_lists (
    id          BIGSERIAL   PRIMARY KEY,
    case_id     TEXT        NOT NULL REFERENCES cases (id),
    approval_id TEXT        NOT NULL REFERENCES approvals (approval_id),
    data        JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Access and equipment requests to IT (Chelsea Tech). Never a real order.
CREATE TABLE IF NOT EXISTS mocks.it_requests (
    id          BIGSERIAL   PRIMARY KEY,
    case_id     TEXT        NOT NULL REFERENCES cases (id),
    approval_id TEXT        NOT NULL REFERENCES approvals (approval_id),
    data        JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
