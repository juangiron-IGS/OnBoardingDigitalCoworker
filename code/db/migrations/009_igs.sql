-- Culture and Belonging (IGS): LDC tracker, welcome kit and leader messages
-- (US-028, US-029). Checkpoint data model "Cultural follow-up". Synthetic only.

-- LDC approves the welcome kit of one package version before it is sent.
CREATE TABLE IF NOT EXISTS ldc_kit_approvals (
    case_id         TEXT        NOT NULL REFERENCES cases (id),
    package_version INTEGER     NOT NULL,
    approved_by     TEXT        NOT NULL,
    approved_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (case_id, package_version)
);

-- Leader feedback request and congratulation: drafted, approved by LDC, then sent.
CREATE TABLE IF NOT EXISTS leader_messages (
    id          BIGSERIAL   PRIMARY KEY,
    case_id     TEXT        NOT NULL REFERENCES cases (id),
    kind        TEXT        NOT NULL CHECK (kind IN ('feedback_request', 'congratulation')),
    recipient   TEXT        NOT NULL,
    text        TEXT        NOT NULL,
    rule_id     TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft', 'approved', 'sent')),
    approved_by TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at     TIMESTAMPTZ,
    UNIQUE (case_id, kind)
);

-- The LDC tracker (SharePoint list, simulated) and the welcome kit shipment.
-- Written by the single writer only, with the approval ID that authorized it.
CREATE TABLE IF NOT EXISTS mocks.ldc_tracker (
    id          BIGSERIAL   PRIMARY KEY,
    case_id     TEXT        NOT NULL REFERENCES cases (id),
    approval_id TEXT        NOT NULL REFERENCES approvals (approval_id),
    data        JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mocks.welcome_kits (
    id          BIGSERIAL   PRIMARY KEY,
    case_id     TEXT        NOT NULL REFERENCES cases (id),
    approval_id TEXT        NOT NULL REFERENCES approvals (approval_id),
    data        JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
