"""Command-line demo for PawPal+.

Builds a small household of pets and tasks, then exercises the Scheduler's
algorithmic layer and the optional extensions: priority scheduling, a
next-available-slot finder, formatted (emoji + table) output, and JSON
persistence. Run with: ``python main.py``.
"""

import os
import tempfile
from datetime import date, datetime, time

from tabulate import tabulate

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

# Challenge 4: an emoji per task type for friendlier output.
# (Plain double-width emojis chosen so the table columns line up.)
ICONS = {
    TaskType.FEEDING: "🥣",
    TaskType.WALK: "🐕",
    TaskType.MEDICATION: "💊",
    TaskType.APPOINTMENT: "🏥",
    TaskType.GROOMING: "🛁",
    TaskType.OTHER: "📌",
}


def at(hour: int, minute: int = 0) -> datetime:
    """Return a datetime for today at the given hour/minute."""
    return datetime.combine(datetime.today().date(), time(hour, minute))


def banner(title: str) -> None:
    """Print a titled section header."""
    print(f"\n{title}")
    print("-" * len(title))


def render(tasks: list[Task]) -> str:
    """Render tasks as a tabulate grid with task-type icons (Challenge 4)."""
    rows = [
        [
            ICONS[t.task_type],
            t.due.strftime("%I:%M %p").lstrip("0"),
            t.title,
            t.pet_name,
            t.priority.name.title(),
            "—" if t.recurrence is Recurrence.NONE else t.recurrence.value,
            "✅" if t.completed else "",
        ]
        for t in tasks
    ]
    headers = ["", "Time", "Task", "Pet", "Priority", "Repeat", "Done"]
    return tabulate(rows, headers=headers, tablefmt="rounded_outline")


def build_household() -> Owner:
    """Create an owner with two pets and a handful of care tasks."""
    owner = Owner(name="Sam", email="sam@example.com")

    rex = Pet(name="Rex", species="dog", breed="Beagle", age=4)
    whiskers = Pet(name="Whiskers", species="cat", breed="Tabby", age=2)
    owner.add_pet(rex)
    owner.add_pet(whiskers)

    # Added deliberately OUT OF ORDER to show sorting at work.
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

    # --- Sorting by time (tasks were added out of order) ---
    banner("Today — sorted by time")
    print(render(scheduler.sort_by_time()))

    # --- Challenge 3: priority-first scheduling ---
    banner("Today — by priority, then time")
    print(render(scheduler.sort_by_priority()))

    # --- Conflict detection: warnings, not crashes ---
    banner("Conflict Warnings")
    warnings = scheduler.conflict_warnings()
    print("\n".join(warnings) if warnings else "None — schedule is clear.")

    # --- Challenge 1: next available slot ---
    banner("Next Available Slot")
    slot = scheduler.next_available_slot(date.today(), duration_minutes=45)
    if slot:
        print(f"Earliest free 45-min slot today: {slot:%I:%M %p}".replace(" 0", " "))
    else:
        print("No 45-min slot free in working hours today.")

    # --- Recurring tasks: completing a daily task rolls it forward ---
    banner("Recurring — complete a daily task")
    walk = next(t for t in scheduler.tasks if t.title == "Morning walk")
    next_walk = scheduler.complete_task(walk)
    print(f"Completed: {walk.title}  ({walk.due:%a %I:%M %p})")
    print(f"Auto-scheduled: {next_walk.title}  ({next_walk.due:%a %I:%M %p})")

    # --- Challenge 2: persistence round-trip ---
    banner("Persistence")
    path = os.path.join(tempfile.gettempdir(), "pawpal_demo.json")
    save_to_json(owner, path)
    reloaded = load_from_json(path)
    print(f"Saved {len(owner.all_tasks())} tasks to {path}")
    print(f"Reloaded {len(reloaded.all_tasks())} tasks "
          f"for {len(reloaded.pets)} pets: {[p.name for p in reloaded.pets]}")
    os.remove(path)

    print()


if __name__ == "__main__":
    main()
