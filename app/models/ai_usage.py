from sqlalchemy import Column, String, Integer, Boolean, Numeric, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AIUsage(Base):
    __tablename__ = "ai_usage"

    # Core Identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, comment="usage_event_id")
    request_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    operation_id = Column(UUID(as_uuid=True), index=True, nullable=True)

    # Attribution Context
    account_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(UUID(as_uuid=True), nullable=True)

    module = Column(String(64), nullable=False)
    feature = Column(String(64), nullable=False)
    operation = Column(String(64), nullable=False)

    # Provider Context
    provider = Column(String(64), nullable=False)
    model = Column(String(64), nullable=False)

    # Metrics
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, nullable=True)

    # Financials
    # actual_provider_cost CANNOT default to 0.0, use cost_type
    actual_provider_cost = Column(Numeric(10, 6), nullable=True)
    cost_type = Column(String(16), default='UNKNOWN', nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'cost_type' not in kwargs:
            self.cost_type = 'UNKNOWN'
        if 'billing_exemption' not in kwargs:
            self.billing_exemption = False

    credits_calculated = Column(Integer, nullable=False)
    credits_charged = Column(Integer, nullable=False)

    # Exemptions
    billing_exemption = Column(Boolean, default=False, nullable=False)
    exemption_reason = Column(String(64), nullable=True)

    # Status
    status = Column(String(32), nullable=False)

    # Timestamp
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
