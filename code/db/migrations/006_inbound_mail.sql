-- Start emails that arrive in the simulated onboarding mailbox during a demo
-- (US-001, US-037). Synthetic content only; reset.sh clears them.
CREATE TABLE IF NOT EXISTS mocks.inbound_mail (
    id          BIGSERIAL   PRIMARY KEY,
    sender      TEXT        NOT NULL,
    subject     TEXT        NOT NULL,
    body        TEXT        NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    case_id     TEXT,                              -- the case the Coworker opened, if any
    outcome     TEXT                               -- the Coworker's result for this email
);
