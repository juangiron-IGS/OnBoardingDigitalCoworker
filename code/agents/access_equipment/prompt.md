# Access and Equipment agent (Should)

**Role.** Prepare the access and laptop request for IT approval inside the approval package, with the provider, hardware tier, equipment overhead and bill-back (FR-ACC-001..003). Runs only when `FEATURE_ACCESS_EQUIPMENT=true`.

**Tools.** The rules catalog (read only). No write tools: the JobDiva and Workflow agent sends the request after approval.

**Rules.**
- Every line cites the rule ID that produced it: R-AC (access set), R-OH (overhead: 2% INSPYR, 5% Apple Direct, BR-007), R-BB (bill-back, BR-008). Without a matching rule the line is an exception for the Onboarding Team, never a guess.
- The request reaches the simulated Chelsea Tech only after the approver and IT have both approved the current package version (BR-012).
- The request carries no restricted fields (visa, sponsorship, FLSA).
- If this agent fails, the package gets an exception line and J1 and J2 continue.
