from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from insurance_data_layer.adapters.base import SourceAdapter, register, slug, stable_key
from insurance_data_layer.models import (
    ApplicantRisk,
    BenefitRule,
    CanonicalRecord,
    CoverageStatus,
    DurationRule,
    ExcessRule,
    Frequency,
    InsuranceType,
    LimitRule,
    MappingStatus,
    Money,
    PetRisk,
    Plan,
    Premium,
    Product,
    Provenance,
    Provider,
    QualityIssue,
    QuoteRequest,
)

MONEY_FEATURES = {
    "Commercial, part-time (annual turnover)": ("commercial_use_turnover", "annual_threshold"),
    "Replacement cost compensation for damaged items": ("replacement_cost", "benefit_sublimit"),
    "Additional benefits for sustainable damage compensation": (
        "sustainable_damage_compensation",
        "benefit_sublimit",
    ),
    "Damage to rented immovable property (land, buildings)": (
        "rented_immovable_property_damage",
        "benefit_sublimit",
    ),
    "Damage to movable property in holiday accommodations": (
        "holiday_accommodation_movables",
        "benefit_sublimit",
    ),
    "Dog transport trailers/boxes": ("dog_transport_equipment", "benefit_sublimit"),
    "Minimum damage amount": ("minimum_damage_amount", "claim_threshold"),
    "Enforcement of legal claims (cost coverage)": (
        "legal_claim_enforcement_costs",
        "benefit_sublimit",
    ),
    "Victim protection: injury by stranger's dog": ("victim_protection", "benefit_sublimit"),
    "Vet costs for own dog if injured by another dog": (
        "own_dog_vet_costs_third_party_dog",
        "benefit_sublimit",
    ),
}

DURATION_FEATURES = {
    "Puppies covered up to": "puppy_coverage",
    "Damages abroad - within Europe": "territory_europe",
    "Damages abroad - outside Europe": "territory_outside_europe",
}


def parse_duration(value: str) -> tuple[int | None, str | None, bool]:
    if value.casefold() == "unlimited":
        return None, None, True
    match = re.fullmatch(r"(\d+)\s+(day|days|month|months|year|years)", value.casefold())
    if not match:
        raise ValueError(f"Unsupported duration: {value}")
    return int(match.group(1)), match.group(2).removesuffix("s"), False


@register
class HanseMerkurAdapter(SourceAdapter):
    source_site = "hansemerkur.de"

    def adapt(self, raw: dict[str, Any], raw_file: str) -> CanonicalRecord:
        source_input = raw["input"]
        output = raw["output"]
        observed_at = datetime.fromisoformat(output["scraped_at"])
        plan_name = output["package_name"]
        plan_code = slug(plan_name)
        request_key = stable_key("qr", {"site": self.source_site, "input": source_input})
        version_key = stable_key(
            "pv",
            {
                "provider": "hansemerkur",
                "plan": plan_code,
                "observed_date": observed_at.date(),
            },
        )
        currency = output["premium_currency"]
        rules = [
            LimitRule(
                benefit_code="third_party_liability",
                amount=Money(amount=output["coverage_amount"], currency=currency),
                scope="overall",
            ),
            ExcessRule(
                amount=Money(amount=output["excess_amount"], currency=currency),
                scope="unknown",
                mapping_status=MappingStatus.AMBIGUOUS,
            ),
        ]
        issues = [
            QualityIssue(
                code="ambiguous_premium_relationship",
                field="output.premium_annual",
                message="Monthly and annual values are preserved; their relationship is not assumed.",
            ),
            QualityIssue(
                code="ambiguous_excess_scope",
                field="output.excess_amount",
                message="The source does not prove the excess application scope.",
            ),
        ]

        for feature in output.get("features", []):
            label = feature["feature"]
            value = feature.get(plan_name)
            if label.startswith("label."):
                issues.append(
                    QualityIssue(
                        code="localisation_key",
                        field="output.features",
                        message=f"Ignored untranslated UI key: {label}",
                    )
                )
                continue
            if label in MONEY_FEATURES:
                benefit_code, scope = MONEY_FEATURES[label]
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    rules.append(
                        LimitRule(
                            benefit_code=benefit_code,
                            amount=Money(amount=value, currency=currency),
                            scope=scope,
                            mapping_status=MappingStatus.INFERRED,
                        )
                    )
                else:
                    status = (
                        CoverageStatus.EXCLUDED
                        if value is False
                        else CoverageStatus.INCLUDED
                        if value == "none"
                        else CoverageStatus.UNKNOWN
                    )
                    rules.append(
                        BenefitRule(
                            benefit_code=benefit_code,
                            label=label,
                            status=status,
                            mapping_status=MappingStatus.INFERRED,
                        )
                    )
                continue
            if label in DURATION_FEATURES and isinstance(value, str):
                duration_value, duration_unit, unlimited = parse_duration(value)
                rules.append(
                    DurationRule(
                        benefit_code=DURATION_FEATURES[label],
                        duration_value=duration_value,
                        duration_unit=duration_unit,
                        unlimited=unlimited,
                    )
                )
                continue
            if isinstance(value, bool):
                rules.append(
                    BenefitRule(
                        benefit_code=slug(label),
                        label=label,
                        status=(CoverageStatus.INCLUDED if value else CoverageStatus.EXCLUDED),
                        mapping_status=MappingStatus.INFERRED,
                    )
                )
            else:
                issues.append(
                    QualityIssue(
                        code="unmapped_feature",
                        field="output.features",
                        message=f"No safe mapping for {label!r} with value {value!r}.",
                    )
                )

        premiums = [
            Premium(
                amount=output["premium_amount"],
                currency=currency,
                frequency=Frequency.MONTH,
                source_label="premium_amount",
            )
        ]
        if output.get("premium_annual") is not None:
            premiums.append(
                Premium(
                    amount=output["premium_annual"],
                    currency=currency,
                    frequency=Frequency.YEAR,
                    source_label="premium_annual",
                    mapping_status=MappingStatus.AMBIGUOUS,
                )
            )

        return CanonicalRecord(
            canonical_record_key=stable_key(
                "cr", {"request": request_key, "plan": plan_code, "source_id": output["id"]}
            ),
            provider=Provider(code="hansemerkur", name=output["provider_name"]),
            product=Product(
                code="hansemerkur_dog_liability_de",
                name="Dog owner liability insurance",
                insurance_type=InsuranceType.PET_LIABILITY,
                market_country="DE",
            ),
            plan=Plan(code=plan_code, name=plan_name, version_key=version_key),
            quote_request=QuoteRequest(
                request_key=request_key,
                pet=PetRisk(species="dog", name=source_input.get("dog_name"), breed=source_input.get("breed")),
                applicant=ApplicantRisk(
                    date_of_birth=source_input.get("owner_dob"),
                    had_prior_damage=source_input.get("had_prior_damage"),
                    had_prior_insurance=source_input.get("had_prior_insurance"),
                ),
                requested_effective_date=source_input.get("start_date"),
                submitted_at=source_input.get("created_at"),
            ),
            premiums=premiums,
            rules=rules,
            provenance=Provenance(
                source_site=output["source_site"],
                source_url=output["quote_url"],
                observed_at=observed_at,
                source_record_id=output.get("id"),
                scraper_status=output.get("scrape_status"),
                raw_file=raw_file,
                adapter_name=self.__class__.__name__,
                adapter_version=self.adapter_version,
            ),
            quality_issues=issues,
        )
