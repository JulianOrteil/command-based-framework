import math
from threading import Thread
import time

import mock
import pytest

from command_based_framework.actions import Action, Condition
from command_based_framework.commands import Command, CommandState, ParallelCommandGroup, SequentialCommandGroup
from command_based_framework.scheduler import Scheduler
from command_based_framework.subsystems import Subsystem


def test_tracking_scheduler_instances() -> None:
    """Verify only one scheduler instance exists at any one time."""
    from command_based_framework.exceptions import SchedulerExistsError

    # Verify no scheduler has been set
    assert Scheduler.get_instance() == None

    # Create a scheduler and verify it is tracked
    s = Scheduler()
    assert Scheduler.get_instance() == s

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
    scheduler = Scheduler.get_instance() or Scheduler()

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
    scheduler = Scheduler.get_instance() or Scheduler()
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
    scheduler = Scheduler.get_instance() or Scheduler()
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
    scheduler = Scheduler.get_instance() or Scheduler()
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
    scheduler = Scheduler.get_instance() or Scheduler()
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
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack


    class MyCommand(Command):

        canceled_counter = 0

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

        def end(self, interrupted: bool) -> None:
            self.canceled_counter += 1
            assert interrupted

    command = MyCommand()
    command.state = CommandState.executing

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
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    class MyCommand(Command):
        _state = CommandState.executing

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

        def end(self, interrupted: bool) -> None:
            raise ValueError("test error")

    command = MyCommand()
    command.state = CommandState.executing

    # Artificially inject the command into the stack
    scheduler._all_stack.add(command)

    # Verify the command fails and raises a warning if not explicitly
    # specified
    with pytest.warns(RuntimeWarning):
        scheduler.cancel()

    # Re-inject the command
    scheduler._all_stack.add(command)
    command.state = CommandState.executing

    # Verify the command fails and raises a warning if explicitly
    # specified
    with pytest.warns(RuntimeWarning):
        scheduler.cancel(command)


def test_scheduler_event_loop() -> None:
    """Verify the event loop schedules everything correctly."""
    scheduler = Scheduler.get_instance() or Scheduler()
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
    subsystem2 = MySubsystem()
    command1 = MyCommand("Command1", subsystem)
    command2 = MyCommand("Command2", subsystem)
    command3 = MyCommand("Command3", subsystem)
    command4 = MyCommand("Command4", subsystem)
    command5 = MyCommand("Command5", subsystem)
    command6 = MyCommand("Command6", subsystem2)

    # Bind each command to separate conditions
    action.toggle_when_activated(command2)
    action.when_activated(command3)
    action.when_deactivated(command4)
    action.when_held(command5)
    action.cancel_when_activated(command6)

    # Set the subsystem's default command to command1
    subsystem.default_command = command1

    # Verify the scheduler is tracking the commands correctly
    assert scheduler._actions_stack == {
        action: {
            Condition.cancel_when_activated: {command6},
            Condition.toggle_when_activated: {command2},
            Condition.when_activated: {command3},
            Condition.when_deactivated: {command4},
            Condition.when_held: {command5},
        }
    }

    # Inject command6 as if it was already executing
    scheduler._scheduled_stack.add(command6)

    # Run one loop of the scheduler
    scheduler.run_once()

    # Verify the scheduler has updated
    assert command1.did_init == 1
    assert command1.did_exec == 0
    assert command1.did_end == 0
    assert command1.did_interrupt == 0
    assert command1.did_finish == 0
    assert scheduler._scheduled_stack == {command1, command6}
    assert not scheduler._incoming_stack
    assert subsystem.current_command == command1
    assert subsystem.periodic_counter == 1
    assert command6.did_exec == 1

    # Run again to ensure command1's exec is called
    scheduler.run_once()
    assert command1.did_init == 1
    assert command1.did_exec == 1
    assert command1.did_end == 0
    assert command1.did_interrupt == 0
    assert command1.did_finish == 1
    assert subsystem.current_command == command1
    assert subsystem.periodic_counter == 2
    assert command6.did_exec == 2

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
    assert subsystem.periodic_counter == 3

    assert command6.did_exec == 2
    assert command6.did_interrupt == 1

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
    assert subsystem.periodic_counter == 4

    scheduler.run_once()  # when held

    assert command5.did_init == 1
    assert command5.did_exec == 1
    assert command5.did_end == 0
    assert command5.did_interrupt == 0
    assert command5.did_finish == 1
    assert subsystem.periodic_counter == 5

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
    assert subsystem.periodic_counter == 6

    scheduler.run_once()

    assert command4.did_init == 1
    assert command4.did_exec == 1
    assert command4.did_end == 0
    assert command4.did_interrupt == 0
    assert command4.did_finish == 1
    assert subsystem.periodic_counter == 7

    # End the command
    command4.do_finish = True
    scheduler.run_once()

    assert command4.did_init == 1
    assert command4.did_exec == 1
    assert command4.did_interrupt == 0
    assert command4.did_end == 1
    assert command4.did_finish == 2
    assert subsystem.current_command == None
    assert subsystem.periodic_counter == 8

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
    assert subsystem.periodic_counter == 9

    # Interrupt the default command
    action2.state = True
    scheduler.run_once()

    assert command1.did_init == 2
    assert command1.did_exec == 1
    assert command1.did_end == 0
    assert command1.did_interrupt == 2
    assert command1.did_finish == 1
    assert subsystem.current_command == command6
    assert subsystem.periodic_counter == 10


