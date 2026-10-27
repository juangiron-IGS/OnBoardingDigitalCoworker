-- Application roles. Idempotent: apply_db.sh may run on an existing database.
SELECT format('CREATE ROLE coworker_app LOGIN PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'coworker_app') \gexec
SELECT format('CREATE ROLE audit_writer LOGIN PASSWORD %L', :'audit_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'audit_writer') \gexec

GRANT USAGE ON SCHEMA public TO coworker_app, audit_writer;

-- Case state changes in place; package lines, decisions and applied actions are
-- records that are only ever added, never changed.
GRANT SELECT, INSERT, UPDATE ON cases, package_versions TO coworker_app;
GRANT SELECT, INSERT ON package_lines, approvals, action_ledger, it_approvals TO coworker_app;
GRANT USAGE ON SEQUENCE package_lines_id_seq, approvals_id_seq TO coworker_app;

-- Audit log: append-only for every application role (NFR-SEC-004).
-- coworker_app also needs INSERT so an action and its audit entry commit in one
-- transaction on one connection (NFR-REL-002); audit_writer serves standalone writes.
REVOKE ALL ON audit_log FROM PUBLIC;
GRANT SELECT, INSERT ON audit_log TO coworker_app;
GRANT INSERT ON audit_log TO audit_writer;
GRANT USAGE ON SEQUENCE audit_log_id_seq TO coworker_app, audit_writer;
-- No UPDATE, DELETE or TRUNCATE on audit_log is granted to any application role.

-- Simulated systems: records are only added, by the JobDiva and Workflow server.
GRANT USAGE ON SCHEMA mocks TO coworker_app;
GRANT SELECT, INSERT ON mocks.jobdiva_cases, mocks.task_lists, mocks.it_requests
    TO coworker_app;
GRANT USAGE ON SEQUENCE mocks.jobdiva_cases_id_seq, mocks.task_lists_id_seq,
    mocks.it_requests_id_seq TO coworker_app;

-- Simulated alerts: added by the notifications tool, read by the alerts view.
GRANT SELECT, INSERT ON mocks.alerts TO coworker_app;
GRANT USAGE ON SEQUENCE mocks.alerts_id_seq TO coworker_app;

-- Simulated mailbox: emails arrive, and the Coworker records what it did with each.
GRANT SELECT, INSERT ON mocks.inbound_mail TO coworker_app;
GRANT UPDATE (case_id, outcome) ON mocks.inbound_mail TO coworker_app;
GRANT USAGE ON SEQUENCE mocks.inbound_mail_id_seq TO coworker_app;

-- Onboarding knowledge: validation decisions and pending questions (US-025).
GRANT SELECT, INSERT ON mocks.knowledge_validations, mocks.knowledge_questions TO coworker_app;
GRANT USAGE ON SEQUENCE mocks.knowledge_validations_id_seq, mocks.knowledge_questions_id_seq TO coworker_app;
