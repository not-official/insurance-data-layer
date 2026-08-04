from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from insurance_data_layer.adapters.base import SourceAdapter, register, slug, stable_key
from insurance_data_layer.models import (
    ApplicantRisk,
    CanonicalRecord,
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
    QuoteOption,
    QuoteRequest,
    ReimbursementRule,
    SourceEvidence,
    WaitingPeriodRule,
)


@register
class SantevetAdapter(SourceAdapter):
    source_site = "santevet.com"

    def adapt(self, raw: dict[str, Any], raw_file: str) -> CanonicalRecord:
        source_input = raw["input"]
        output = raw["output"]

        observed_at = datetime.fromisoformat(output["scraped_at"])
        plan_code = slug(output["package_code"])

        request_key = stable_key(
            "qr",
            {
                "site": self.source_site,
                "input": source_input,
            },
        )

        version_key = stable_key(
            "pv",
            {
                "provider": "santevet",
                "plan": plan_code,
                "observed_date": observed_at.date(),
            },
        )

        option_key = stable_key(
            "qo",
            {
                "request": request_key,
                "plan_version": version_key,
                "source_id": output["id"],
            },
        )

        currency = output["premium_currency"]
        limits = output.get("features", {}).get("coverage_limits", {})
        waiting = output.get("features", {}).get("waiting_periods", {})

        rules = [
            ReimbursementRule(
                benefit_code="accident_and_illness",
                rate=Decimal(str(output["coverage_amount"])) / Decimal(100),
                source_evidence=SourceEvidence(
                    field="output.coverage_amount",
                    raw_label="coverage_amount",
                    raw_value=output["coverage_amount"],
                    source_language="fr",
                ),
            ),
            ExcessRule(
                amount=Money(
                    amount=output["excess_amount"],
                    currency=currency,
                ),
                scope="unknown",
                mapping_status=MappingStatus.AMBIGUOUS,
                source_evidence=SourceEvidence(
                    field="output.excess_amount",
                    raw_label="excess_amount",
                    raw_value=output["excess_amount"],
                    source_language="fr",
                ),
            ),
        ]

        benefit_map = {
            "accidentIllness": "accident_and_illness",
            "accident": "accident",
            "illness": "illness",
            "prevention": "preventive_care",
            "therapeuticNutrition": "therapeutic_nutrition",
        }

        for source_name, benefit_code in benefit_map.items():
            amount = limits.get(source_name)

            if amount is not None and amount > 0:
                rules.append(
                    LimitRule(
                        benefit_code=benefit_code,
                        amount=Money(
                            amount=amount,
                            currency=currency,
                        ),
                        scope="policy_year",
                        source_evidence=SourceEvidence(
                            field=(
                                "output.features.coverage_limits."
                                f"{source_name}"
                            ),
                            raw_label=source_name,
                            raw_value=amount,
                            source_language="fr",
                        ),
                    )
                )

        waiting_map = {
            "waitingPeriodAccident": "accident",
            "waitingPeriodIllness": "illness",
            "waitingPeriodSurgery": "surgery",
        }

        for source_name, benefit_code in waiting_map.items():
            value = waiting.get(source_name)

            if value:
                rules.append(
                    WaitingPeriodRule(
                        benefit_code=benefit_code,
                        duration_value=value["value"],
                        duration_unit=value["granularity"].removesuffix("s"),
                        # The source does not provide a verified policy effective
                        # date, so a calendar eligibility date is not asserted.
                        eligible_from=None,
                        starts_from="policy_effective_date",
                        source_evidence=SourceEvidence(
                            field=(
                                "output.features.waiting_periods."
                                f"{source_name}"
                            ),
                            raw_label=source_name,
                            raw_value=value,
                            source_language="fr",
                        ),
                    )
                )

        issues = [
            QualityIssue(
                code="ambiguous_excess_scope",
                field="output.excess_amount",
                message=(
                    "The source does not prove whether excess is annual, "
                    "per claim, or per incident."
                ),
            ),
            QualityIssue(
                code="untrusted_source_pet_id",
                field="output.pet_id",
                message=(
                    "Source pet_id varies across plan options; a "
                    "deterministic request key was generated."
                ),
                severity="info",
            ),
            QualityIssue(
                code="unverified_waiting_period_start_date",
                field="output.features.waiting_periods",
                message=(
                    "Waiting-period durations are preserved, but eligible_from "
                    "is omitted because the policy effective date is not verified."
                ),
                severity="info",
            ),
        ]

        record_key = stable_key(
            "cr",
            {
                "request": request_key,
                "plan": plan_code,
                "source_id": output["id"],
            },
        )

        return CanonicalRecord(
            canonical_record_key=record_key,
            provider=Provider(
                code="santevet",
                name=output["provider_name"],
            ),
            product=Product(
                code="santevet_pet_health_fr",
                name="Pet health insurance",
                insurance_type=InsuranceType.PET_HEALTH,
                market_country=output.get(
                    "insurance_metadata",
                    {},
                ).get("country_code"),
            ),
            plan=Plan(
                code=plan_code,
                name=output["package_name"],
                version_key=version_key,
            ),
            quote_request=QuoteRequest(
                request_key=request_key,
                pet=PetRisk(
                    species={
                        "CHAT": "cat",
                        "CHIEN": "dog",
                    }.get(
                        source_input["species"],
                        source_input["species"].lower(),
                    ),
                    name=source_input.get("animal_name"),
                    breed=source_input.get("breed"),
                    date_of_birth=source_input.get("birth_day"),
                    sex=source_input.get("gender", "unknown").lower(),
                    is_cross_breed=source_input.get("is_cross_breed"),
                    is_indoor=source_input.get("is_indoor"),
                ),
                applicant=ApplicantRisk(
                    postcode=source_input.get("city"),
                ),
                submitted_at=source_input.get("created_at"),
            ),
            quote_option=QuoteOption(
                option_key=option_key,
            ),
            premiums=[
                Premium(
                    amount=output["premium_amount"],
                    currency=currency,
                    frequency=Frequency.MONTH,
                    source_label="premium_amount",
                )
            ],
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