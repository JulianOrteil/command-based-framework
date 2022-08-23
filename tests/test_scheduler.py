import pytest


def test_tracking_scheduler_instances() -> None:
    """Verify only one scheduler instance exists at any one time."""
    from command_based_framework.exceptions import SchedulerExistsError
    from command_based_framework.scheduler import Scheduler

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
