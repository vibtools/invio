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
