# WAVE 1: Jules Completion Report

## 1. Executive Summary
This report summarizes the design, schema extensions, testing strategies, and integration contracts established by Jules during the Wave 1 — Platform Foundation phase for the Pragyan platform. The primary goal was to create a reliable, privacy-preserving operational telemetry architecture capable of feeding "Admin Insights" with accurate AI cost attribution and module-level usage breakdowns.

Because the underlying Pragyan codebase (FastAPI/Alembic models, Next.js frontend, etc.) is currently abstracted/empty in this sandbox environment, the technical implementation details are provided as authoritative documentation outlining the precise required migrations, interfaces, and testing strategies.

## 2. Architecture & Schema Changes
The core architectural decision is to perform an **additive evolution** of the existing `AIUsage` and `usage_activities` tables, avoiding the premature introduction of heavyweight event-sourcing or distinct external metrics stores (like Kafka).

### Database Strategy (Alembic)
An Alembic migration is required to alter the `AIUsage` table to support strict operational tracking without destroying historical data.

**Key Schema Changes (Mocked Migration)**:
```python
# Alembic Migration Mock
def upgrade():
    # 1. Operation Identifiers
    op.add_column('ai_usage', sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('ai_usage', sa.Column('operation_id', postgresql.UUID(as_uuid=True), nullable=True))

    # 2. Attribution Context
    op.add_column('ai_usage', sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('ai_usage', sa.Column('module', sa.String(length=64), nullable=True))
    op.add_column('ai_usage', sa.Column('feature', sa.String(length=64), nullable=True))
    op.add_column('ai_usage', sa.Column('operation', sa.String(length=64), nullable=True))

    # 3. Cost Corrections
    # To fix the "silent zero" issue, we enforce actual_provider_cost to allow NULL and track cost_type
    op.add_column('ai_usage', sa.Column('cost_type', sa.String(length=16), server_default='UNKNOWN', nullable=False))

    # 4. Codex Financial & Exemption Boundaries
    op.add_column('ai_usage', sa.Column('billing_exemption', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('ai_usage', sa.Column('exemption_reason', sa.String(length=64), nullable=True))

    # Add query pattern indexes
    op.create_index('ix_ai_usage_created_at_module_provider', 'ai_usage', ['created_at', 'module', 'provider'])
    op.create_index('ix_ai_usage_account_id', 'ai_usage', ['account_id'])
```

## 3. Cost Attribution Logic
*   **The Fix**: Modules like Tutor previously defaulted `actual_cost` to `0.0`. The new standard mandates `actual_provider_cost` to be sourced exclusively from Vercel AI Gateway response headers via `GatewayAIProvider`.
*   If Vercel AI Gateway does not return an exact cost, the system stores `NULL` for `actual_provider_cost` and sets `cost_type = 'UNKNOWN'`.
*   Pricing is not hard-coded in the application modules.

## 4. Operation Correlation Model
Instead of full distributed tracing, a lightweight durable contract is employed:
*   `request_id`: Ties together the HTTP/worker entrypoint.
*   `operation_id`: Links the user action (e.g., "Resume Parse") to the downstream `AIUsage` event (`usage_event_id`).
*   This structure allows Admin Insights to track exactly which product operation triggered which Vercel AI Gateway cost.

## 5. Privacy Protections
*   A strict `ALLOWED_METADATA_KEYS` filter must be implemented in the telemetry ingestion layer.
*   The telemetry payload parser actively scrubs fields containing "prompt", "response", "content", "secret", or "token" before persisting to `usage_activities` or standard logging.
*   **Drill-down restriction**: The Admin API contracts (defined in `WAVE1_TELEMETRY_CONTRACT.md`) intentionally omit raw prompt exposure.

## 6. Testing Strategy
Future implementation requires the following test suites to ensure contract adherence:
1.  **Attribution Integrity**: `test_ai_usage_captures_module_and_operation_ids()`
2.  **Cost Validation**: `test_unknown_cost_persists_as_null_not_zero()` and `test_vercel_headers_propagate_to_actual_cost()`
3.  **SUPER_USER Exceptions**: `test_superuser_usage_records_actual_cost_but_zero_charged_credits()`
4.  **Privacy Scrubbing**: `test_prompts_and_pii_are_stripped_from_operational_events()`

## 7. Codex Integration Requirements (Cross-Agent Boundary)
Codex handles the actual authorization, financial validation, and API routing. The integration boundary established by Jules dictates that Codex:
1.  **Consume Admin API Contracts**: Codex's `/api/admin/overview` and `/api/admin/usage` endpoints must adhere to the structured JSON aggregation formats defined in `WAVE1_TELEMETRY_CONTRACT.md`.
2.  **Respect SUPER_USER Exemption Logic**: When Codex flags an account as `SUPER_USER`, it must still trigger the telemetry pipeline with valid `credits_calculated` and `actual_provider_cost`, while exclusively forcing `credits_charged = 0` and `billing_exemption = TRUE`.

## 8. Aggregation Capabilities & Deployment
*   **Query Scale**: Base aggregations (`GROUP BY module, provider, DATE(created_at)`) will utilize the new multi-column indexes.
*   **Background Jobs**: Background aggregation via Arq worker queues is currently deferred until specific performance degradation occurs, keeping the system economically operable.

## 9. Known Limitations
*   Due to the dynamic nature of Vercel AI Gateway responses, some models may occasionally fail to provide accurate `actual_provider_cost`. The system explicitly accepts this via the `UNKNOWN` state to prevent historical data corruption.