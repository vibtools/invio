# Task Guide

A Task is an isolated provider execution unit. Each open Task owns its selected accounts until the Task is closed.

## Create a Task

Select:

1. installed Provider;
2. one or more available **Verified** Accounts for that provider;
3. Invoice Template;
4. Customer List with at least one email.

P01 verification gates remain unchanged. P02 persists the created Task, ordered selected accounts, counters/status/message, and account reservations transactionally.

## Restart Recovery

Tasks survive application restart. A Task stored as `Ready`, `Stopped`, `Failed`, or `Completed` is restored with its saved metadata. A Task found as `Running`, `Paused`, or `Stopping` is restored as **Stopped** with a recovery message. Invio does not automatically resume provider requests after restart.

Account reservations are restored with the Task, so an account reserved by an open recovered Task does not become silently selectable by another Task.

## Controls

Existing controls remain: **Start**, **Pause**, **Resume**, **Stop**, **Retry Failed**, and **Close Task**. P03 adds a pre-execution provider-install gate: Start/Retry cannot create a runner while the Task provider is uninstalled. Reinstalling the provider restores availability without rebuilding the Task or its Account reservation.

Re-testing a reserved Account is permitted only when its Task worker is inactive. If that Re-test fails, the Account becomes **Not Verified** and the existing P01 execution gate blocks the Task.

## P02 Boundary

P02 persists Task-level execution metadata, not the future P10 recipient delivery ledger. Failed-recipient retry memory, provider customer/invoice IDs, per-attempt records, run identities, and exact crash-to-provider reconciliation remain later scope.
