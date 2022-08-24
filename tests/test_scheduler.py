import math

import pytest

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
