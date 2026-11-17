# EasyTicket v3 - Technical Documentation

## 1. Overview
EasyTicket v3 is a Gradio-based self-serve portal for Databricks resource provisioning with built-in approval routing and request history tracking.

The system supports:
- Create User
- Add Existing User to Group
- Create Group
- Request History (My requests, Pending requests, Approved/Denied requests)
- Request History filtering and pagination (10 rows/page)

Core design goals:
- Enforce policy-driven approvals when requester is not authorized.
- Keep an auditable request-history trail for both auto-approved and manually approved flows.
- Submit final approved payloads as ticket JSON files into Databricks storage.

## 2. Architecture
### 2.1 Layers
- UI Layer: Gradio layout/components and event bindings.
- Handler Layer: Form flow orchestration, preview validation, history interactions, approval actions.
- Service Layer: Databricks API/SQL integrations, ticket persistence.
- Domain Models: Typed request objects for user/group operations.
- Utility Layer: Validation helpers and requestor extraction.
- Test Layer: Unit tests for normalization, mapping, validation, and history contracts.

### 2.2 Request Lifecycle
1. User selects request type and action.
2. Form inputs are captured and normalized into a structured request context.
3. Validation executes:
   - Required fields
   - Email policy checks
   - Group owner checks
   - Approval routing rules
4. Preview appears.
5. Submission path:
   - Direct path: operation executes and request-history is stored as Approved.
   - Approval path: row stored as Pending for approver action.
6. Approver reviews from Request History > Pending requests.
7. On approval, status updates to Approved and actual ticket is executed.

## 3. Module-by-Module Reference

## 3.1 Application Entry
### easyticket-v3/app.py
- main()
  - Purpose: application entrypoint.
  - Behavior: calls create_ui(), launches Gradio app.

## 3.2 Configuration
### easyticket-v3/config/settings.py
- Global constants:
  - APP_NAME, APP_DESCRIPTION, ENV
  - Databricks credentials and host values
  - DATABRICKS_SQL_HTTP_PATH for SQL warehouse
  - STORAGE_BASE_PATH for JSON ticket persistence
- Logging bootstrapping for the process.

### easyticket-v3/config/operations.py
- OPERATIONS (configuration registry)
  - Purpose: declarative source of truth for supported actions, fields, models, and form rendering.
  - Used by UI builder and handlers for dynamic mapping and validation.

## 3.3 Domain Models
### easyticket-v3/models/requests.py
- BaseRequest
  - username
- DBXUserRequest
  - action, email, group, description
- DBXGroupRequest
  - action, group_name, group_owner, description, entitlements, workspace

These models provide typed payload contracts passed into the ticket service.

## 3.4 UI Modules
### easyticket-v3/ui/form_builder.py
- build_field(field)
  - Purpose: build Gradio component from field config.
- build_operation_form(operation)
  - Purpose: construct operation form container, fields map, and error component map.

### easyticket-v3/ui/layout.py
- create_ui()
  - Purpose: compose all Gradio components and wire shared component registry.
  - Key states:
    - approval_mode: flag for approval flow display state.
    - request_context_state: structured request context used by confirm handlers.
    - history_page_my/history_page_pending/history_page_approved: per-tab pagination state.
  - History controls:
    - requestor filter
    - action filter
    - request status filter
    - ticket id filter
    - reset filters, previous page, next page, and page info indicator
  - UX behavior:
    - filter and pagination controls are hidden until a history tab is selected.
  - Invokes setup_handlers(components).

## 3.5 Handler Modules
### easyticket-v3/handlers/form_handler.py
Primary orchestration module for UI behavior and business flow.

Major responsibilities:
- Dynamic action/form visibility switching.
- Dynamic dropdown loading and username propagation.
- Request history loading, filtering, and pagination.
- Preview building and validation invocation.
- Direct submit and approval submit handling.
- Approver decision processing and post-decision ticket execution.

Key internal callbacks:
- update_actions(req_type): request type to action/table visibility mapping.
- toggle_forms(action): show selected operation form.
- load_dynamic_choices_for_action(action, username): hydrate source-backed fields.
- load_history(...): render history tables with requestor/action/date/ticket filters and page slicing.
- process_decision(...): approve/deny and execute payload when approved.
- build_preview(action, ...): maps values, validates, builds preview, stores request context.
- submit_request_context(context): executes operation and writes auto-approved history row.
- handle_confirmation(context): routes to direct submit or pending approval insert.

### easyticket-v3/handlers/constants.py
- PLATFORM_APPROVERS
  - Static platform-team approver list for create-group policy routing.

### easyticket-v3/handlers/status.py
- RequestStatus enum
  - Pending, Approved, Denied
- normalize_status(value, default)
  - Purpose: canonical title-case status normalization for DB writes and filters.

### easyticket-v3/handlers/payload_mapper.py
- build_operation_lookup(operations)
- build_action_field_names(operations)
- extract_action_payload(operations, action, all_values)
- merge_saved_data(data, saved_data)
- build_preview_json(operation, data)

Purpose:
- Decouple payload extraction from callback wiring.
- Remove fragile manual slicing scattered across submit code.

### easyticket-v3/handlers/history_utils.py
- HEADERS_ALL, HEADERS_PENDING
- make_rows(rows, headers)
- can_user_approve(row, user_email)
- filter_history_rows(view, data, username)

Purpose:
- Enforce table row/header contract consistency.
- Support multi-approver values in comma-separated approver fields.

### easyticket-v3/handlers/validation.py
- validate_operation_request(...)