def test_toggle_commands() -> None:
    """Verify commands toggle."""
    scheduler = Scheduler.get_instance() or Scheduler()
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

    command = MyCommand()
    action = MyAction()
    action.state = True

    action.toggle_when_activated(command)

    scheduler.run_once()

    assert command.did_init == 1
    assert command.did_exec == 0
    assert command.did_end == 0
    assert command.did_interrupt == 0
    assert command.did_finish == 0

    scheduler.run_once()

    assert command.did_init == 1
    assert command.did_exec == 1
    assert command.did_end == 0
    assert command.did_interrupt == 0
    assert command.did_finish == 1

    action.state = False

    scheduler.run_once()

    assert command.did_init == 1
    assert command.did_exec == 2
    assert command.did_end == 0
    assert command.did_interrupt == 0
    assert command.did_finish == 2

    action.state = True

    scheduler.run_once()

    assert command.did_init == 1
    assert command.did_exec == 2
    assert command.did_end == 1
    assert command.did_interrupt == 0
    assert command.did_finish == 2


def test_command_error_cancels() -> None:
    """Verify commands cancel if methods raise unhandable exceptions."""
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    class MyCommand(Command):

        interrupted = False

        def is_finished(self) -> bool:
            return False

        def execute(self) -> None:
            raise ValueError("test")

        def end(self, interrupted: bool) -> None:
            self.interrupted = interrupted

        def handle_exception(self, *exc) -> bool:
            return False

    class MyCommand2(Command):

        interrupted = False

        def initialize(self) -> None:
            raise ValueError("test")

        def is_finished(self) -> bool:
            return False

        def execute(self) -> None:
            pass

        def end(self, interrupted: bool) -> None:
            self.interrupted = interrupted

        def handle_exception(self, *exc) -> bool:
            return False

    command = MyCommand()
    command2 = MyCommand2()

    # Inject the command
    scheduler._incoming_stack.add(command2)
    scheduler._all_stack.add(command)
    scheduler._scheduled_stack.add(command)

    scheduler.run_once()

    assert command.interrupted
    assert command2.interrupted


def test_conflicting_incoming_commands() -> None:
    """Verify incoming commands with conflicting requirements."""
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack


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

        def periodic(self) -> None:
            pass

    subsystem1 = MySubsystem()
    subsystem2 = MySubsystem()
    command1 = MyCommand("Command1", subsystem1)
    command2 = MyCommand("Command2", subsystem1)
    command3 = MyCommand("Command3", subsystem2)

    # Inject both commands into the incoming stack
    scheduler._incoming_stack.add(command1)
    scheduler._incoming_stack.add(command2)
    scheduler._incoming_stack.add(command3)

    # Verify only one command runs
    scheduler.run_once()
    assert command1.did_init != command2.did_init
    assert command3.did_init


