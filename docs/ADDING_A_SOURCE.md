# Adding another source

Adding a website should be a local change.

1. Save an untouched sample at `data_vault/raw/<source>/<date>_<description>.json`.
2. Profile its top-level structure, value types, nulls, repeated IDs, and source terminology.
3. Write a source-to-canonical mapping table before code.
4. Add `src/insurance_data_layer/adapters/<source>.py` implementing `SourceAdapter`.
5. Register it with `@register` and import it from `adapters/__init__.py`.
6. Map only meanings supported by evidence. Add a `QualityIssue` for ambiguity.
7. Add source fixtures and tests for every overloaded or unusual field.
8. Run transformation and review the validation report.
9. Have the product/domain owner approve inferred mappings.
10. Only then load canonical records into PostgreSQL.

An adapter may populate only the canonical concepts applicable to its insurance type. Never add source-specific names such as `accidentIllness` to the shared model merely to avoid translating them.

## Required mapping document

Use this table for every new source:

| Raw path | Example | Canonical destination | Conversion | Status | Evidence/question |
|---|---|---|---|---|---|
| `output.tier` | `Gold` | `plan.name` | none | verified | Visible plan label |
| `output.refund` | `80` | reimbursement rule | divide by 100 | inferred | Confirm percentage basis |

Allowed statuses: `verified`, `inferred`, `ambiguous`, `unmapped`, `invalid`.
