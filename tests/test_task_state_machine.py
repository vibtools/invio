from __future__ import annotations

import unittest

from src.core.state import AppState, StateError
from src.tasks.state_machine import (
    COMPLETED_RESEND_MESSAGE,
    CONTINUATION_UNAVAILABLE_MESSAGE,
    FAILED_FULL_START_MESSAGE,
    TaskAction,
    TaskExecutionMode,
    require_task_action,
    task_action_policy,
    validate_status_transition,
)


class TaskStateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = AppState()
        self.account = self.state.add_account(
            "stripe", "Stripe", "Primary", "Test", {"secret_key": "sk_test_state"}, status="Verified"
        )
        customer_list = self.state.create_customer_list("Customers")
        self.state.add_emails(customer_list.id, ["a@example.com", "b@example.com"])
        template = self.state.save_invoice_template(
            template_id=None,
            name="Default",
            currency="usd",
            days_until_due=30,
            memo="",
            footer="",
            automatic_tax=False,
            reuse_customer=True,
            items=[("Service", "1", "10.00")],
        )
        self.task = self.state.create_task(
            "stripe", "Stripe", [self.account.id], customer_list.id, template.id
        )

    def test_allowed_status_transitions_are_explicit(self):
        for current, target in (
            ("Ready", "Running"),
            ("Running", "Paused"),
            ("Paused", "Running"),
            ("Running", "Stopping"),
            ("Stopping", "Stopped"),
            ("Stopped", "Running"),
            ("Running", "Failed"),
            ("Failed", "Running"),
            ("Running", "Completed"),
            ("Completed", "Completed"),
        ):
            validate_status_transition(current, target)

    def test_ambiguous_or_resend_transitions_are_rejected(self):
        for current, target in (
            ("Ready", "Paused"),
            ("Stopped", "Ready"),
            ("Failed", "Ready"),
            ("Completed", "Ready"),
            ("Completed", "Running"),
        ):
            with self.subTest(current=current, target=target):
                with self.assertRaises(ValueError):
                    validate_status_transition(current, target)

    def test_first_run_requires_pristine_ready_task(self):
        mode = require_task_action(self.task, TaskAction.START)
        self.assertIs(mode, TaskExecutionMode.FIRST_RUN)
        self.task.processed = 1
        self.task.success = 1
        with self.assertRaisesRegex(ValueError, "already contains progress"):
            require_task_action(self.task, TaskAction.START)

    def test_stopped_task_uses_resume_remaining_not_full_start(self):
        self.task.status = "Stopped"
        with self.assertRaisesRegex(ValueError, "cannot perform a full Start"):
            require_task_action(self.task, TaskAction.START)
        mode = require_task_action(
            self.task,
            TaskAction.RESUME_REMAINING,
            resume_remaining_available=True,
        )
        self.assertIs(mode, TaskExecutionMode.RESUME_REMAINING)

    def test_failed_task_can_only_retry_exact_failed_set(self):
        self.task.status = "Failed"
        self.task.processed = self.task.total
        self.task.success = self.task.total - 1
        self.task.failed = 1
        with self.assertRaisesRegex(ValueError, "cannot perform a full Start"):
            require_task_action(self.task, TaskAction.START)
        mode = require_task_action(
            self.task,
            TaskAction.RETRY_FAILED,
            retry_failed_available=True,
        )
        self.assertIs(mode, TaskExecutionMode.RETRY_FAILED)
        with self.assertRaisesRegex(ValueError, "exact continuation recipient set"):
            require_task_action(
                self.task,
                TaskAction.RETRY_FAILED,
                retry_failed_available=False,
            )

    def test_completed_task_has_no_execution_action(self):
        self.task.status = "Completed"
        self.task.processed = self.task.total
        self.task.success = self.task.total
        policy = task_action_policy(self.task)
        self.assertFalse(policy.start_enabled)
        self.assertFalse(policy.retry_enabled)
        self.assertTrue(policy.close_enabled)
        self.assertEqual(policy.start_tooltip, COMPLETED_RESEND_MESSAGE)
        with self.assertRaisesRegex(ValueError, "Create a new Task"):
            require_task_action(self.task, TaskAction.START)

    def test_policy_exposes_safe_stopped_and_failed_actions_only_when_recipient_set_exists(self):
        self.task.status = "Stopped"
        stopped = task_action_policy(self.task, resume_remaining_available=True)
        self.assertTrue(stopped.start_enabled)
        self.assertEqual(stopped.start_label, "Resume Remaining")
        missing = task_action_policy(self.task, resume_remaining_available=False)
        self.assertFalse(missing.start_enabled)
        self.assertEqual(missing.start_tooltip, CONTINUATION_UNAVAILABLE_MESSAGE)

        self.task.status = "Failed"
        failed = task_action_policy(self.task, retry_failed_available=True)
        self.assertFalse(failed.start_enabled)
        self.assertTrue(failed.retry_enabled)
        self.assertEqual(failed.start_tooltip, FAILED_FULL_START_MESSAGE)

    def test_close_is_blocked_while_worker_state_is_active(self):
        for status in ("Running", "Paused", "Stopping"):
            self.task.status = status
            with self.subTest(status=status):
                with self.assertRaisesRegex(ValueError, "Stop the task before closing"):
                    require_task_action(self.task, TaskAction.CLOSE)

    def test_app_state_enforces_transition_and_close_rules(self):
        with self.assertRaisesRegex(StateError, "Ready -> Paused"):
            self.state.set_task_status(self.task.id, "Paused")
        self.state.set_task_status(self.task.id, "Running")
        with self.assertRaisesRegex(StateError, "Stop the task before closing"):
            self.state.close_task(self.task.id)
        self.assertEqual(self.state.account_reservations[self.account.id], self.task.id)
        self.state.set_task_status(self.task.id, "Stopping")
        self.state.set_task_status(self.task.id, "Stopped")
        self.state.close_task(self.task.id)
        self.assertNotIn(self.account.id, self.state.account_reservations)


if __name__ == "__main__":
    unittest.main()
