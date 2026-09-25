# WAVE 1: Jules Telemetry Assessment

## Overview
This assessment reviews the existing Pragyan platform's operational telemetry, AI cost attribution, and usage tracking capabilities as part of Wave 1 - Platform Foundation. The primary objective is to evaluate current gaps in answering key operational questions regarding AI costs, module attribution, and resource usage without compromising customer privacy.

## Existing Architecture Review
Pragyan currently utilizes:
- Next.js 15 / React 19 frontend
- FastAPI backend
- Arq worker + Redis
- PostgreSQL/Supabase with SQLAlchemy async and Alembic
- Clerk (auth) & Stripe (billing)
- Vercel AI Gateway, AIRouter, GatewayAIProvider
- Core domain entities: `AIUsage`, `CreditService`, `usage_activities`, `AuditService`

**Current State**:
- `AIRouter` selects AI policy/model.
- `GatewayAIProvider` interfaces with Vercel AI Gateway.
- Codex manages RBAC, authorization, financial correctness (`CreditService`), `SUPER_USER` billing exemptions, and audit frameworks.

## Identified Telemetry & Attribution Gaps

### 1. Incomplete Cost Attribution
- **Known Issue**: The Tutor module currently records `actual_cost` as `0.0` in `AIUsage` in at least one execution path. This results in incomplete and inaccurate provider-cost aggregates.
- **Risk**: Other modules (Skill Builder, Job Assistant, Personal Assistant, background workers) may similarly fail to record accurate provider costs or silently represent unknown/estimated costs as exactly `0.0`.
- **Finding**: Actual cost attribution from `GatewayAIProvider` responses is not consistently propagated down to the persistence layer.

### 2. Missing Module and Feature Context
- AI calls from product modules currently lack standardized attribution to trace operations back to specific product surfaces.
- **Missing Link**: There is no durable operation identifier (`operation_id` or `request_id`) clearly linking:
  `User request -> Product operation -> AI Request -> AIUsage -> Credit Settlement`
- Usage events are not cleanly categorized into `module` -> `feature` -> `operation`.

### 3. Profile Semantic Ambiguity
- The platform uses generic account identifiers (`users.id`), but lacks consistent attribution for optional profile models (e.g., Tutor profiles vs. standard learner profiles).
- Telemetry events must map seamlessly to an `account_id` with an optional, nullable `profile_id` without forcing a universal profile redesign.

### 4. Operational Event Fragmentation
- Standard operational events (e.g., `MODULE_USED`, `AI_REQUEST_COMPLETED`, `AI_REQUEST_FAILED`) are either missing, siloed in application logs, or inconsistently tracked in `usage_activities`.
- Error analytics lack normalized categories (e.g., `PROVIDER_TIMEOUT`, `RATE_LIMIT`), making it difficult to monitor the health of specific AI flows.

### 5. Privacy Risks in Event Payloads
- Without a strict telemetry contract, arbitrary metadata or error logging risks persisting customer content (prompts, AI responses, emails, documents) or sensitive secrets (OAuth tokens, API keys) into long-term operational analytics storage.

### 6. SUPER_USER Attribution Mismatch
- While `SUPER_USER` usage is exempt from billing (managed by Codex), telemetry must accurately reflect the real provider cost and calculated credits (even if `credits_charged` = 0) to evaluate internal testing/support costs.

## Conclusion and Next Steps
The existing architecture has the right primitives (`AIUsage`, `usage_activities`, `AIRouter`) but lacks a unified, privacy-safe correlation model and strict cost/module attribution contracts.

To resolve these gaps, the next step is to design a formal telemetry contract (`WAVE1_TELEMETRY_CONTRACT.md`) that extends the `AIUsage` schema, standardizes module taxonomy, defines operational event identities, and explicitly prevents customer content ingestion into telemetry databases.
