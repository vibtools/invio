# Invio v1.0.0.1.4 Delta Patch Manifest

Baseline: `v1.0.0.1.3`  
Target: `v1.0.0.1.4`  
Patch format: project-root replace-ready ZIP with no wrapper directory.

## Approved scope

1. Correct wrong white/light background surfaces affecting Settings and Invoice Template scroll/content regions.
2. Make Invoice Template Currency slightly narrower and replace the oversized currency list experience with compact type-to-search completion while keeping the existing approved currency catalog.
3. Repair Invoice Template popup spacing/stretch behavior without removing or changing fields.
4. Preserve the existing invoice-template -> task -> provider create/send binding and all provider/worker behavior.
5. Update directly required tests, version metadata, README/CHANGELOG/public docs, private scope/update/audit records, and release notes.

## Explicit non-changes

- No page was added, removed, or renamed.
- No invoice-template field/model was removed or renamed.
- No provider manifest, credential schema, account model, customer-list model, task model, provider execution sequence, retry behavior, or QThread architecture was changed.
- No dependency was added, removed, or replaced.
- No customer, billing, shipping, or payment data was added to Invoice Templates.
