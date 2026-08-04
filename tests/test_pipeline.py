from decimal import Decimal
from pathlib import Path

from insurance_data_layer.models import LimitRule, ReimbursementRule
from insurance_data_layer.pipeline import transform_file

ROOT = Path(__file__).parents[1]


def test_santevet_file_transforms_and_deduplicates_requests():
    records, report = transform_file(
        ROOT / "data_vault/raw/santevet/2026-07-28_quotes.json"
    )
    assert report["input_records"] == 29
    assert report["invalid_records"] == 0
    assert report["unique_quote_requests"] == 6
    light = records[0]
    reimbursement = next(r for r in light.rules if isinstance(r, ReimbursementRule))
    assert reimbursement.rate == Decimal("0.6")
    annual_limit = next(
        r
        for r in light.rules
        if isinstance(r, LimitRule) and r.benefit_code == "accident_and_illness"
    )
    assert annual_limit.amount.amount == Decimal(1500)
    assert annual_limit.scope == "policy_year"


def test_hansemerkur_file_preserves_both_premiums_and_liability_limit():
    records, report = transform_file(
        ROOT / "data_vault/raw/hansemerkur/2026-07-28_quotes.json"
    )
    assert report["input_records"] == 100
    assert report["invalid_records"] == 0
    assert report["unique_quote_requests"] == 50
    komfort = records[0]
    assert [premium.frequency.value for premium in komfort.premiums] == ["month", "year"]
    overall = next(
        r
        for r in komfort.rules
        if isinstance(r, LimitRule) and r.benefit_code == "third_party_liability"
    )
    assert overall.amount.amount == Decimal(15000000)
    assert not any(
        "tarifinformationen" in (getattr(r, "benefit_code", None) or "")
        for r in komfort.rules
    )


def test_request_keys_are_stable_across_options():
    records, _ = transform_file(
        ROOT / "data_vault/raw/hansemerkur/2026-07-28_quotes.json"
    )
    assert records[0].quote_request.request_key == records[1].quote_request.request_key
    assert records[0].plan.code != records[1].plan.code
