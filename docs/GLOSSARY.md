# Canonical glossary

| Term | Insurance Data Layer meaning |
|---|---|
| Provider | Brand or organisation offering the product. Its legal role is not assumed. |
| Underwriter | Regulated insurer legally assuming risk. Not captured by these samples. |
| Product | Contract family for one insurance type and market. |
| Plan | Named coverage configuration, such as Confort or PremiumPlus. |
| Plan version | Time-bound definition of plan terms. Current sample dates are observations, not proven legal effective dates. |
| Quote request | Snapshot of pet, applicant, and requested-start inputs used for pricing. |
| Quote option | A plan and personalised premium returned for one request. A canonical record currently represents this unit. |
| Premium | Price observation with amount, currency, frequency, and original label. |
| Excess | Customer-retained part of a covered loss. Scope stays `unknown` until verified. |
| Reimbursement rate | Fraction of eligible health expense considered for reimbursement. Stored from 0 to 1. |
| Benefit | Specific protection or service with an explicit coverage status. |
| Limit | Maximum or threshold with money, benefit, and scope. |
| Waiting period | Benefit-specific duration before eligibility begins. |
| Duration rule | Non-monetary duration such as permitted time abroad. |
| Underwriting input | Pet or applicant fact used for eligibility or pricing. |
| Observation | What a scraper saw, where, and when. It is evidence, not automatically a legal product fact. |

## Missing-value rule

`excluded`, `unknown`, `not_captured`, and `not_applicable` are different states. An adapter must not translate `null` to `excluded` without verified source semantics.

## Current unresolved meanings

- Santévet excess application scope.
- HanseMerkur relationship between `premium_amount` and `premium_annual`.
- Whether observation dates equal plan-version effective dates.
- Legal underwriter and governing documents for each product.
- Whether HanseMerkur monetary feature mappings are limits, thresholds, or another contractual rule in every case.
