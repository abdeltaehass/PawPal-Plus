"""Automated tests for the PawPal+ logic layer.

Organized into happy-path checks (sorting, filtering, recurrence, conflicts)
and edge cases (empty pets/owners/schedulers, one-off tasks, non-overlapping
times).
"""

from datetime import datetime, time, timedelta

from pawpal_system import (
    Owner,
    Pet,
    Priority,
    Recurrence,
    Scheduler,
    Task,
    TaskType,
    load_from_json,
    save_to_json,
)


def at(hour: int, minute: int = 0) -> datetime:
    """Return today at the given hour/minute."""
    return datetime.combine(datetime.today().date(), time(hour, minute))


def make_task(hour: int, title: str = "Walk", duration: int = 30) -> Task:
    """Build a simple one-off task at today's given hour."""
    return Task(title, TaskType.WALK, at(hour), duration)


# ---------------------------------------------------------------------------
# Core behavior
# ---------------------------------------------------------------------------
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


def test_owner_flattens_tasks_across_pets():
    """Owner.all_tasks() collects tasks from every pet."""
    owner = Owner(name="Sam")
    rex, cat = Pet("Rex", "dog"), Pet("Whiskers", "cat")
    owner.add_pet(rex)
    owner.add_pet(cat)
    rex.add_task(make_task(8))
    cat.add_task(make_task(9))
    assert len(owner.all_tasks()) == 2


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------
def test_sort_by_time_orders_chronologically():
    """sort_by_time() returns tasks earliest-first regardless of insertion order."""
    scheduler = Scheduler([make_task(19, "eve"), make_task(7, "dawn"),
                           make_task(14, "noon"), make_task(8, "morn")])
    ordered = [t.due.hour for t in scheduler.sort_by_time()]
    assert ordered == [7, 8, 14, 19]


def test_sort_by_priority_puts_most_urgent_first():
    """sort_by_priority() ranks CRITICAL above lower priorities."""
    low = Task("low", TaskType.OTHER, at(9), priority=Priority.LOW)
    critical = Task("critical", TaskType.APPOINTMENT, at(10), priority=Priority.CRITICAL)
    medium = Task("medium", TaskType.WALK, at(11), priority=Priority.MEDIUM)
    scheduler = Scheduler([low, critical, medium])
    assert scheduler.sort_by_priority()[0] is critical


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
def test_filter_by_pet_returns_only_that_pet():
    """filter_by_pet() returns only tasks stamped with the given pet name."""
    owner = Owner(name="Sam")
    rex, cat = Pet("Rex", "dog"), Pet("Whiskers", "cat")
    owner.add_pet(rex)
    owner.add_pet(cat)
    rex.add_task(make_task(8))
    cat.add_task(make_task(9))
    scheduler = Scheduler.from_owner(owner)
    assert all(t.pet_name == "Rex" for t in scheduler.filter_by_pet("Rex"))
    assert len(scheduler.filter_by_pet("Rex")) == 1


def test_filter_by_status_splits_completed_and_pending():
    """filter_by_status separates completed tasks from pending ones."""
    done, todo = make_task(8, "done"), make_task(9, "todo")
    done.mark_complete()
    scheduler = Scheduler([done, todo])
    assert scheduler.filter_by_status(True) == [done]
    assert scheduler.pending() == [todo]


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------
def test_detect_conflicts_finds_exact_duplicate_time():
    """Two tasks at the exact same time are reported as a conflict."""
    scheduler = Scheduler([make_task(8, "Rex breakfast"),
                           make_task(8, "Whiskers breakfast")])
    assert len(scheduler.detect_conflicts()) == 1


def test_overlapping_durations_conflict():
    """An 8:00 (60 min) task overlaps an 8:30 task -> one conflict."""
    scheduler = Scheduler([make_task(8, "long", duration=60),
                           Task("mid", TaskType.WALK, at(8, 30), 30)])
    assert len(scheduler.detect_conflicts()) == 1


def test_separate_times_do_not_conflict():
    """Non-overlapping tasks produce no conflicts."""
    scheduler = Scheduler([make_task(8, "a", duration=30),
                           make_task(9, "b", duration=30)])
    assert scheduler.detect_conflicts() == []


