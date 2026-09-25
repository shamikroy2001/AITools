# System Architecture

This project is modularized into four primary areas, structurally separated to prevent code conflict and clearly define responsibilities.

## Modules

- **Codex**: Security & Finance (RBAC, Audit, Credit ledger, Admin APIs, etc.)
- **Jules**: Observability (AI usage, Cost attribution, Telemetry, etc.)
- **Antigravity**: Admin Experience (Insights, Roles, Diagnostics)
- **Cursor**: Final integration

## Architecture and Data Flow

```text
CODEX                          JULES
Security + Finance             Observability
──────────────────             ─────────────────
RBAC                           AI usage
ADMIN / SUPER_USER             Cost attribution
Credit ledger                  Operation IDs
Idempotency                    Aggregations
Audit                          Error analytics
Admin APIs                     Telemetry contract
        │                            │
        └────────────┬───────────────┘
                     ▼
                ANTIGRAVITY
               Admin Experience
                     │
            ┌────────┼────────┐
            ▼        ▼        ▼
         Insights  Roles   Diagnostics
                     │
                     ▼
                   CURSOR
              Final integration
```

Codex and Jules provide foundational security, finance, and observability services which are then utilized by Antigravity for the Admin Experience. Ultimately, Cursor handles the final integration.
