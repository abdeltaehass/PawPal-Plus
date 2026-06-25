"""PawPal+ — Smart Pet Care Management System (logic layer).

This module is the **logic layer** for PawPal+. It defines the domain model
(``Owner``, ``Pet``, ``Task``) and the scheduling engine (``Scheduler``) that
sorts, surfaces, and de-conflicts pet-care tasks.

Phase 1 deliverable: class *skeletons* only — attributes are fully declared,
but method bodies are intentionally left as stubs (``NotImplementedError``) to
be implemented in later phases. Keeping behaviour unimplemented here lets us
lock the architecture (names, relationships, signatures) before writing logic.

Design notes
------------
* ``Task`` and ``Pet`` are ``@dataclass`` types — they are mostly bundles of
  data with a few helper methods, so dataclasses remove boilerplate.
* ``Owner`` is also a dataclass (it owns a list of pets).
* ``Scheduler`` is a plain class — it is behaviour-heavy (algorithms) rather
  than data-heavy, so a dataclass would buy us little.
* Enums (``TaskType``, ``Priority``, ``Recurrence``) replace "magic strings"
  so invalid states are unrepresentable and sorting by priority is trivial.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class TaskType(Enum):
    """The kind of care a task represents."""

    FEEDING = "feeding"
    WALK = "walk"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    GROOMING = "grooming"
    OTHER = "other"


class Priority(Enum):
    """How urgent a task is. Integer values allow direct sorting."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Recurrence(Enum):
    """How often a task repeats. ``NONE`` means a one-off task."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# Module-level counter that hands out unique, stable task IDs.
_task_id_counter = itertools.count(1)


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Task:
    """A single unit of pet care (a feeding, a walk, a vet visit, ...).

    Attributes
    ----------
    title:
        Human-readable label, e.g. "Morning walk".
    task_type:
        Category of care (see :class:`TaskType`).
    due:
        When the task should happen.
    duration_minutes:
        Expected length; used for overlap/conflict detection.
    priority:
        Urgency used to order the day's agenda.
    recurrence:
        Repeat cadence; ``NONE`` for a one-off task.
    completed:
        Whether the owner has marked this task done.
    pet_name:
        Name of the pet this task belongs to (set when attached to a pet).
    task_id:
        Auto-assigned unique identifier.
    """

    title: str
    task_type: TaskType
    due: datetime
    duration_minutes: int = 30
    priority: Priority = Priority.MEDIUM
    recurrence: Recurrence = Recurrence.NONE
    completed: bool = False
    pet_name: Optional[str] = None
    task_id: int = field(default_factory=lambda: next(_task_id_counter), init=False)

    # -- behaviour stubs --------------------------------------------------
    def mark_complete(self) -> None:
        """Mark this task as done."""
        raise NotImplementedError

    def end_time(self) -> datetime:
        """Return ``due + duration``; the moment the task is expected to finish."""
        raise NotImplementedError

    def is_due_on(self, day: date) -> bool:
        """Return ``True`` if this task occurs on ``day`` (respecting recurrence)."""
        raise NotImplementedError

    def overlaps_with(self, other: "Task") -> bool:
        """Return ``True`` if this task's time window collides with ``other``'s."""
        raise NotImplementedError

    def next_occurrence(self) -> Optional["Task"]:
        """Return the next repeat of this task, or ``None`` if non-recurring."""
        raise NotImplementedError


@dataclass
class Pet:
    """An animal under an owner's care, holding its own list of tasks."""

    name: str
    species: str
    breed: str = ""
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        raise NotImplementedError

    def remove_task(self, task_id: int) -> None:
        """Detach a task from this pet by its id."""
        raise NotImplementedError

    def get_tasks(self) -> list[Task]:
        """Return all tasks attached to this pet."""
        raise NotImplementedError


@dataclass
class Owner:
    """A PawPal+ user who owns one or more pets."""

    name: str
    email: str = ""
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        raise NotImplementedError

    def remove_pet(self, name: str) -> None:
        """Remove a pet (and its tasks) by name."""
        raise NotImplementedError

    def get_pet(self, name: str) -> Optional[Pet]:
        """Look up one of this owner's pets by name."""
        raise NotImplementedError

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets (flattened)."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Scheduling engine
# ---------------------------------------------------------------------------
@dataclass
class Conflict:
    """Two tasks whose time windows overlap."""

    first: Task
    second: Task


class Scheduler:
    """Organizes and prioritizes tasks.

    The scheduler is the algorithmic heart of PawPal+: it sorts tasks, surfaces
    the day's agenda, expands recurring tasks into concrete occurrences, and
    flags scheduling conflicts.
    """

    def __init__(self, tasks: Optional[list[Task]] = None) -> None:
        self.tasks: list[Task] = tasks if tasks is not None else []

    def add_task(self, task: Task) -> None:
        """Register a task with the scheduler."""
        raise NotImplementedError

    def sort_by_priority(self) -> list[Task]:
        """Return tasks ordered by priority (highest first), tie-broken by time."""
        raise NotImplementedError

    def sort_by_time(self) -> list[Task]:
        """Return tasks ordered chronologically by due time."""
        raise NotImplementedError

    def tasks_for_day(self, day: date) -> list[Task]:
        """Return all tasks due on ``day`` (including recurring occurrences)."""
        raise NotImplementedError

    def today(self) -> list[Task]:
        """Return today's prioritized agenda."""
        raise NotImplementedError

    def upcoming(self, days: int = 7) -> list[Task]:
        """Return tasks due within the next ``days`` days."""
        raise NotImplementedError

    def detect_conflicts(self) -> list[Conflict]:
        """Return pairs of tasks whose time windows overlap."""
        raise NotImplementedError

    def expand_recurring(self, until: date) -> list[Task]:
        """Materialize recurring tasks into concrete occurrences up to ``until``."""
        raise NotImplementedError


if __name__ == "__main__":
    # A real CLI demo arrives in a later phase; this is just a smoke check
    # that the skeleton imports and constructs cleanly.
    owner = Owner(name="Sam", email="sam@example.com")
    rex = Pet(name="Rex", species="dog", breed="Beagle", age=4)
    walk = Task(
        title="Morning walk",
        task_type=TaskType.WALK,
        due=datetime.now(),
        recurrence=Recurrence.DAILY,
    )
    print(f"Built {owner.name}, {rex.name}, and task #{walk.task_id}: {walk.title}")
