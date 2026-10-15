# Solution Intake - Employee Onboarding Digital Coworker

**Hackathon Duration:** Three weeks<br>**Business Owner:** Paola | Kristen | Jordan - to be confirmed<br>**Primary Users:** Hiring managers and INSPYR onboarding personnel

## 1. Business Problem

Starting an employee or contractor onboarding process requires information from the hiring manager, HR, IT and operational teams. This information is often collected through conversations, spreadsheets and manual follow-ups.

Missing or inconsistent information can delay:

- Creation of the placement or employee record.
- Approval of the onboarding request.
- Email and application access.
- Equipment ordering.
- Client or department billing decisions.
- Delivery of role, company and client information.

The opportunity is to guide the requester through a complete intake, validate the information and coordinate the actions required to prepare the new employee for their start date.

## 2. Solution Objective

Build an Employee Onboarding Digital Coworker that helps hiring managers and onboarding personnel:

- Initiate an onboarding request through a conversational interface.
- Identify and collect missing information.
- Determine the appropriate onboarding path.
- Define required equipment, email and software access.
- Produce a complete request for review and approval.
- Coordinate or simulate the approved downstream actions.

The Coworker should reduce manual follow-up while keeping HR, operational and IT decisions under human control.

## 3. Solution Vision

The Coworker should become a single entry point for starting and coordinating employee onboarding at INSPYR.

The broader vision includes:

- Guiding managers through each onboarding requirement.
- Coordinating HR, JobDiva, IT and operational activities.
- Monitoring completion before the start date.
- Identifying delays, missing approvals and unresolved dependencies.
- Providing the new employee with relevant company, client and role information.

For the hackathon, the solution should focus on the initial request and approval process rather than the complete employee onboarding lifecycle.

## 4. Hackathon MVP Scope

**Journey 1 — Onboarding Intake**

A hiring manager starts a conversation with a basic request such as:

“I want to hire John Agnitsch with a start date of October 1.”

The Coworker identifies the missing information and asks the appropriate follow-up questions. Depending on the onboarding path, these may include:

- Role and department.
- Manager.
- Start date.
- Employment or contractor type.
- Location and work arrangement.
- Compensation or billing information.
- Client assignment.
- Required email account type.
- Required applications and software.
- Equipment requirements.
- Shipping information.
- Client bill-back requirements.
- Additional onboarding instructions.

The Coworker confirms when all required information has been collected and identifies any unresolved exceptions.

**Journey 2 — Approval and Action Package**

Once the intake is complete, the Coworker creates a structured onboarding package for review.

The package should include:

- Employee or contractor information.
- Start date and assignment.
- Selected onboarding path.
- Required approvals.
- JobDiva placement or employee record information.
- Email and application access requirements.
- Equipment request.
- Billing or client bill-back considerations.
- Missing information, exceptions and risks.

An authorized person reviews the package and approves, rejects or returns it for correction.

After approval, the Coworker may create or simulate:

- A JobDiva placement or employee record.
- An IT access request.
- An equipment request.
- An onboarding task list.

**Optional Capability — New Employee Information**

If the two core journeys are complete, the Coworker may prepare a personalized onboarding information package containing:

- INSPYR company information.
- Relevant policies and resources.
- Client information.
- Role expectations.
- First-day instructions.
- Required learning materials.

## 5. Business Capabilities

| Priority | Capability | Expected Behavior |
|---|---|---|
| Must | Conversational intake | Allow a manager to start onboarding using a simple request rather than completing a complex form. |
| Must | Adaptive questioning | Ask only the questions required for the selected employee, contractor, location and assignment type. |
| Must | Completeness validation | Confirm that all mandatory information is available before submitting the request for approval. |
| Must | Onboarding path identification | Apply approved rules to identify the appropriate onboarding workflow and escalate unclear cases. |
| Must | Access identification | Determine the required email account, Teams access, Office applications and other approved systems. |
| Must | Equipment identification | Capture laptop, device, shipping and other equipment requirements. |
| Must | Billing validation | Identify potential client bill-back requirements for equipment or other onboarding costs. |
| Must | Approval package | Produce a concise summary that an authorized person can approve, reject or return for correction. |
| Must | Human control | Require approval before creating records, ordering equipment or requesting system access. |
| Should | JobDiva action | Create or simulate the creation of the approved placement or employee record. |
| Should | Provisioning requests | Create or simulate approved access and equipment requests. |
| Could | Employee information package | Prepare company, client and role information for the new employee. |
| Could | Readiness tracking | Display outstanding actions and risks before the start date. |

