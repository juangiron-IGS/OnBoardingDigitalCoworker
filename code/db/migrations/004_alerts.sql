-- Simulated Teams and email alerts shown in the simulated alerts view (FR-WEB-004).
-- Alerts name fields, never restricted values (BR-011).
CREATE TABLE IF NOT EXISTS mocks.alerts (
    id         BIGSERIAL   PRIMARY KEY,
    case_id    TEXT        NOT NULL,
    recipient  TEXT        NOT NULL,
    text       TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS alerts_case_id_idx ON mocks.alerts (case_id, id);
