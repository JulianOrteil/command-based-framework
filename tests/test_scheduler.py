import math

import pytest

from command_based_framework.actions import Action, Condition
from command_based_framework.commands import Command
from command_based_framework.scheduler import Scheduler
from command_based_framework.subsystems import Subsystem


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
    assert scheduler._actions_stack[action] == {condition: {command}}

    # Rebind the command, just on a different condition
    new_condition = Condition.when_deactivated
    scheduler.bind_command(action, command, new_condition)
    assert action in scheduler._actions_stack
    assert len(scheduler._actions_stack) == 1
    assert len(scheduler._actions_stack[action]) == 2
    assert len(scheduler._actions_stack[action][condition]) == 0
    assert scheduler._actions_stack[action][new_condition] == {command}


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
    assert scheduler._actions_stack[action] == {condition: {command1}}

    # Add a second mapping
    scheduler.bind_command(action, command2, condition)
    assert action in scheduler._actions_stack
    assert scheduler._actions_stack[action] == {condition: {command1, command2}}

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
    assert scheduler._actions_stack[action] == {condition: {command1}}

    # Add a second mapping
    scheduler.bind_command(action, command2, condition)
    assert action in scheduler._actions_stack
    assert scheduler._actions_stack[action] == {condition: {command1, command2}}

    # Rebind the first mapping
    new_condition = Condition.when_deactivated
    scheduler.bind_command(action, command1, new_condition)
    assert action in scheduler._actions_stack
    assert len(scheduler._actions_stack) == 1
    assert len(scheduler._actions_stack[action]) == 2
    assert scheduler._actions_stack[action][condition] == {command2}
    assert scheduler._actions_stack[action][new_condition] == {command1}


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
    assert scheduler._actions_stack[action1] == {condition1: {command}}
    assert scheduler._actions_stack[action2] == {condition2: {command}}


def test_cancel_command() -> None:
    """Verify commands are canceled."""
    scheduler = Scheduler.instance or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    class MyAction(Action):

        def poll(self) -> bool:
            return True

    class MyCommand(Command):

        canceled_counter = 0

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

        def end(self, interrupted: bool) -> None:
            self.canceled_counter += 1
            assert interrupted

    action = MyAction()
    command = MyCommand()

    # Inject the command into the scheduler's stack
    scheduler._all_stack.add(command)

    # Cancel the command
    scheduler.cancel()
    assert command.canceled_counter == 1

    # Cancel again, but verify the command is already de-stacked
    scheduler.cancel()
    assert command.canceled_counter == 1


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


