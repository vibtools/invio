# Windows Popup Lifecycle Canary — v1.0.0.1.48.02

Use the exact v1.48.02 candidate on Windows and verify each existing flow opens a styled Invio message box without a `libshiboken` deleted-layout exception.

1. Close Task → choose No, then reopen → choose Yes.
2. New Task with no available account → Warning appears and closes normally.
3. Trigger an Add Account validation/API Test failure → Warning appears.
4. Customer import result/warning → feedback appears after the existing import logic.
5. Delete confirmation paths → No cancels; Yes continues the existing delete action.
6. Information/Critical message paths → OK closes normally.
7. Reopen message boxes repeatedly to confirm no stale layout lifetime issue.

Expected: existing message text/buttons/business behavior is unchanged; only the broken popup lifecycle is repaired.
