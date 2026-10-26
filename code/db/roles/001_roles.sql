-- Application roles. Idempotent: apply_db.sh may run on an existing database.
SELECT format('CREATE ROLE coworker_app LOGIN PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'coworker_app') \gexec
SELECT format('CREATE ROLE audit_writer LOGIN PASSWORD %L', :'audit_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'audit_writer') \gexec

GRANT USAGE ON SCHEMA public TO coworker_app, audit_writer;

-- Case state, packages, approvals and the action ledger.
GRANT SELECT, INSERT, UPDATE ON cases, package_versions, package_lines, approvals, action_ledger
    TO coworker_app;
GRANT USAGE ON SEQUENCE package_lines_id_seq, approvals_id_seq TO coworker_app;

-- Audit log: append-only for every application role (NFR-SEC-004).
-- coworker_app also needs INSERT so an action and its audit entry commit in one
-- transaction on one connection (NFR-REL-002); audit_writer serves standalone writes.
REVOKE ALL ON audit_log FROM PUBLIC;
GRANT SELECT, INSERT ON audit_log TO coworker_app;
GRANT INSERT ON audit_log TO audit_writer;
GRANT USAGE ON SEQUENCE audit_log_id_seq TO coworker_app, audit_writer;
-- No UPDATE, DELETE or TRUNCATE on audit_log is granted to any application role.