def test_scheduler_event_loop() -> None:
    """Verify the event loop schedules everything correctly."""
    scheduler = Scheduler.instance or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack


    class MyAction(Action):

        state = False

        def poll(self) -> bool:
            return self.state


    class MyCommand(Command):

        did_init = 0
        did_exec = 0
        did_end = 0
        did_interrupt = 0
        did_finish = 0
        do_finish = False

        def initialize(self) -> None:
            self.did_init += 1

        def execute(self) -> None:
            self.did_exec += 1

        def end(self, interrupted: bool) -> None:
            if interrupted:
                self.did_interrupt += 1
                return
            self.did_end += 1

        def is_finished(self) -> bool:
            self.did_finish += 1
            return self.do_finish

        def reset(self) -> None:
            self.did_init = 0
            self.did_exec = 0
            self.did_end = 0
            self.did_interrupt = 0
            self.do_finish = False


    class MySubsystem(Subsystem):

        periodic_counter = 0

        def periodic(self) -> None:
            self.periodic_counter += 1

        def reset(self) -> None:
            self.periodic_counter = 0


    action = MyAction()
    subsystem = MySubsystem()
    command1 = MyCommand("Command1", subsystem)
    command2 = MyCommand("Command2", subsystem)
    command3 = MyCommand("Command3", subsystem)
    command4 = MyCommand("Command4", subsystem)
    command5 = MyCommand("Command5", subsystem)

    # Bind each command to separate conditions
    action.cancel_when_activated(command1)
    action.toggle_when_activated(command2)
    action.when_activated(command3)
    action.when_deactivated(command4)
    action.when_held(command5)

    # Set the subsystem's default command to command1
    subsystem.default_command = command1

    # Verify the scheduler is tracking the commands correctly
    assert scheduler._actions_stack == {
        action: {
            Condition.cancel_when_activated: {command1},
            Condition.toggle_when_activated: {command2},
            Condition.when_activated: {command3},
            Condition.when_deactivated: {command4},
            Condition.when_held: {command5},
        }
    }

    # Run one loop of the scheduler
    scheduler.run_once()

    # Verify the scheduler has updated
    assert command1.did_init == 1
    assert command1.did_exec == 0
    assert command1.did_end == 0
    assert command1.did_interrupt == 0
    assert command1.did_finish == 0
    assert scheduler._scheduled_stack == {command1}
    assert not scheduler._incoming_stack
    assert subsystem.current_command == command1

    # Run again to ensure command1's exec is called
    scheduler.run_once()
    assert command1.did_init == 1
    assert command1.did_exec == 1
    assert command1.did_end == 0
    assert command1.did_interrupt == 0
    assert command1.did_finish == 1
    assert subsystem.current_command == command1

    # Now activate the action
    action.state = True

    # Run the scheduler and verify all commands are stacked correctly
    scheduler.run_once()  # when activated

    assert command1.did_init == 1
    assert command1.did_exec == 1
    assert command1.did_end == 0
    assert command1.did_interrupt == 1
    assert command1.did_finish == 1

    assert command2.did_init != command3.did_init
    assert not command2.did_exec and not command3.did_exec
    assert not command2.did_end and not command3.did_end
    assert not command2.did_finish and not command3.did_finish
    assert not command2.did_interrupt and not command3.did_interrupt
    assert subsystem.current_command == (command2 if command2.did_init else command3)

    scheduler.run_once()  # when held

    assert command1.did_init == 1
    assert command1.did_exec == 1
    assert command1.did_end == 0
    assert command1.did_interrupt == 1
    assert command1.did_finish == 1

    assert len({1, 0}.intersection({command2.did_init, command3.did_init})) == 2
    assert not command2.did_exec and not command3.did_exec
    assert not command2.did_end and not command3.did_end
    assert not command2.did_finish and not command3.did_finish
    assert len({1, 0}.intersection({command2.did_interrupt, command3.did_interrupt})) == 2

    assert command5.did_init == 1
    assert command5.did_exec == 0
    assert command5.did_end == 0
    assert command5.did_interrupt == 0
    assert command5.did_finish == 0
    assert subsystem.current_command == command5

    scheduler.run_once()  # when held

    assert command5.did_init == 1
    assert command5.did_exec == 1
    assert command5.did_end == 0
    assert command5.did_interrupt == 0
    assert command5.did_finish == 1

    # Deactivate the action
    action.state = False
    scheduler.run_once()  # when deactivated

    assert command5.did_init == 1
    assert command5.did_exec == 1
    assert command5.did_end == 1
    assert command5.did_interrupt == 0
    assert command5.did_finish == 1

    assert command4.did_init == 1
    assert command4.did_exec == 0
    assert command4.did_end == 0
    assert command4.did_interrupt == 0
    assert command4.did_finish == 0
    assert subsystem.current_command == command4

    scheduler.run_once()

    assert command4.did_init == 1
    assert command4.did_exec == 1
    assert command4.did_end == 0
    assert command4.did_interrupt == 0
    assert command4.did_finish == 1

    # End the command
    command4.do_finish = True
    scheduler.run_once()

    assert command4.did_init == 1
    assert command4.did_exec == 1
    assert command4.did_interrupt == 0
    assert command4.did_end == 1
    assert command4.did_finish == 2
    assert subsystem.current_command == None

    # Create another command and action
    action2 = MyAction()
    command6 = MyCommand("Command6", subsystem)

    action2.when_activated(command6)

    # Verify command1 is rescheduled as the default
    scheduler.run_once()

    assert command1.did_init == 2
    assert command1.did_exec == 1
    assert command1.did_end == 0
    assert command1.did_interrupt == 1
    assert command1.did_finish == 1
    assert subsystem.current_command == command1

    # Interrupt the default command
    action2.state = True
    scheduler.run_once()

    assert command1.did_init == 2
    assert command1.did_exec == 1
    assert command1.did_end == 0
    assert command1.did_interrupt == 2
    assert command1.did_finish == 1
    assert subsystem.current_command == command6