## 6. Digital Coworker and Agent Responsibilities

The Digital Coworker owns the onboarding request and coordinates specialized agents such as:

| Agent | Responsibility |
|---|---|
| Onboarding Orchestrator | Manages the conversation, identifies the onboarding path and coordinates the complete request. |
| Employee Information Agent | Collects and validates personal, role, manager, location, start-date and assignment information. |
| Policy and Classification Agent | Applies approved onboarding rules and identifies cases that require HR review. |
| Access and Equipment Agent | Determines email, application, equipment, shipping and potential bill-back requirements. |
| JobDiva and Workflow Agent | Prepares or creates the approved placement record and downstream requests. |
| Onboarding Content Agent | Produces the optional company, client and role information package. |

The prototype should demonstrate agents sharing context and coordinating a single onboarding outcome.

## 7. Data and Content

The Coworker may use:

**Internal sources**

- Current onboarding checklist or Smartsheet.
- JobDiva employee and placement requirements.
- Employment and contractor onboarding policies.
- Location-specific onboarding requirements.
- Email account types and access rules.
- Approved software and application catalog.
- Equipment options and shipping requirements.
- Client billing and bill-back rules.
- Company, client and role onboarding materials.

**Test environment**

The preferred option is controlled, read-only access to approved systems and content.

If system access is unavailable, the team may use:

- A realistic mock onboarding checklist.
- Synthetic employee and contractor scenarios.
- A simulated JobDiva service.
- Simulated equipment and access-request services.
- Approved sample policies and onboarding materials.

## 8. Demonstration Scenario

The final demonstration should show one connected onboarding journey:

1. A manager provides a name and proposed start date.
1. The Coworker identifies missing information.
1. Specialized agents collect and validate the required details.
1. The Coworker recommends the correct email, software and equipment requirements.
1. The Coworker identifies a potential billing or bill-back consideration.
1. A complete onboarding package is presented to an authorized approver.
1. The approver reviews and approves the request.
1. The Coworker creates or simulates the JobDiva record and required IT or equipment requests.
1. Optionally, the Coworker prepares a personalized onboarding information package.

## 9. Success Metrics

| Dimension | Hackathon Target |
|---|---|
| Core journeys | Successfully demonstrate both Intake and Approval and Action Package. |
| Information completeness | Collect 100% of the mandatory information defined for the selected test scenarios. |
| Adaptive experience | Ask questions based on the onboarding path without requesting irrelevant information. |
| Validation | Identify all predefined missing-data and exception conditions in the test scenarios. |
| Processing time | Produce an approval-ready onboarding package within five minutes after receiving the required information. |
| Human control | Require approval before every enterprise-system, access, equipment or purchasing action. |
| Traceability | Show which information, rule or user response supported each recommendation. |
| Business usefulness | Receive an average evaluation of at least 4 out of 5 from the business reviewers. |
| Multi-agent workflow | Demonstrate at least three specialized agents collaborating in the workflow. |

## 10. Governance and Guardrails

- Limit the prototype to approved synthetic or controlled employee data.
- Protect personal, compensation, client and employment information.
- Use role-based access for managers, HR, IT and approvers.
- Do not make legal employment or worker-classification decisions autonomously.
- Escalate unclear policy, classification or compensation cases.
- Require human approval before creating records or requesting access and equipment.
- Distinguish confirmed information, recommendations and unresolved exceptions.
- Log user responses, agent activity, approvals and proposed actions.
- Prevent duplicate onboarding requests and records.
- Do not place real orders or provision production access during the demonstration.

## 11. Out of Scope

- Complete redesign of INSPYR’s onboarding process.
- Generic onboarding for every company or client.
- Payroll or benefits enrollment.
- Background checks or employment eligibility verification.
- Legal worker-classification decisions.
- Autonomous equipment purchases.
- Autonomous account provisioning.
- Production deployment across all locations.
- Activities after initial onboarding readiness, such as performance management or offboarding.

## 12. Definition of Done

The MVP is complete when a hiring manager can:

- Start an onboarding request through a simple conversation.
- Receive relevant follow-up questions.
- Provide all required employee, assignment, access and equipment information.
- Receive a validated onboarding summary.
- Submit the package for human approval.
- Create or simulate the approved JobDiva and provisioning actions.
- Review the sources, rules, approvals and exceptions behind the workflow.

**Question the prototype must answer:** Can the Coworker collect everything INSPYR needs to onboard a person and turn it into an approved, actionable request?
