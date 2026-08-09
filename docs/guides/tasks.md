# Task Guide

A task is an isolated provider execution unit. Each task owns its selected accounts until the task is closed.

## Create a task

Select:

1. installed Provider;
2. one or more available **Verified** Accounts for that provider;
3. Invoice Template;
4. Customer List with at least one email.

The selected template ID/name is stored on the task. A template assigned to an open task cannot be deleted. Selected accounts are reserved and cannot be selected by another task. Accounts that have not completed a successful real API Test are disabled in New Task and rejected by backend Task creation.

## Controls

Existing task controls remain: **Start**, **Pause**, **Resume**, **Stop**, **Retry Failed**, and **Close Task**.

- Start first re-checks every assigned account is still `Verified`, then obtains the built-in runner for packaged providers or an explicitly registered custom runner.
- Pause/Resume/Stop act on that task's own worker slot.
- Retry Failed re-checks account verification before using provider runtime failure state to retry failed Stripe recipients only.
- Close Task requires the worker to be stopped, releases account reservations, and clears task-local retry state.

## Threading

Every active task has a separate `QThread`. Network invoice creation/sending occurs inside the task worker, not on the GUI thread. Worker progress/status/log signals update the UI safely.

## Provider constraints

Stripe has a built-in executable task runner in `v1.0.0.1.3`. Refrens task start is blocked before any create/send request when required `billedTo.country` cannot be supplied by the current email-only Customer List model.
