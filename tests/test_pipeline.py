from decimal import Decimal
from pathlib import Path

from insurance_data_layer.models import (
    DurationRule,
    LimitRule,
    ReimbursementRule,
    TerritoryRule,
    WaitingPeriodRule,
)
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

    assert light.schema_version == "1.1"
    assert light.quote_option.option_key.startswith("qo_")

    reimbursement = next(
        rule
        for rule in light.rules
        if isinstance(rule, ReimbursementRule)
    )
    assert reimbursement.rate == Decimal("0.6")
    assert reimbursement.source_evidence.field == "output.coverage_amount"
    assert reimbursement.source_evidence.raw_value == 60

    annual_limit = next(
        rule
        for rule in light.rules
        if (
            isinstance(rule, LimitRule)
            and rule.benefit_code == "accident_and_illness"
        )
    )
    assert annual_limit.amount is not None
    assert annual_limit.amount.amount == Decimal(1500)
    assert annual_limit.scope == "policy_year"
    assert annual_limit.source_evidence.raw_label == "accidentIllness"

    waiting_rules = [
        rule
        for rule in light.rules
        if isinstance(rule, WaitingPeriodRule)
    ]
    assert waiting_rules
    assert all(rule.eligible_from is None for rule in waiting_rules)
    assert all(
        rule.starts_from == "policy_effective_date"
        for rule in waiting_rules
    )

    assert all(rule.source_evidence for rule in light.rules)

    assert any(
        issue.code == "unverified_waiting_period_start_date"
        for issue in light.quality_issues
    )


def test_hansemerkur_file_preserves_both_premiums_and_liability_limit():
    records, report = transform_file(
        ROOT / "data_vault/raw/hansemerkur/2026-07-28_quotes.json"
    )

    assert report["input_records"] == 100
    assert report["invalid_records"] == 0
    assert report["unique_quote_requests"] == 50

    komfort = records[0]

    assert komfort.schema_version == "1.1"
    assert komfort.quote_option.option_key.startswith("qo_")

    assert [
        premium.frequency.value
        for premium in komfort.premiums
    ] == ["month", "year"]

    overall = next(
        rule
        for rule in komfort.rules
        if (
            isinstance(rule, LimitRule)
            and rule.benefit_code == "third_party_liability"
        )
    )
    assert overall.amount is not None
    assert overall.amount.amount == Decimal(15000000)
    assert overall.source_evidence.field == "output.coverage_amount"

    assert not any(
        "tarifinformationen"
        in (getattr(rule, "benefit_code", None) or "")
        for rule in komfort.rules
    )

    assert all(rule.source_evidence for rule in komfort.rules)


def test_hansemerkur_models_geography_as_territory_rules():
    records, _ = transform_file(
        ROOT / "data_vault/raw/hansemerkur/2026-07-28_quotes.json"
    )

    komfort = records[0]

    territory_rules = [
        rule
        for rule in komfort.rules
        if isinstance(rule, TerritoryRule)
    ]

    assert territory_rules
    assert {
        rule.territory_code
        for rule in territory_rules
    } == {"europe", "outside_europe"}

    assert not any(
        isinstance(rule, DurationRule)
        and rule.benefit_code in {
            "territory_europe",
            "territory_outside_europe",
        }
        for rule in komfort.rules
    )

    europe = next(
        rule
        for rule in territory_rules
        if rule.territory_code == "europe"
    )

    if europe.unlimited_duration:
        assert europe.maximum_duration is None
    else:
        assert europe.maximum_duration is not None


def test_request_keys_are_stable_across_options():
    records, _ = transform_file(
        ROOT / "data_vault/raw/hansemerkur/2026-07-28_quotes.json"
    )

    assert (
        records[0].quote_request.request_key
        == records[1].quote_request.request_key
    )
    assert records[0].plan.code != records[1].plan.code
    assert (
        records[0].quote_option.option_key
        != records[1].quote_option.option_key
    )


def test_option_keys_are_deterministic_across_repeated_transforms():
    path = ROOT / "data_vault/raw/hansemerkur/2026-07-28_quotes.json"

    first_records, _ = transform_file(path)
    second_records, _ = transform_file(path)

    assert [
        record.quote_option.option_key
        for record in first_records
    ] == [
        record.quote_option.option_key
        for record in second_records
    ]


def test_raw_file_paths_use_forward_slashes():
    path = ROOT / "data_vault/raw/santevet/2026-07-28_quotes.json"

    records, report = transform_file(path)

    assert "\\" not in report["raw_file"]
    assert report["raw_file"].endswith(
        "data_vault/raw/santevet/2026-07-28_quotes.json"
    )
    assert records[0].provenance.raw_file == report["raw_file"]