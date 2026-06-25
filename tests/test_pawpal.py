"""Quick checks for the PawPal+ logic layer."""

from datetime import datetime, time

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