def test_scheduled_incoming_conflicting_commands() -> None:
    """Verify scheduled commands are interrupted by incoming commands."""
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack


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

        def periodic(self) -> None:
            pass

    subsystem = MySubsystem()
    subsystem2 = MySubsystem()
    command1 = MyCommand("Command1", subsystem)
    command1.state = CommandState.executing
    command2 = MyCommand("Command2", subsystem)
    command3 = MyCommand("Command3", subsystem2)
    command3.state = CommandState.executing

    # Inject one command into the scheduled stack and the other into the
    # incoming stack
    scheduler._scheduled_stack.add(command1)
    scheduler._scheduled_stack.add(command3)
    scheduler._incoming_stack.add(command2)

    # Verify only one command runs
    scheduler.run_once()
    assert not command1.did_exec
    assert command1.did_interrupt
    assert command2.did_init
    assert command3.did_exec


@mock.patch.object(Command, "initialize")
@mock.patch.object(Command, "execute")
@mock.patch.object(Command, "is_finished")
@mock.patch.object(Command, "end")
def test_subsystems_dont_default_incoming_commands(*_) -> None:
    """Verify subsystems detect incoming commands and don't default."""
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    class MyCommand(Command):

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

    class MySubsystem(Subsystem):

        periodic_counter = 0

        def periodic(self) -> None:
            self.periodic_counter += 1

        def reset(self) -> None:
            self.periodic_counter = 0

    subsystem = MySubsystem()
    subsystem2 = MySubsystem()
    command1 = MyCommand("Command1", subsystem)
    command2 = MyCommand("Command2", subsystem)
    command3 = MyCommand("Command3", subsystem2)
    command4 = MyCommand("Command4", subsystem2)

    subsystem.default_command = command1
    subsystem2.default_command = command3

    # Inject the commands to the incoming stack
    scheduler._incoming_stack.add(command2)
    scheduler._incoming_stack.add(command4)

    scheduler.run_once()

    assert subsystem.current_command == command2

    # Cancel command2
    scheduler.cancel(command2)

    assert subsystem.current_command == None


@mock.patch.object(Command, "initialize")
@mock.patch.object(Command, "execute")
@mock.patch.object(Command, "is_finished")
@mock.patch.object(Command, "end")
def test_forked_exec(*_) -> None:
    """Verify execute runs normally when forked."""
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    class MyAction(Action):

        state = False

        def poll(self) -> bool:
            return self.state

    class MyCommand(Command):

        did_exec = False

        def is_finished(self) -> bool:
            return False

        def execute(self) -> None:
            self.did_exec = True
            return None

    class MySubsystem(Subsystem):

        periodic_counter = 0

        def periodic(self) -> None:
            self.periodic_counter += 1

        def reset(self) -> None:
            self.periodic_counter = 0

    action = MyAction()
    subsystem = MySubsystem()
    command1 = MyCommand("Command1", subsystem)

    action.when_activated(command1)

    fut = scheduler.execute(fork=True)

    # Activate the action
    action.state = True

    # Wait 1 second
    time.sleep(1)

    scheduler.shutdown()
    while not fut.done():
        time.sleep(0.1)

    assert command1.did_exec


