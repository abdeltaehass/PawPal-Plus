"""PawPal+ — Smart Pet Care Management System (logic layer).

This module is the logic layer for PawPal+. It defines the domain model
(``Owner``, ``Pet``, ``Task``) and the scheduling engine (``Scheduler``) that
sorts, surfaces, and de-conflicts pet-care tasks.

Design notes
------------
* ``Task``, ``Pet``, and ``Owner`` are dataclasses — they are mostly bundles of
  data, so dataclasses remove constructor/repr boilerplate.
* ``Scheduler`` is a plain class — it is behaviour-heavy (algorithms) rather
  than data-heavy, so a dataclass would buy us little.
* Enums (``TaskType``, ``Priority``, ``Recurrence``) replace magic strings, so
  invalid states are unrepresentable and sorting by priority is trivial.
"""

from __future__ import annotations

import calendar
import itertools
import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
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


def _add_one_month(when: datetime) -> datetime:
    """Return ``when`` advanced by one calendar month, clamping the day if needed."""
    month = when.month % 12 + 1
    year = when.year + (when.month // 12)
    last_day = calendar.monthrange(year, month)[1]
    return when.replace(year=year, month=month, day=min(when.day, last_day))


def _advance(when: datetime, recurrence: "Recurrence") -> datetime:
    """Return the next occurrence time for ``when`` under the given recurrence."""
    if recurrence is Recurrence.DAILY:
        return when + timedelta(days=1)
    if recurrence is Recurrence.WEEKLY:
        return when + timedelta(weeks=1)
    if recurrence is Recurrence.MONTHLY:
        return _add_one_month(when)
    return when


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Task:
    """A single unit of pet care (a feeding, a walk, a vet visit, ...)."""

    title: str
    task_type: TaskType
    due: datetime
    duration_minutes: int = 30
    priority: Priority = Priority.MEDIUM
    recurrence: Recurrence = Recurrence.NONE
    completed: bool = False
    pet_name: Optional[str] = None
    task_id: int = field(default_factory=lambda: next(_task_id_counter), init=False)

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def end_time(self) -> datetime:
        """Return the moment the task is expected to finish (due + duration)."""
        return self.due + timedelta(minutes=self.duration_minutes)

    def is_due_on(self, day: date) -> bool:
        """Return ``True`` if this task occurs on ``day``, respecting recurrence."""
        start = self.due.date()
        if self.recurrence is Recurrence.NONE:
            return day == start
        if day < start:
            return False
        if self.recurrence is Recurrence.DAILY:
            return True
        if self.recurrence is Recurrence.WEEKLY:
            return day.weekday() == start.weekday()
        if self.recurrence is Recurrence.MONTHLY:
            return day.day == start.day
        return False

    def overlaps_with(self, other: "Task") -> bool:
        """Return ``True`` if this task's time window collides with ``other``'s."""
        return self.due < other.end_time() and other.due < self.end_time()

    def next_occurrence(self) -> Optional["Task"]:
        """Return the next repeat of this task, or ``None`` if non-recurring."""
        if self.recurrence is Recurrence.NONE:
            return None
        return Task(
            title=self.title,
            task_type=self.task_type,
            due=_advance(self.due, self.recurrence),
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recurrence=self.recurrence,
            completed=False,
            pet_name=self.pet_name,
        )

    def __str__(self) -> str:
        """Return a compact, human-readable one-line summary of the task."""
        status = "✓" if self.completed else "○"
        when = self.due.strftime("%I:%M %p").lstrip("0")
        owner = f"  [{self.pet_name}]" if self.pet_name else ""
        repeat = "" if self.recurrence is Recurrence.NONE else f"  ↻{self.recurrence.value}"
        return f"{status} {when:>8}  {self.title} ({self.task_type.value}){owner}{repeat}"

    def to_dict(self) -> dict:
        """Serialize this task to a JSON-friendly dictionary."""
        return {
            "title": self.title,
            "task_type": self.task_type.value,
            "due": self.due.isoformat(),
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.name,
            "recurrence": self.recurrence.value,
            "completed": self.completed,
            "pet_name": self.pet_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuild a task from a dictionary produced by ``to_dict``."""
        return cls(
            title=data["title"],
            task_type=TaskType(data["task_type"]),
            due=datetime.fromisoformat(data["due"]),
            duration_minutes=data["duration_minutes"],
            priority=Priority[data["priority"]],
            recurrence=Recurrence(data["recurrence"]),
            completed=data["completed"],
            pet_name=data.get("pet_name"),
        )


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
        """Attach a care task to this pet and stamp it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        """Detach a task from this pet by its id."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks(self) -> list[Task]:
        """Return a copy of all tasks attached to this pet."""
        return list(self.tasks)

    def to_dict(self) -> dict:
        """Serialize this pet and its tasks to a dictionary."""
        return {
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "age": self.age,
            "notes": self.notes,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Rebuild a pet (and its tasks) from a dictionary."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            breed=data.get("breed", ""),
            age=data.get("age", 0),
            notes=data.get("notes", ""),
        )
        pet.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return pet


@dataclass
class Owner:
    """A PawPal+ user who owns one or more pets."""

    name: str
    email: str = ""
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove a pet (and its tasks) by name."""
        self.pets = [p for p in self.pets if p.name != name]

    def get_pet(self, name: str) -> Optional[Pet]:
        """Look up one of this owner's pets by name, or ``None`` if absent."""
        return next((p for p in self.pets if p.name == name), None)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets, flattened."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def to_dict(self) -> dict:
        """Serialize this owner and all pets/tasks to a dictionary."""
        return {
            "name": self.name,
            "email": self.email,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Rebuild an owner (with pets and tasks) from a dictionary."""
        owner = cls(name=data["name"], email=data.get("email", ""))
        owner.pets = [Pet.from_dict(p) for p in data.get("pets", [])]
        return owner


# ---------------------------------------------------------------------------
# Scheduling engine
# ---------------------------------------------------------------------------
@dataclass
class Conflict:
    """Two tasks whose time windows overlap."""

    first: Task
    second: Task

    def __str__(self) -> str:
        """Return a readable description of the clashing pair."""
        return f"{self.first.title} clashes with {self.second.title}"


class Scheduler:
    """The 'brain' that retrieves, organizes, and manages tasks across pets."""

    def __init__(self, tasks: Optional[list[Task]] = None) -> None:
        self.tasks: list[Task] = list(tasks) if tasks is not None else []

    @classmethod
    def from_owner(cls, owner: Owner) -> "Scheduler":
        """Build a scheduler populated with every task across the owner's pets."""
        return cls(owner.all_tasks())

    def add_task(self, task: Task) -> None:
        """Register a task with the scheduler."""
        self.tasks.append(task)

    def sort_by_priority(self) -> list[Task]:
        """Return tasks ordered by priority (highest first), tie-broken by time."""
        return sorted(self.tasks, key=lambda t: (-t.priority.value, t.due))

    def sort_by_time(self) -> list[Task]:
        """Return tasks ordered chronologically by due time."""
        return sorted(self.tasks, key=lambda t: t.due)

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return only the tasks belonging to the named pet."""
        return [t for t in self.tasks if t.pet_name == pet_name]

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return tasks matching the given completion state."""
        return [t for t in self.tasks if t.completed == completed]

    def pending(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        return self.filter_by_status(False)

    def tasks_for_day(self, day: date) -> list[Task]:
        """Return tasks due on ``day`` (including recurring), ordered by time."""
        due = [t for t in self.tasks if t.is_due_on(day)]
        return sorted(due, key=lambda t: t.due.time())

    def today(self) -> list[Task]:
        """Return today's schedule in chronological order."""
        return self.tasks_for_day(date.today())

    def upcoming(self, days: int = 7) -> list[Task]:
        """Return unique tasks due within the next ``days`` days, ordered by date."""
        start = date.today()
        result: list[Task] = []
        seen: set[int] = set()
        for offset in range(days + 1):
            for task in self.tasks_for_day(start + timedelta(days=offset)):
                if task.task_id not in seen:
                    seen.add(task.task_id)
                    result.append(task)
        return result

    def next_available_slot(
        self,
        day: date,
        duration_minutes: int,
        start_hour: int = 8,
        end_hour: int = 20,
    ) -> Optional[datetime]:
        """Return the earliest free start time on ``day`` that fits a task of the
        given length within working hours, or ``None`` if the day is full.

        Greedy sweep: walk the day's tasks in time order, tracking a ``cursor``
        at the end of the latest commitment so far; the first gap >= the needed
        duration wins.
        """
        need = timedelta(minutes=duration_minutes)
        window_start = datetime.combine(day, time(start_hour))
        window_end = datetime.combine(day, time(end_hour))

        busy = sorted(
            (t for t in self.tasks_for_day(day) if not t.completed),
            key=lambda t: t.due.time(),
        )
        cursor = window_start
        for task in busy:
            start = datetime.combine(day, task.due.time())
            end = start + timedelta(minutes=task.duration_minutes)
            if start - cursor >= need:
                return cursor
            cursor = max(cursor, end)
        return cursor if window_end - cursor >= need else None

    def detect_conflicts(self) -> list[Conflict]:
        """Return pairs of active tasks whose scheduled time windows overlap."""
        active = [t for t in self.tasks if not t.completed]
        return [
            Conflict(a, b)
            for a, b in itertools.combinations(active, 2)
            if a.overlaps_with(b)
        ]

    def conflict_warnings(self) -> list[str]:
        """Return human-readable warning strings (never raises) for each conflict."""
        warnings: list[str] = []
        for conflict in self.detect_conflicts():
            a, b = conflict.first, conflict.second
            when = a.due.strftime("%I:%M %p").lstrip("0")
            who = a.pet_name if a.pet_name == b.pet_name else f"{a.pet_name} & {b.pet_name}"
            warnings.append(f"⚠ {when}: '{a.title}' overlaps '{b.title}' ({who})")
        return warnings

    def expand_recurring(self, until: date) -> list[Task]:
        """Materialize recurring tasks into concrete occurrences up to ``until``."""
        occurrences: list[Task] = []
        for task in self.tasks:
            current: Optional[Task] = task
            while current is not None and current.due.date() <= until:
                occurrences.append(current)
                current = current.next_occurrence()
        return sorted(occurrences, key=lambda t: t.due)

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task done; if it recurs, schedule and return its next occurrence."""
        task.mark_complete()
        if task.recurrence is Recurrence.NONE:
            return None
        upcoming = task.next_occurrence()
        if upcoming is not None:
            self.add_task(upcoming)
        return upcoming


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
DATA_FILE = "data.json"


def save_to_json(owner: Owner, path: str = DATA_FILE) -> None:
    """Persist an owner (with all pets and tasks) to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(owner.to_dict(), fh, indent=2)


def load_from_json(path: str = DATA_FILE) -> Owner:
    """Load an owner from a JSON file, or return a fresh empty owner if absent."""
    if not os.path.exists(path):
        return Owner(name="You")
    with open(path, "r", encoding="utf-8") as fh:
        return Owner.from_dict(json.load(fh))
