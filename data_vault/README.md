# Data vault

The vault separates immutable source evidence from reproducible outputs.

```text
data_vault/
├── raw/<source>/          # Exact scraper payloads; append-only
├── canonical/             # Adapter-generated JSONL; safe to regenerate
└── reports/               # Validation and quarantine reports
```

Rules:

1. Never manually clean a file under `raw/`.
2. Use a source folder and observation date in every raw filename.
3. Never place secrets or direct customer identifiers here.
4. Correct mappings in adapters, then regenerate canonical outputs.
5. Raw files should be immutable after commit. A corrected scrape is a new file.

Current raw-file checksums:

| File | SHA-256 |
|---|---|
| `raw/santevet/2026-07-28_quotes.json` | `3d3cb1a84932ec04ad224eb1562ee0c6ba65130f670355dd569641117775203a` |
| `raw/hansemerkur/2026-07-28_quotes.json` | `310954aced9e0705840c4d075c27ae5555b64e9d2d7df79b397764438cca4b37` |

