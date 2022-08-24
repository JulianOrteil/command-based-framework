import math

import pytest

from command_based_framework.actions import Action, Condition
from command_based_framework.commands import Command
from command_based_framework.scheduler import Scheduler


def test_tracking_scheduler_instances() -> None:
    """Verify only one scheduler instance exists at any one time."""
    from command_based_framework.exceptions import SchedulerExistsError

    # Verify no scheduler has been set
    assert Scheduler.instance == None

    # Create a scheduler and verify it is tracked
    s = Scheduler()
    assert Scheduler.instance == s

    # Ensure no new scheduler can be created
    with pytest.raises(SchedulerExistsError):
        Scheduler()

    # Delete the reference and ensure a new scheduler can be created
    del s
    t = Scheduler()

    # Once again, ensure no new scheduler can be created
    with pytest.raises(SchedulerExistsError):
        Scheduler()


def test_setting_clock_speed() -> None:
    """Verify the clock speed is set properly."""
    scheduler = Scheduler.instance or Scheduler()

    assert math.isclose(scheduler.clock_speed, 1 / 60)

    # Set the clock speed normally
    scheduler.clock_speed = 1 / 50

    # Ensure setting at or below 0 raises value errors
    with pytest.raises(ValueError):
        scheduler.clock_speed = 0

    with pytest.raises(ValueError):
        scheduler.clock_speed = -1

    # Ensure the clock speed is still at 1/50
    assert math.isclose(scheduler.clock_speed, 1 / 50)


def test_rebinding_same_command() -> None:
    """Verify actions are bound to commands correctly."""
    scheduler = Scheduler.instance or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    # Add a new mapping
    class MyAction(Action):

        def poll(self) -> bool:
            return True

    class MyCommand(Command):

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

    action = MyAction()
    command = MyCommand()
    condition = Condition.when_activated

    scheduler.bind_command(action, command, condition)
    assert action in scheduler._actions_stack
    assert scheduler._actions_stack[action] == {condition: [command]}

    # Rebind the command, just on a different condition
    new_condition = Condition.when_deactivated
    scheduler.bind_command(action, command, new_condition)
    assert action in scheduler._actions_stack
    assert len(scheduler._actions_stack) == 1
    assert len(scheduler._actions_stack[action]) == 2
    assert len(scheduler._actions_stack[action][condition]) == 0
    assert scheduler._actions_stack[action][new_condition] == [command]


def test_binding_multiple_commands_same_action() -> None:
    """Verify multiple commands bind to an action."""
    scheduler = Scheduler.instance or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    # Add a new mapping
    class MyAction(Action):

        def poll(self) -> bool:
            return True

    class MyCommand(Command):

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

    action = MyAction()
    command1 = MyCommand()
    command2 = MyCommand()
    condition = Condition.when_activated

    scheduler.bind_command(action, command1, condition)
    assert action in scheduler._actions_stack
    assert scheduler._actions_stack[action] == {condition: [command1]}

    # Add a second mapping
    scheduler.bind_command(action, command2, condition)
    assert action in scheduler._actions_stack
    assert scheduler._actions_stack[action] == {condition: [command1, command2]}

def test_rebinding_multiple_commands_same_action() -> None:
    """Verify rebinding multiple commands on the same action."""
    scheduler = Scheduler.instance or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    # Add a new mapping
    class MyAction(Action):

        def poll(self) -> bool:
            return True

    class MyCommand(Command):

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

    action = MyAction()
    command1 = MyCommand()
    command2 = MyCommand()
    condition = Condition.when_activated

    scheduler.bind_command(action, command1, condition)
    assert action in scheduler._actions_stack
    assert scheduler._actions_stack[action] == {condition: [command1]}

    # Add a second mapping
    scheduler.bind_command(action, command2, condition)
    assert action in scheduler._actions_stack
    assert scheduler._actions_stack[action] == {condition: [command1, command2]}

    # Rebind the first mapping
    new_condition = Condition.when_deactivated
    scheduler.bind_command(action, command1, new_condition)
    assert action in scheduler._actions_stack
    assert len(scheduler._actions_stack) == 1
    assert len(scheduler._actions_stack[action]) == 2
    assert scheduler._actions_stack[action][condition] == [command2]
    assert scheduler._actions_stack[action][new_condition] == [command1]


def test_binding_multiple_actions() -> None:
    """Verify binding a command to multiple actions."""
    scheduler = Scheduler.instance or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    # Add a new mapping
    class MyAction(Action):

        def poll(self) -> bool:
            return True

    class MyCommand(Command):

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

    action1 = MyAction()
    action2 = MyAction()
    command = MyCommand()
    condition1 = Condition.when_activated
    condition2 = Condition.when_held

    scheduler.bind_command(action1, command, condition1)
    scheduler.bind_command(action2, command, condition2)
    assert action1 in scheduler._actions_stack
    assert action2 in scheduler._actions_stack
    assert scheduler._actions_stack[action1] == {condition1: [command]}
    assert scheduler._actions_stack[action2] == {condition2: [command]}


def test_command_raises_runtime_warning_in_cancel() -> None:
    """Verify commands raise RuntimeWarnings if they fail to cancel."""
    scheduler = Scheduler.instance or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    class MyCommand(Command):

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

        def end(self, interrupted: bool) -> None:
            raise ValueError("test error")

    command = MyCommand()

    # Artificially inject the command into the stack
    scheduler._all_stack.add(command)

    # Verify the command fails and raises a warning if not explicitly
    # specified
    with pytest.warns(RuntimeWarning):
        scheduler.cancel()

    # Re-inject the command
    scheduler._all_stack.add(command)

    # Verify the command fails and raises a warning if explicitly
    # specified
    with pytest.warns(RuntimeWarning):
        scheduler.cancel(command)
