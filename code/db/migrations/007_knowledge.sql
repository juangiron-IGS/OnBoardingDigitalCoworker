-- Onboarding knowledge (US-025, BR-013). The records are data in rules/knowledge;
-- these tables keep the Onboarding Team's validation decisions and the questions
-- no record answers, pending for the team. Synthetic content only.
CREATE TABLE IF NOT EXISTS mocks.knowledge_validations (
    id          BIGSERIAL   PRIMARY KEY,
    record_id   TEXT        NOT NULL,
    decision    TEXT        NOT NULL CHECK (decision IN ('validated', 'rejected')),
    decided_by  TEXT        NOT NULL,
    decided_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mocks.knowledge_questions (
    id          BIGSERIAL   PRIMARY KEY,
    question    TEXT        NOT NULL,
    asked_by    TEXT        NOT NULL,
    channel     TEXT        NOT NULL,
    reason      TEXT        NOT NULL CHECK (reason IN ('no_answer', 'hr_decision')),
    asked_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
