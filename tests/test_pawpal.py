"""Quick checks for the PawPal+ logic layer."""

from datetime import datetime, time, timedelta

from pawpal_system import Pet, Priority, Recurrence, Scheduler, Task, TaskType


def make_task(hour: int, title: str = "Walk", duration: int = 30) -> Task:
    """Build a simple one-off task at today's given hour."""
    due = datetime.combine(datetime.today().date(), time(hour, 0))
    return Task(title, TaskType.WALK, due, duration)


def test_mark_complete_changes_status():
    """mark_complete() flips a task from incomplete to complete."""
    task = make_task(9)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_count():
    """Adding a task to a pet increases that pet's task count."""
    pet = Pet(name="Rex", species="dog")
    assert len(pet.get_tasks()) == 0
    pet.add_task(make_task(8))
    assert len(pet.get_tasks()) == 1


def test_detect_conflicts_finds_overlap():
    """Two tasks sharing a time window are reported as a conflict."""
    scheduler = Scheduler([make_task(8, "Rex breakfast"),
                           make_task(8, "Whiskers breakfast")])
    assert len(scheduler.detect_conflicts()) == 1


def test_conflict_warning_is_a_string():
    """Conflicts surface as warning strings instead of raising."""
    scheduler = Scheduler([make_task(8, "A"), make_task(8, "B")])
    warnings = scheduler.conflict_warnings()
    assert len(warnings) == 1
    assert isinstance(warnings[0], str)


def test_filter_by_status_splits_completed_and_pending():
    """filter_by_status separates completed tasks from pending ones."""
    done, todo = make_task(8, "done"), make_task(9, "todo")
    done.mark_complete()
    scheduler = Scheduler([done, todo])
    assert scheduler.filter_by_status(True) == [done]
    assert scheduler.pending() == [todo]


def test_completing_daily_task_schedules_next_occurrence():
    """Completing a daily task auto-creates the next day's occurrence."""
    daily = Task("Walk", TaskType.WALK,
                 datetime.combine(datetime.today().date(), time(7, 30)),
                 recurrence=Recurrence.DAILY)
    scheduler = Scheduler([daily])
    next_task = scheduler.complete_task(daily)
    assert daily.completed is True
    assert next_task is not None
    assert next_task.due == daily.due + timedelta(days=1)
    assert next_task.completed is False
    assert len(scheduler.tasks) == 2