@mock.patch.object(Command, "initialize")
@mock.patch.object(Command, "execute")
@mock.patch.object(Command, "is_finished")
@mock.patch.object(Command, "end")
def test_exec(*_) -> None:
    """Verify execute runs when executed in the main thread."""
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    class MyAction(Action):

        state = False

        def poll(self) -> bool:
            return self.state

    class MyCommand(Command):

        did_exec = False

        def is_finished(self) -> bool:
            return False

        def execute(self) -> None:
            self.did_exec = True
            return None

    class MySubsystem(Subsystem):

        periodic_counter = 0

        def periodic(self) -> None:
            self.periodic_counter += 1

        def reset(self) -> None:
            self.periodic_counter = 0

    action = MyAction()
    subsystem = MySubsystem()
    command1 = MyCommand("Command1", subsystem)

    action.when_activated(command1)

    def quit_after_one_second(sched: Scheduler) -> None:
        time.sleep(1)
        sched.shutdown()

    thread = Thread(target=quit_after_one_second, args=(scheduler,))
    thread.start()

    # Activate the action
    action.state = True

    # Run the scheduler
    scheduler.execute()

    assert command1.did_exec


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
@mock.patch.object(Command, "initialize")
@mock.patch.object(Command, "execute")
@mock.patch.object(Command, "is_finished")
@mock.patch.object(Command, "end")
def test_exec_cancels_on_error(*_) -> None:
    """Verify the event loop cancels all commands when errors occur."""
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    class MyAction(Action):

        state = False

        def poll(self) -> bool:
            return self.state

    class MyCommand(Command):

        did_exec = False
        did_cancel = False

        def is_finished(self) -> bool:
            # Force an error condition
            raise ValueError("test error")

        def execute(self) -> None:
            self.did_exec = True
            return None

        def end(self, interrupted: bool) -> None:
            self.did_cancel = interrupted

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

    action.when_activated(command1)

    fut = scheduler.execute(fork=True)

    # Activate the action
    action.state = True

    # Wait 1 second
    time.sleep(1)

    scheduler.shutdown()
    while not fut.done():
        time.sleep(0.1)

    # command.is_finished is called before command.execute
    assert not command1.did_exec
    assert command1.did_cancel
    assert fut.exception() is not None

    action.when_held(command2)

    def quit_after_one_second(sched: Scheduler) -> None:
        time.sleep(1)
        sched.shutdown()

    thread = Thread(target=quit_after_one_second, args=(scheduler,))
    thread.start()

    # Activate the action
    action.state = True

    # Run the scheduler
    with pytest.raises(ValueError):
        scheduler.execute()

    assert not command2.did_exec
    assert command2.did_cancel


def test_sequential_command_group() -> None:
    """Verify sequential command group operates as expected."""
    scheduler = Scheduler.get_instance() or Scheduler()
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
    command3 = MyCommand("Command1", subsystem)
    command4 = MyCommand("Command2", subsystem)
    seq_command = SequentialCommandGroup("MySequentialCommandGroup", command1, command2)
    seq_command2 = SequentialCommandGroup("MySequentialCommandGroup2", command3, command4)

    subsystem.default_command = seq_command2

    action.when_activated(seq_command)
    action.state = True

    scheduler.run_once()

    assert subsystem.current_command == seq_command
    assert command1.did_init == 1
    assert command2.did_init == 0

    scheduler.run_once()

    assert command1.did_init == 1
    assert command1.did_finish == 1
    assert command1.did_exec == 1
    assert command2.did_init == 0

    command1.do_finish = True

    scheduler.run_once()

    assert command1.did_exec == 1
    assert command1.did_finish == 2
    assert command1.did_end == 1

    scheduler.run_once()

    assert command2.did_init == 1

    scheduler.run_once()

    assert command2.did_init == 1
    assert command2.did_exec == 1
    assert command2.did_finish == 1

    command2.do_finish = True

    scheduler.run_once()
    scheduler.run_once()

    assert command2.did_exec == 1
    assert command2.did_finish == 2
    assert command2.did_end == 1
    assert seq_command._end_of_sequence
    assert subsystem.current_command == None

    scheduler.run_once()

    assert subsystem.current_command == seq_command2
    assert command3.did_init == 1

    scheduler.run_once()

    assert command3.did_exec == 1
    assert command3.did_finish == 1

    # Cancel the sequential command
    subsystem.default_command = None
    scheduler.cancel(seq_command2)

    assert subsystem.current_command == None
    assert command3.did_interrupt == 1
    assert command4.did_init == 0
    assert command4.did_exec == 0
    assert command4.did_end == 0
    assert command4.did_finish == 0
    assert command4.did_interrupt == 0