def test_conflict_warning_is_a_string():
    """Conflicts surface as warning strings instead of raising."""
    scheduler = Scheduler([make_task(8, "A"), make_task(8, "B")])
    warnings = scheduler.conflict_warnings()
    assert len(warnings) == 1
    assert isinstance(warnings[0], str)


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------
def test_completing_daily_task_schedules_next_day():
    """Completing a daily task auto-creates the next day's occurrence."""
    daily = Task("Walk", TaskType.WALK, at(7, 30), recurrence=Recurrence.DAILY)
    scheduler = Scheduler([daily])
    next_task = scheduler.complete_task(daily)
    assert daily.completed is True
    assert next_task is not None
    assert next_task.due == daily.due + timedelta(days=1)
    assert next_task.completed is False
    assert len(scheduler.tasks) == 2


def test_completing_weekly_task_advances_seven_days():
    """Completing a weekly task schedules the next occurrence a week later."""
    weekly = Task("Bath", TaskType.GROOMING, at(10), recurrence=Recurrence.WEEKLY)
    scheduler = Scheduler([weekly])
    next_task = scheduler.complete_task(weekly)
    assert next_task.due == weekly.due + timedelta(weeks=1)


def test_completing_one_off_task_creates_no_new_task():
    """A non-recurring task does not spawn a follow-up on completion."""
    one_off = make_task(8)  # Recurrence.NONE by default
    scheduler = Scheduler([one_off])
    assert scheduler.complete_task(one_off) is None
    assert len(scheduler.tasks) == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
def test_pet_with_no_tasks_is_empty():
    """A freshly created pet has an empty task list."""
    assert Pet("Rex", "dog").get_tasks() == []


def test_owner_with_no_pets_has_no_tasks():
    """An owner with no pets reports no tasks."""
    assert Owner("Sam").all_tasks() == []


def test_empty_scheduler_is_safe():
    """An empty scheduler returns empty results, never raising."""
    scheduler = Scheduler([])
    assert scheduler.today() == []
    assert scheduler.detect_conflicts() == []
    assert scheduler.conflict_warnings() == []


# ---------------------------------------------------------------------------
# Optional extensions
# ---------------------------------------------------------------------------
def test_next_available_slot_finds_first_gap():
    """next_available_slot returns the earliest gap that fits the duration."""
    scheduler = Scheduler([make_task(8, "a", duration=30),
                           make_task(10, "b", duration=30)])
    slot = scheduler.next_available_slot(datetime.today().date(), 60)
    assert slot == at(8, 30)


def test_next_available_slot_returns_none_when_full():
    """A task filling the whole working window leaves no slot."""
    scheduler = Scheduler([make_task(8, "all day", duration=12 * 60)])
    assert scheduler.next_available_slot(datetime.today().date(), 30) is None


def test_json_round_trip_preserves_data(tmp_path):
    """save_to_json then load_from_json restores owner, pets, and task fields."""
    owner = Owner("Sam", "sam@example.com")
    rex = Pet("Rex", "dog", "Beagle", 4, "good boy")
    owner.add_pet(rex)
    rex.add_task(Task("Walk", TaskType.WALK, at(7, 30), 30,
                      Priority.HIGH, Recurrence.DAILY))
    path = tmp_path / "data.json"

    save_to_json(owner, str(path))
    loaded = load_from_json(str(path))

    assert loaded.name == "Sam"
    assert len(loaded.pets) == 1
    assert loaded.pets[0].notes == "good boy"
    task = loaded.all_tasks()[0]
    assert task.title == "Walk"
    assert task.priority is Priority.HIGH
    assert task.recurrence is Recurrence.DAILY
    assert task.due == at(7, 30)


def test_load_from_json_missing_file_returns_empty_owner(tmp_path):
    """Loading a non-existent file yields a fresh empty owner instead of raising."""
    owner = load_from_json(str(tmp_path / "nope.json"))
    assert isinstance(owner, Owner)
    assert owner.pets == []
