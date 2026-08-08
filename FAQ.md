# FAQ

**Does 0.1.0 send invoices?**  
No. This release finalizes the UI and threading/provider contracts before backend integration.

**Why is the `project/` folder ignored?**  
It contains personal development material and is not public documentation.


## How do I uninstall a provider?

Open **Providers**. An installed provider card exposes **Uninstall**. After confirmation, Invio removes only the installed registry manifest. Bundled Stripe/Refrens package files and current in-memory accounts/tasks are not deleted.

## Why are dialogs wider and shorter in v1.0.0.1.2?

The approved modal update uses compact parent-relative sizing. Add Account uses two credential columns only when the selected provider has more than two credential fields. Native operating-system file/folder pickers are unchanged.
