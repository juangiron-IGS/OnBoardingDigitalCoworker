-- IT's approval of the access and laptop request in a package version (US-020,
-- BR-012). The single writer sends the request only when this row exists for the
-- version the approver approved.
CREATE TABLE IF NOT EXISTS it_approvals (
    case_id         TEXT        NOT NULL,
    package_version INTEGER     NOT NULL,
    approver_role   TEXT        NOT NULL,
    approved_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (case_id, package_version),
    FOREIGN KEY (case_id, package_version) REFERENCES package_versions (case_id, version)
);
