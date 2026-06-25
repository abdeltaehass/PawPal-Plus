"""Command-line demo for PawPal+.

Builds a small household of pets and tasks, then exercises the Scheduler's
algorithmic layer: sorting, filtering, conflict warnings, and recurring tasks.
Run with: ``python main.py``.
"""

from datetime import datetime, time

from pawpal_system import (
    Owner,
    Pet,
    Priority,
    Recurrence,
    Scheduler,
    Task,
    TaskType,
)


def at(hour: int, minute: int = 0) -> datetime:
    """Return a datetime for today at the given hour/minute."""
    return datetime.combine(datetime.today().date(), time(hour, minute))


def banner(title: str) -> None:
    """Print a titled section header."""
    print(f"\n{title}")
    print("-" * len(title))


def build_household() -> Owner:
    """Create an owner with two pets and a handful of care tasks."""
    owner = Owner(name="Sam", email="sam@example.com")

    rex = Pet(name="Rex", species="dog", breed="Beagle", age=4)
    whiskers = Pet(name="Whiskers", species="cat", breed="Tabby", age=2)
    owner.add_pet(rex)
    owner.add_pet(whiskers)

    # Added deliberately OUT OF ORDER to show sort_by_time() at work.
    rex.add_task(Task("Evening meds", TaskType.MEDICATION, at(19, 0), 5,
                      Priority.HIGH, Recurrence.DAILY))
    rex.add_task(Task("Morning walk", TaskType.WALK, at(7, 30), 30,
                      Priority.MEDIUM, Recurrence.DAILY))
    rex.add_task(Task("Vet checkup", TaskType.APPOINTMENT, at(14, 0), 60,
                      Priority.CRITICAL, Recurrence.NONE))
    rex.add_task(Task("Breakfast", TaskType.FEEDING, at(8, 0), 15,
                      Priority.HIGH, Recurrence.DAILY))
    # Same 8:00 slot as Rex's breakfast -> an intentional conflict.
    whiskers.add_task(Task("Breakfast", TaskType.FEEDING, at(8, 0), 15,
                           Priority.HIGH, Recurrence.DAILY))

    return owner


def main() -> None:
    owner = build_household()
    scheduler = Scheduler.from_owner(owner)

    print(f"PawPal+ — {owner.name}'s household "
          f"({len(owner.pets)} pets, {len(owner.all_tasks())} tasks)")

    # --- Sorting: tasks were added out of order ---
    banner("Sorted by Time")
    for task in scheduler.sort_by_time():
        print(task)

    # --- Filtering: by pet, then by status ---
    banner("Filter — Rex's tasks")
    for task in scheduler.filter_by_pet("Rex"):
        print(task)

    # --- Conflict detection: warnings, not crashes ---
    banner("Conflict Warnings")
    warnings = scheduler.conflict_warnings()
    print("\n".join(warnings) if warnings else "None — schedule is clear.")

    # --- Recurring tasks: completing a daily task rolls it forward ---
    banner("Recurring — complete a daily task")
    walk = next(t for t in scheduler.tasks if t.title == "Morning walk")
    next_walk = scheduler.complete_task(walk)
    print(f"Completed: {walk.title}  ({walk.due:%a %I:%M %p})")
    print(f"Auto-scheduled: {next_walk.title}  ({next_walk.due:%a %I:%M %p})")

    # --- Filtering by status reflects the change ---
    banner("Filter — by status")
    print("Completed:", [t.title for t in scheduler.filter_by_status(True)])
    print(f"Pending:   {len(scheduler.pending())} tasks")

    print()


if __name__ == "__main__":
    main()
