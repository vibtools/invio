# Installation

## Requirements

- Python 3.12+
- Windows, Linux, or macOS with a desktop environment

## Install dependencies

```bash
python -m pip install -r requirements.txt
```

Stripe and Refrens are packaged as validated provider manifests. No provider SDK is added by release `v1.0.0.1.2`.

## Start Invio

```bash
python main.py
```

The UI uses PySide6 and the official Vib Tools dark desktop baseline. After launch, open **Providers** and install the packaged provider(s) you want to expose to Accounts and Tasks. Installed provider cards can be returned to the Available state with **Uninstall**; no extra dependency is required.


## User settings storage

No extra setup is required for Settings. Invio creates its per-user `settings.json` only when a preference or opted-in runtime convenience value needs to be saved. The file stores non-sensitive application preferences only; account credentials remain outside this settings store.
