# Accounts Flat Table UI — v1.0.0.1.48.8

The v1.48.7 canonical one-badge status renderer is preserved. The `STATUS` column now uses content-driven width rather than a fixed 132px section so labels such as `✕ Not Installed` remain fully contained without widening unrelated columns.

# Accounts Flat Table UI — v1.0.0.1.48.7

The Accounts table keeps its v1.48.6 compact column/action layout. Status cells now use `set_data_status_cell()` so only the canonical centered badge is visible; raw status text is not painted underneath.

# Accounts Flat Table UI — v1.0.0.1.48.6

Compact presentation remains:

```text
Accounts                                             [Add Account]
Added Accounts List             [Search] [Provider] [Status]
ACCOUNT              PROVIDER              STATUS        ACTION
Odoo-main            Odoo                  ✓ Verified       ⋯
Refrens-test         Refrens               ! Not Verified   ⋯
Agiled-main          Agiled                ! Not Installed  ⋯
Showing 1–10 of N                         Rows [10] [<] [1] [>]
```

Accounts-only semantic colors: success `#22C55E`, warning `#FCD34D`, danger `#F87171`, primary `#2563EB`. Row menus retain Edit/Re-test/Delete callbacks and are bounded to the Invio-window/current-screen safe region.
