# Invoice Template Guide

Invoice Templates contain reusable invoice content only. They intentionally exclude customer identity, billing, shipping, and payment details so one template can be reused for a bulk customer list.

## Template fields

- Template name
- Currency (uppercase in the UI)
- Days until due
- Invoice type: `INVOICE` or `BOS`
- Invoice title
- Invoice subtitle (optional)
- Invoice note / memo (optional)
- Customer note (optional)
- Footer (optional)
- Terms, one per line (optional)
- Provider automatic tax option when supported
- Exact-email provider customer reuse option when supported
- Line items: description, quantity, unit amount, tax rate

At least one line item is required. Quantity must be greater than zero, unit amount cannot be negative, and tax rate must be between 0 and 100.

## Currency behavior

Invio displays/stores approved currency codes in uppercase. In `v1.0.0.1.4`, the Currency field is an editable type-to-search control with case-insensitive contains matching and a compact maximum of eight visible results, avoiding the previous oversized full-list popup. Typed values are validated against the existing approved catalog before save. Provider adapters convert accepted codes to the provider's required API representation. Stripe receives lowercase ISO codes and amounts in the required minor-unit representation.

In `v1.0.0.1.5`, the Currency search behavior and catalog are unchanged. The editor UI now places the Currency and Invoice Type guidance on dedicated full-width rows and preserves minimum content height for wrapped notes and multiline controls. This prevents helper text from colliding with following controls when the compact dialog is resized or scrolled.

Provider/account country rules can further restrict which currencies a specific live account can use; a provider API rejection is reported as a task failure in Live Logs.

## Provider mapping

### Stripe

- Invoice note and non-default title/subtitle are mapped into Stripe's invoice description/memo.
- Footer, customer note, and terms are mapped into the invoice footer.
- Days until due are used with `send_invoice`.
- Automatic tax is enabled only when selected.
- Line quantity and unit amount are submitted as invoice-item values.
- The template's manual line tax rate is not converted into an arbitrary Stripe tax-rate object. Stripe automatic tax remains the supported built-in tax path.

### Refrens

The adapter supports invoice title, subtitle, type, currency, due date, notes, terms, line quantity/rate, and line tax rate. Refrens also requires customer billing identity/country. P04 Customer Lists can now supply explicit customer name/country data, while keeping that data outside Invoice Templates. Refrens Task execution remains blocked until the separately approved P11 production runner is implemented.


## Task snapshot behavior from v1.0.0.1.15

When a new Task is created, Invio copies the complete selected Invoice Template, including ordered line items and terms, into that Task's immutable execution snapshot. Editing the reusable source Template afterward affects future Tasks only. Existing Task Start/Retry continues to use the copy captured when that Task was created. Customer identity/name/country remains in Customer Lists and is not moved into Invoice Templates.

## P06 provider-template preflight

Invoice Templates remain provider-neutral reusable content, but a Task can execute only when its **immutable P05 template copy** passes the selected provider's current runtime contract. For the built-in Stripe adapter, P06 allows standard `INVOICE`, rejects `BOS`, rejects Automatic Tax under the current customer-location contract, and rejects any non-zero template percentage line tax because the current Stripe sender does not translate it into Stripe TaxRate object assignments. Existing customer-reuse, memo/title/subtitle, footer/customer-note, and terms mappings remain unchanged.

P06 does not remove or redesign template fields. Unsupported combinations are simply blocked before provider-side invoice creation with a correction message.

## v1.0.0.1.18 P06 contract clarification

The existing invoice-currency catalogue is intentionally unchanged. P06 continues to fail closed for currencies outside that catalogue rather than silently broadening provider currency/minor-unit handling. Stripe Automatic Tax and non-zero template percentage line tax remain blocked by the current Invio Stripe preflight contract, and Stripe remains `INVOICE`-only in the current adapter.
