from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class MappingStatus(StrEnum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    AMBIGUOUS = "ambiguous"
    UNMAPPED = "unmapped"
    INVALID = "invalid"


class InsuranceType(StrEnum):
    PET_HEALTH = "pet_health"
    PET_SURGERY = "pet_surgery"
    PET_ACCIDENT_ONLY = "pet_accident_only"
    PET_LIABILITY = "pet_liability"


class Frequency(StrEnum):
    MONTH = "month"
    YEAR = "year"
    ONE_TIME = "one_time"


class DurationUnit(StrEnum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"


class CoverageStatus(StrEnum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    LIMITED = "limited"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"
    NOT_CAPTURED = "not_captured"


class Money(StrictModel):
    amount: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class Premium(Money):
    frequency: Frequency
    source_label: str | None = None
    mapping_status: MappingStatus = MappingStatus.VERIFIED


class Provenance(StrictModel):
    source_site: str
    source_url: HttpUrl
    observed_at: datetime
    source_record_id: str | None = None
    scraper_status: str | None = None
    raw_file: str
    adapter_name: str
    adapter_version: str


class Provider(StrictModel):
    code: str
    name: str


class Product(StrictModel):
    code: str
    name: str
    insurance_type: InsuranceType
    market_country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")


class Plan(StrictModel):
    code: str
    name: str
    version_key: str
    valid_from: date | None = None
    valid_to: date | None = None


class PetRisk(StrictModel):
    species: Literal["cat", "dog"]
    name: str | None = None
    breed: str | None = None
    date_of_birth: date | None = None
    sex: Literal["female", "male", "unknown"] | None = None
    is_cross_breed: bool | None = None
    is_indoor: bool | None = None


class ApplicantRisk(StrictModel):
    date_of_birth: date | None = None
    postcode: str | None = None
    had_prior_damage: bool | None = None
    had_prior_insurance: bool | None = None


class QuoteRequest(StrictModel):
    request_key: str
    pet: PetRisk
    applicant: ApplicantRisk = Field(default_factory=ApplicantRisk)
    requested_effective_date: date | None = None
    submitted_at: datetime | None = None


class ReimbursementRule(StrictModel):
    rule_type: Literal["reimbursement"] = "reimbursement"
    benefit_code: str
    rate: Decimal = Field(ge=0, le=1)
    mapping_status: MappingStatus = MappingStatus.VERIFIED


class LimitRule(StrictModel):
    rule_type: Literal["limit"] = "limit"
    benefit_code: str
    amount: Money | None = None
    scope: str
    unlimited: bool = False
    mapping_status: MappingStatus = MappingStatus.VERIFIED

    @field_validator("amount")
    @classmethod
    def require_amount_unless_unlimited(cls, value: Money | None, info):
        if value is None and not info.data.get("unlimited", False):
            raise ValueError("amount is required unless unlimited is true")
        return value


class ExcessRule(StrictModel):
    rule_type: Literal["excess"] = "excess"
    benefit_code: str | None = None
    amount: Money
    scope: str
    mapping_status: MappingStatus = MappingStatus.AMBIGUOUS


class WaitingPeriodRule(StrictModel):
    rule_type: Literal["waiting_period"] = "waiting_period"
    benefit_code: str
    duration_value: int = Field(gt=0)
    duration_unit: DurationUnit
    eligible_from: date | None = None
    starts_from: str = "policy_effective_date"
    mapping_status: MappingStatus = MappingStatus.VERIFIED


class BenefitRule(StrictModel):
    rule_type: Literal["benefit"] = "benefit"
    benefit_code: str
    label: str
    status: CoverageStatus
    mapping_status: MappingStatus


class DurationRule(StrictModel):
    rule_type: Literal["duration"] = "duration"
    benefit_code: str
    duration_value: int | None = Field(default=None, gt=0)
    duration_unit: DurationUnit | None = None
    unlimited: bool = False
    mapping_status: MappingStatus = MappingStatus.INFERRED


Rule = Annotated[
    ReimbursementRule | LimitRule | ExcessRule | WaitingPeriodRule | BenefitRule | DurationRule,
    Field(discriminator="rule_type"),
]


class QualityIssue(StrictModel):
    code: str
    field: str | None = None
    message: str
    severity: Literal["info", "warning", "error"] = "warning"


class CanonicalRecord(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    canonical_record_key: str
    provider: Provider
    product: Product
    plan: Plan
    quote_request: QuoteRequest
    premiums: list[Premium]
    rules: list[Rule]
    provenance: Provenance
    quality_issues: list[QualityIssue] = Field(default_factory=list)

