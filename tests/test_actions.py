from command_based_framework.actions import Action, Condition
from command_based_framework.commands import Command
from command_based_framework.scheduler import Scheduler

def test_bind_all_condition_types() -> None:
    """Verify all condition types bind properly."""
    scheduler = Scheduler.get_instance() or Scheduler()
    scheduler._reset_all_stacks()

    # Verify the stack is empty
    assert not scheduler._actions_stack

    class MyAction(Action):

        def poll(self) -> bool:
            return True

    class MyCommand(Command):

        def is_finished(self) -> bool:
            return True

        def execute(self) -> None:
            return None

    action = MyAction()
    command_cancel_when_activated = MyCommand()
    command_toggle_when_activated = MyCommand()
    command_when_activated = MyCommand()
    command_when_held = MyCommand()
    command_when_deactivated = MyCommand()

    action.cancel_when_activated(command_cancel_when_activated)
    action.toggle_when_activated(command_toggle_when_activated)
    action.when_activated(command_when_activated)
    action.when_deactivated(command_when_deactivated)
    action.when_held(command_when_held)

    assert scheduler._actions_stack[action][Condition.cancel_when_activated] == {command_cancel_when_activated}
    assert scheduler._actions_stack[action][Condition.toggle_when_activated] == {command_toggle_when_activated}
    assert scheduler._actions_stack[action][Condition.when_activated] == {command_when_activated}
    assert scheduler._actions_stack[action][Condition.when_deactivated] == {command_when_deactivated}
    assert scheduler._actions_stack[action][Condition.when_held] == {command_when_held}
