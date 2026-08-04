# Insurance Data Layer

Insurance Data Layer converts source-specific pet-insurance scrape results into one validated canonical model. It is the data-refinement boundary before PostgreSQL, pgvector, or a chatbot.

```text
raw source JSON -> source adapter -> canonical JSONL -> PostgreSQL loader
                              |-> validation report
```

The project currently supports:

- Santévet pet-health quote observations;
- HanseMerkur dog-liability quote observations.

It deliberately does **not** perform embeddings or database loading yet. This phase establishes trustworthy meaning first.

## Why adapters exist

An adapter is a Python translator for one source. For Santévet, `coverage_amount: 70` is mapped to a `0.70` reimbursement rate. For HanseMerkur, `coverage_amount: 50000000` is mapped to a €50 million overall liability limit. The raw key is identical; the business meaning is not.

All adapters output `CanonicalRecord`, but they populate only applicable concepts. The standard format is therefore a typed object that later maps to connected database tables.

## Layout

```text
insurance-data-layer/
├── data_vault/
│   ├── raw/                 immutable source evidence
│   ├── canonical/           generated JSONL
│   └── reports/             generated validation reports
├── docs/
│   ├── ADDING_A_SOURCE.md
│   ├── GLOSSARY.md
│   └── SOURCE_MAPPINGS.md
├── src/insurance_data_layer/
│   ├── adapters/            one module per source
│   ├── models.py            canonical Pydantic model
│   ├── pipeline.py          transform and report
│   └── cli.py
└── tests/
```

## Setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

On Windows PowerShell, activation is:

```powershell
.venv\Scripts\Activate.ps1
```

## Transform the samples

```bash
insurance-data-layer data_vault/raw/santevet/2026-07-28_quotes.json \
  --output data_vault/canonical/santevet.jsonl \
  --report data_vault/reports/santevet.json

insurance-data-layer data_vault/raw/hansemerkur/2026-07-28_quotes.json \
  --output data_vault/canonical/hansemerkur.jsonl \
  --report data_vault/reports/hansemerkur.json
```

Generated JSONL and reports are ignored by Git because they are reproducible. Raw source evidence is versioned for this MVP; if it later contains personal or licensed data, move it to protected object storage and commit only manifests/fixtures.

## Verify

```bash
pytest
ruff check .
```

Expected sample results:

| Source | Raw rows | Canonical rows | Unique quote requests |
|---|---:|---:|---:|
| Santévet | 29 | 29 | 6 |
| HanseMerkur | 100 | 100 | 50 |

Canonical rows currently represent quote options. Repeated plan terms are expected at this interchange stage; the future PostgreSQL loader will upsert and connect providers, products, plan versions, quote requests, quote options, premiums, and rules.

## Definition of done for a source

- raw sample preserved with provenance;
- mapping table reviewed;
- adapter registered;
- values typed with units and scopes;
- ambiguity emitted as a quality issue;
- representative and edge-case tests pass;
- validation report contains zero invalid records;
- no source-specific field leaks into the canonical model.
