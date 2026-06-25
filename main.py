"""Command-line demo for PawPal+.

Builds a small household of pets and tasks, then exercises the Scheduler to
print today's schedule, a priority view, detected conflicts, and the week
ahead. Run with: ``python main.py``.
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

    rex.add_task(Task("Morning walk", TaskType.WALK, at(7, 30), 30,
                      Priority.MEDIUM, Recurrence.DAILY))
    rex.add_task(Task("Breakfast", TaskType.FEEDING, at(8, 0), 15,
                      Priority.HIGH, Recurrence.DAILY))
    rex.add_task(Task("Vet checkup", TaskType.APPOINTMENT, at(14, 0), 60,
                      Priority.CRITICAL, Recurrence.NONE))

    whiskers.add_task(Task("Breakfast", TaskType.FEEDING, at(8, 0), 15,
                           Priority.HIGH, Recurrence.DAILY))
    whiskers.add_task(Task("Evening meds", TaskType.MEDICATION, at(19, 0), 5,
                           Priority.HIGH, Recurrence.DAILY))

    return owner


def main() -> None:
    owner = build_household()
    scheduler = Scheduler.from_owner(owner)

    print(f"PawPal+ — {owner.name}'s household "
          f"({len(owner.pets)} pets, {len(owner.all_tasks())} tasks)")

    banner("Today's Schedule")
    for task in scheduler.today():
        print(task)

    banner("By Priority")
    for task in scheduler.sort_by_priority():
        print(f"{task.priority.name:>8}  {task.title}  ({task.pet_name})")

    banner("Scheduling Conflicts")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for conflict in conflicts:
            both = f"{conflict.first.pet_name} & {conflict.second.pet_name}"
            print(f"⚠  {conflict}  at "
                  f"{conflict.first.due.strftime('%I:%M %p').lstrip('0')}  ({both})")
    else:
        print("None — schedule is clear.")

    banner("Mark a Task Complete")
    walk = scheduler.today()[0]
    walk.mark_complete()
    print(f"Marked done: {walk}")

    print()


if __name__ == "__main__":
    main()
