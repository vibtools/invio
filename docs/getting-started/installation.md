# Installation

## Requirements

- Python 3.12+
- Windows, Linux, or macOS with a desktop environment

## Install dependencies

```bash
python -m pip install -r requirements.txt
```

Stripe and Refrens are packaged as validated provider manifests. No provider SDK is added by release `v1.0.0.1`.

## Start Invio

```bash
python main.py
```

The UI uses PySide6 and the official Vib Tools dark desktop baseline. After launch, open **Providers** and install the packaged provider(s) you want to expose to Accounts and Tasks.
