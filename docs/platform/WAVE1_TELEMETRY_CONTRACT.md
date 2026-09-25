# WAVE 1: Telemetry Contract

## 1. Common Operation Identity
To ensure comprehensive traceability across the system without introducing heavy distributed tracing overhead, we establish the following correlation identifiers to be propagated through requests, background jobs, and AI events:

*   **`request_id`** (UUID): The entrypoint identifier (e.g., from an HTTP request or background worker job execution).
*   **`operation_id`** (UUID): The primary durable identifier for a specific product operation (e.g., `evaluate_essay_submission_123`). This may often match the `request_id` unless a single request performs multiple distinct operations.
*   **`usage_event_id`** (UUID): The unique identifier for a specific telemetry/usage record in `AIUsage` or `usage_activities`.

**Flow**:
`User request (request_id) -> Product operation (operation_id) -> AI request -> AIUsage (usage_event_id)`

## 2. Taxonomy and Attribution

### Modules and Features
Standardized identifiers must be used when recording usage. Do not use frontend URLs for backend module attribution.

*   **Modules**: `personal_tutor`, `skill_builder`, `job_assistant`, `personal_assistant`, `platform`
*   **Features / Operations** (Examples):
    *   `module`: `personal_tutor` -> `feature`: `essay_feedback` -> `operation`: `evaluate_submission`
    *   `module`: `job_assistant` -> `feature`: `resume_review` -> `operation`: `parse_resume`

### Account and Profile
*   **`account_id`** (UUID, references `users.id`): The primary billing and identity boundary.
*   **`profile_id`** (UUID, nullable): To attribute usage to specific sub-entities without enforcing a unified profile concept.

## 3. Normalized AI Usage Schema

The existing `AIUsage` table will be additively extended to include the following conceptual schema:

```sql
-- Identifiers
id UUID PRIMARY KEY (usage_event_id)
request_id UUID
operation_id UUID

-- Attribution
account_id UUID NOT NULL REFERENCES users(id)
profile_id UUID NULL

-- Product Context
module VARCHAR(64) NOT NULL
feature VARCHAR(64) NOT NULL
operation VARCHAR(64) NOT NULL

-- Provider Details
provider VARCHAR(64) NOT NULL
model VARCHAR(64) NOT NULL

-- Metrics
input_tokens INT NOT NULL DEFAULT 0
output_tokens INT NOT NULL DEFAULT 0
total_tokens INT NOT NULL DEFAULT 0
latency_ms INT NULL

-- Financials
actual_provider_cost NUMERIC(10, 6) NULL -- NULL if unknown, do not default to 0.0 unless actually 0
cost_type VARCHAR(16) NOT NULL DEFAULT 'ACTUAL' -- 'ACTUAL', 'ESTIMATED', 'UNKNOWN'
credits_calculated INT NOT NULL
credits_charged INT NOT NULL

-- Exemptions
billing_exemption BOOLEAN NOT NULL DEFAULT FALSE
exemption_reason VARCHAR(64) NULL

-- Status
status VARCHAR(32) NOT NULL -- 'SUCCESS', 'FAILED', 'TIMEOUT', etc.

-- Time
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

## 4. Cost Attribution Rules
*   **Source of Truth**: Read usage/cost information directly from the `GatewayAIProvider` or Vercel AI Gateway response headers/metadata.
*   **No Silent Zeroes**: If cost data is missing or cannot be accurately determined, `actual_provider_cost` MUST be `NULL` (or explicitly tracked as unknown), and `cost_type` set to `UNKNOWN`. Never silently default to `0.0`.
*   **SUPER_USER Exception**: For `SUPER_USER` testing, `actual_provider_cost` MUST record the true cost incurred by Pragyan, `credits_calculated` MUST reflect the theoretical cost to the user, and `credits_charged` MUST be `0`, with `billing_exemption = TRUE` and `exemption_reason = 'SUPER_USER'`.

## 5. Operational Events

The `usage_activities` table will be leveraged for lightweight operational tracking.

Standardized Event Types:
*   `MODULE_USED`
*   `AI_REQUEST_COMPLETED`
*   `AI_REQUEST_FAILED`
*   `AUTOMATION_EXECUTED`
*   `BACKGROUND_JOB_FAILED`

Safe Metadata Categories for Errors:
*   `PROVIDER_TIMEOUT`, `PROVIDER_ERROR`, `RATE_LIMIT`, `VALIDATION_ERROR`, `INTERNAL_ERROR`, `CREDIT_ERROR`

## 6. Privacy & Data Minimization

Telemetry is strictly for operational and economic analytics. It is NOT a customer content datastore.

**PROHIBITED** from entering `AIUsage`, `usage_activities`, or standard logging JSON contexts:
*   User prompts and AI responses
*   Uploaded document contents, resumes, calendar entries, email bodies
*   OAuth tokens, API keys, refresh tokens, Stripe secrets, Clerk secrets

**ALLOWED**:
*   Module, feature, operation names
*   Token counts, latencies, cost, credits, status codes
*   Error categories

*Any JSON fields must be rigorously audited against this policy.*

## 7. Admin API Response Contracts

These API schemas define the required data structure for the secured Admin endpoints owned by Codex.

### `/api/admin/overview`
```json
{
  "period": "30_days",
  "active_accounts": 1420,
  "active_profiles": 1650,
  "ai_requests": 45000,
  "ai_failures": 120,
  "provider_cost": 450.25,
  "credits_calculated": 450000,
  "credits_charged": 445000,
  "average_latency_ms": 1250
}
```

### `/api/admin/usage` (Drill-down breakdown)
```json
{
  "by_module": [
    {
      "module": "personal_tutor",
      "ai_requests": 20000,
      "provider_cost": 200.50,
      "credits_charged": 200500
    }
  ],
  "by_provider": [
    {
      "provider": "openai",
      "model": "gpt-4o",
      "ai_requests": 40000,
      "provider_cost": 400.00
    }
  ]
}
```

## 8. Aggregation Strategy
*   Start with indexed aggregations on the `AIUsage` table using time (`created_at`), `module`, `provider`, and `account_id` indexes.
*   Time dimensions will be derived dynamically at query time (`created_at >= :start_date`) to remain dashboard-agnostic.
*   Background aggregation via the existing Arq worker queue will only be introduced if real-time query performance degrades at scale.