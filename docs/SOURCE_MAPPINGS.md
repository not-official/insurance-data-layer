# Source mappings

## Santévet

| Raw field | Canonical destination | Conversion/status |
|---|---|---|
| `output.package_name` | `plan.name` | direct, verified |
| `output.package_code` | `plan.code` | normalized slug |
| `output.coverage_amount` | reimbursement rule | percentage divided by 100, inferred from source context |
| `features.coverage_limits.*` | benefit limit | EUR, policy-year scope inferred |
| `features.waiting_periods.*` | waiting-period rule | plural units normalized |
| `input.*` | quote-request pet/applicant snapshot | source enums normalized |
| `output.premium_amount` | monthly premium | direct |
| `output.excess_amount` | excess | amount direct; scope ambiguous |
| `insurance_metadata.country_code` | product market | does not imply coverage territory |
| `output.pet_id` | provenance only | not trusted as pet/request identity |

## HanseMerkur

| Raw field | Canonical destination | Conversion/status |
|---|---|---|
| `output.package_name` | `plan.name` | direct |
| `output.coverage_amount` | overall third-party-liability limit | EUR, not a percentage |
| `output.premium_amount` | monthly premium | preserved directly |
| `output.premium_annual` | annual-labelled premium | preserved as ambiguous; not recalculated |
| `features` Boolean | benefit status | `true` included, `false` excluded |
| `features` monetary | benefit limit/threshold | explicit mapping, inferred |
| `features` duration | duration rule | parsed to typed duration or unlimited |
| `label.lm.tarifinformationen` | quality issue | UI localisation key; not embedded or treated as benefit |
| `input.*` | dog/applicant quote snapshot | direct |