Purpose:
- Centralized validation and approval-routing policy.

Checks included:
- Required fields
- Email format/domain policy
- Create-group name rule: 1-128 chars, allowed set [A-Za-z0-9_.-]
- Group owner existence and ownership authorization
- Group owner required for create_group
- Group owner user existence in Databricks workspace
- Approval routing:
  - create_group always requires platform approval
  - create_user/add_user_to_group require approval when requester is not group owner

## 3.6 Services
### easyticket-v3/services/auth_service.py
- AuthService.generate_databricks_token()
  - Requests OAuth token from Databricks accounts endpoint.

### easyticket-v3/services/databricks_service.py
Core Databricks integration service.

Functions:
- upload_json_to_databricks(json_data, target_path)
  - Upload final ticket JSON into Databricks filesystem.
- fetch_dbx_request_history(username)
  - Query approval table rows where user is requestor or approver.
- update_approval_request(ticket_id, request_status, approver_comments, approver)
  - Update status/comments/approver on approval action.
- fetch_request_by_ticket(ticket_id)
  - Read one request row for payload execution.
- fetch_dbx_workspace_groups()
  - Fetch SCIM groups.
- fetch_group_owner(group_name)
  - Read owner from metadata.users.group_owners.
- log_approval_request(...)
  - Insert approval/audit row in approval table.
  - request_status is normalized by normalize_status().
- fetch_dbx_workspace_users()
  - Fetch SCIM users.

### easyticket-v3/services/ticket_service.py
- TicketService.process_dbx_user_request(request)
- TicketService.process_dbx_group_request(request)

Purpose:
- Convert model request objects into ticket payload schema and call ticket storage.

### easyticket-v3/services/ticket_storage.py
- TicketStorage.generate_ticket_id()
- TicketStorage.generate_timestamp()
- TicketStorage.store_ticket(ticket_data)

Purpose:
- Attach metadata (ticket_id, timestamp), persist JSON to Databricks storage path.

### easyticket-v3/services/dbx/dbx_ticket_service.py
- prepare_ticket_data(system, username, action, additional_data)
  - Lightweight payload assembler used by ticket service.

## 3.7 Utilities
### easyticket-v3/utils/tools.py
- extract_email(request)
  - Extracts requestor identity from x-forwarded-email, defaults to demo@hp.com.

### easyticket-v3/utils/validators.py
- validate_email(email, domain="hp.com")
  - Regex + domain policy validation.

## 4. Approval and Request-History Rules
### 4.1 Create User
- If requester is group owner: operation executes directly.
- A request-history row is inserted with status Approved and approver=requester.
- If requester is not group owner: preview shows owner warning and Send for Approval.

### 4.2 Add Existing User to Group
- Same owner-based approval behavior as create_user.

### 4.3 Create Group
- Always approval-routed.
- Preview displays platform-team approval notice.
- Approver list is platform-team emails.
- Group name validation enforces 1-128 chars with letters, digits, dot, underscore, and hyphen only.
- Group owner is mandatory and must exist in Databricks workspace users.

### 4.4 Pending Approval Experience
- Pending requests include rows where current user appears in approver list.
- Approver can approve/deny with comments.
- Approved action triggers actual provisioning request execution.

### 4.5 Request History Filters and Pagination
- Filters apply to all three tabs:
  - Requestor (contains, case-insensitive)
  - Action (exact action match)
  - Request status (Pending/Approved/Denied)
  - Ticket ID (contains, case-insensitive)
- Pagination is enabled at 10 entries per page with Previous/Next controls.
- Paging state is maintained per tab (My, Pending, Approved/Denied).
- Changing filters or tab resets paging to page 1 for deterministic UX.
- Filter and pagination controls are rendered only after the user selects one of the history tabs.

## 5. Data Contracts
### 5.1 request_context_state
Structured state object created at preview time:
- action: selected operation action
- username: requestor identity
- data: mapped form payload
- is_approval: routing flag
- approver: owner or platform-team string

This object replaces fragile positional argument parsing in confirm/approval callbacks.

### 5.2 Approval Table Fields
Expected fields in sandbox_test.platform_support.easyticket_approval_requests_table:
- ticket_id
- requestor
- request_type
- description
- payload
- event_time
- request_status
- approver
- approver_comments
- created_at
- updated_at

## 6. Testing
Tests are located in tests/ and run with:

python -m unittest discover -s tests -p "test_*.py"

Current test coverage:
- test_status.py
  - status normalization behavior
- test_payload_mapper.py
  - operation payload extraction and merge behavior
- test_history_contracts.py
  - row shape contracts and multi-approver filtering
- test_validation.py
  - approval routing, create-group owner requirement, and blocking/non-blocking validation behavior

## 7. Refactor Summary (Implemented)
1. Split handler logic into dedicated modules.
2. Replaced fragile positional confirm parsing with structured request context state.
3. Centralized validation and approval routing rules.
4. Added unit tests for critical contracts.
5. Added typed status enum + normalization for consistent DB status values.

## 8. Operational Notes
- If Gradio imports fail in static analysis, verify environment dependencies are installed.
- Databricks SQL path and OAuth credentials must be valid for history/owner checks.
- request_status filters are case-insensitive in UI; writes are normalized to title-case.

## 9. Suggested Next Improvements
- Add integration tests for full preview -> submit -> history lifecycle.
- Move raw SQL string building to parameterized helpers where available.
- Add pagination/filtering for large request-history datasets.
- Add retry and timeout policies around external API calls.
