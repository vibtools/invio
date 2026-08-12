## v1.0.0.1.49.4 path rule

All archive entries must be canonical forward-slash names. Do not package `./provider.json`, repeated separators, backslashes, Windows drive/ADS/device names, or path components ending with a dot/space. Use `scripts/provider/build_ivx.py` to produce the deterministic supported layout.

# Provider IVX Format v1 example

Source folder:

```text
ZohoBooks/
├── provider.json
├── adapter.py
├── logo.png          # optional
├── README.md         # optional
├── LICENSE           # optional
└── docs/             # optional
```

Build from the repository root:

```bash
python scripts/provider/build_ivx.py path/to/ZohoBooks
```

Result:

```text
Invio_ZohoBooks_Provider_v1.2.0.ivx
├── provider.json
├── adapter.py
├── logo.png
├── README.md
├── LICENSE
├── docs/...
└── SHA256SUMS.txt
```

`provider.json` must be at archive root. IVX Load validates and imports the package but does not execute `adapter.py`; executable trust/validation remains at Install.