def test_parallel_command_group() -> None:
    """Verify parallel command groups execute as expected."""
    scheduler = Scheduler.get_instance() or Scheduler()
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
        raise_error = False

        def handle_exception(self, *exc) -> bool:
            return True

        def initialize(self) -> None:
            self.did_init += 1

        def execute(self) -> None:
            self.did_exec += 1
            if self.raise_error:
                raise ValueError("test")

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
    action2 = MyAction()
    subsystem = MySubsystem()
    subsystem2 = MySubsystem()
    command1 = MyCommand("Command1", subsystem)
    command2 = MyCommand("Command2", subsystem2)
    command3 = MyCommand("Command3", subsystem)
    command4 = MyCommand("Command4", subsystem2)
    command5 = MyCommand("Command5", subsystem)
    command6 = MyCommand("Command6", subsystem2)
    par_command = ParallelCommandGroup("MyParallelCommandGroup", command1, command2)
    par_command2 = ParallelCommandGroup("MyParallelCommandGroup2", command3, command4)
    par_command3 = ParallelCommandGroup("MyParallelCommandGroup3", command5, command6)

    with pytest.raises(ValueError):
        ParallelCommandGroup("MyParallelCommandGroup", command1, command3)

    action.when_activated(par_command)
    action.state = True

    scheduler.run_once()

    # Allow the threads to execute for a little bit
    time.sleep(1)

    command1.do_finish = True
    command2.do_finish = True

    # Allow parallel threads to reach their barrier
    time.sleep(0.1)

    # Finish executing the parallel command and clean it up
    scheduler.run_once()

    assert command1.did_init == 1
    assert command1.did_exec > 0
    assert command1.did_finish > 0
    assert command1.did_end == 1

    assert command2.did_init == 1
    assert command2.did_exec > 0
    assert command2.did_finish > 0
    assert command2.did_end == 1

    action.when_held(par_command2)

    scheduler.run_once()

    # Allow the threads to execute for a little bit
    time.sleep(1)

    action.state = False

    scheduler.run_once()

    # Allow parallel threads to reach their barrier
    time.sleep(1)

    # Finish executing the parallel command and clean it up
    scheduler.run_once()

    assert command3.did_init == 1
    assert command3.did_exec > 0
    assert command3.did_finish > 0
    assert command3.did_end == 0
    assert command3.did_interrupt == 1

    assert command4.did_init == 1
    assert command4.did_exec > 0
    assert command4.did_finish > 0
    assert command4.did_end == 0
    assert command4.did_interrupt == 1

    action2.when_activated(par_command3)
    action2.state = True

    scheduler.run_once()

    # Allow threads to execute for a little bit
    time.sleep(1)

    # Raise an error in command 5
    command5.raise_error = True

    # Allow threads to catch error being raised
    time.sleep(0.1)

    # Ensure the group catches the error and handles it properly
    scheduler.run_once()

    assert command5.did_init == 1
    assert command5.did_exec > 0
    assert command5.did_finish > 0
    assert command5.did_end == 0
    assert command5.did_interrupt == 1

    assert command6.did_init == 1
    assert command6.did_exec > 0
    assert command6.did_finish > 0
    assert command6.did_end == 0
    assert command6.did_interrupt == 1


def test_callable_command_type() -> None:
    """Verify callables that return commands are executed correctly."""
    scheduler = Scheduler.get_instance() or Scheduler()
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

    action.when_activated(lambda: (
        SequentialCommandGroup(
            None,
            command1,
            command2,
        )
    ))

    # Activate the action
    action.state = True

    scheduler.run_once()

    assert isinstance(subsystem.current_command, SequentialCommandGroup)
    assert command1.did_init == 1

    scheduler.run_once()
    assert command1.did_init == 1
    assert command1.did_exec == 1
    assert command1.did_finish == 1

    command1.do_finish = True

    scheduler.run_once()

    assert command1.did_end == 1

    scheduler.run_once()

    assert command2.did_init == 1
