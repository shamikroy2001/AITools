import pytest
import uuid
from app.models.ai_usage import AIUsage

def test_ai_usage_instantiation_without_cost_defaults_to_unknown():
    # Simulate saving usage when Vercel API Gateway doesn't return exact cost
    usage = AIUsage(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        module="personal_tutor",
        feature="essay_feedback",
        operation="evaluate_submission",
        provider="openai",
        model="gpt-4o",
        credits_calculated=100,
        credits_charged=100,
        status="SUCCESS",
        # intentionally leaving actual_provider_cost unset
    )

    # Asserting that cost_type defaults to UNKNOWN and cost is None,
    # ensuring we do not silently track 0.0
    assert usage.cost_type == "UNKNOWN"
    assert usage.actual_provider_cost is None

def test_superuser_exemption_contract():
    # Simulate Codex indicating a SUPER_USER exemption
    usage = AIUsage(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        module="personal_tutor",
        feature="essay_feedback",
        operation="evaluate_submission",
        provider="openai",
        model="gpt-4o",
        actual_provider_cost=0.015, # Actual cost incurred by Pragyan
        cost_type="ACTUAL",
        credits_calculated=150, # What they would have been charged
        credits_charged=0,      # What they were actually charged
        billing_exemption=True,
        exemption_reason="SUPER_USER",
        status="SUCCESS"
    )

    assert usage.billing_exemption is True
    assert usage.credits_charged == 0
    assert usage.actual_provider_cost == 0.015
    assert usage.credits_calculated == 150
