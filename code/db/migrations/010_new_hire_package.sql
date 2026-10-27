-- The new-hire information package (US-031): prepared from validated knowledge,
-- reviewed by the Onboarding Team, then sent. Synthetic content only.
CREATE TABLE IF NOT EXISTS new_hire_packages (
    case_id     TEXT        PRIMARY KEY REFERENCES cases (id),
    content     JSONB       NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'sent')),
    prepared_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_by TEXT,
    sent_at     TIMESTAMPTZ
);
