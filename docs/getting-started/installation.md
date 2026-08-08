# Installation

## Requirements

- Python 3.12+
- Windows, Linux, or macOS with a desktop environment

## Install dependencies

```bash
python -m pip install -r requirements.txt
```

`v1.0.0.1.3` adds no dependency. Stripe and Refrens remain packaged provider manifests, and built-in provider HTTPS execution uses Python's standard library rather than adding provider SDK packages.

## Start Invio

```bash
python main.py
```

After launch, use **Providers** to install the bundled provider(s). Then add an account, create an Invoice Template, create/import a Customer List, and create a Task. Dashboard provides the live setup/readiness summary.

## User settings storage

Settings creates per-user `settings.json` only when needed. It contains non-sensitive preferences/runtime convenience state; account credentials remain outside the settings store.
