# 🐾 PawPal+

**PawPal+** is a smart pet care management system that helps owners keep their
furry friends happy and healthy. It tracks daily routines — feedings, walks,
medications, and appointments — and uses algorithmic logic to organize and
prioritize tasks.

## Scenario

Pet owners juggle a surprising number of recurring responsibilities: the dog
needs two walks a day, the cat takes medication every morning, the vet
appointment is next Tuesday, and dinner is at 6pm sharp. Forgetting any one of
these has real consequences for an animal's wellbeing.

PawPal+ acts as a personal assistant for pet care. Owners register their pets,
attach care tasks to each pet, and let the system's **Scheduler** sort, surface,
and de-conflict what needs to happen — today and in the days ahead.

## Core Actions

A user of PawPal+ should be able to:

1. **Register a pet** under their account (name, species, breed, age, notes).
2. **Schedule a care task** for a pet (feeding, walk, medication, appointment),
   including one-off and recurring tasks.
3. **See today's agenda** — a prioritized, conflict-aware list of what's due.

## Architecture

The system is split into two layers:

| Layer            | File                | Responsibility                                  |
| ---------------- | ------------------- | ----------------------------------------------- |
| **Logic layer**  | `pawpal_system.py`  | OOP domain model + scheduling algorithms        |
| **UI layer**     | `app.py` (Streamlit)| Thin presentation layer that delegates to logic |

This is a **CLI-first** project: the backend logic in `pawpal_system.py` is
designed and verified independently (via a demo script and `pytest`) before any
UI is connected.

### Domain model

```
Owner ──owns──▶ Pet ──has──▶ Task
                              ▲
                    Scheduler ┘ (manages / prioritizes)
```

See [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd) for the full UML class
diagram.

## Getting Started

```bash
# (optional) create a virtual environment
python -m venv .venv && source .venv/bin/activate

# install test dependency
pip install -r requirements.txt

# run the CLI demo
python main.py

# launch the web app
streamlit run app.py

# run the tests
python -m pytest
```

## Sample Output

Running `python main.py`:

```text
PawPal+ — Sam's household (2 pets, 5 tasks)

Sorted by Time
--------------
○  7:30 AM  Morning walk (walk)  [Rex]  ↻daily
○  8:00 AM  Breakfast (feeding)  [Rex]  ↻daily
○  8:00 AM  Breakfast (feeding)  [Whiskers]  ↻daily
○  2:00 PM  Vet checkup (appointment)  [Rex]
○  7:00 PM  Evening meds (medication)  [Rex]  ↻daily

Filter — Rex's tasks
--------------------
○  7:00 PM  Evening meds (medication)  [Rex]  ↻daily
○  7:30 AM  Morning walk (walk)  [Rex]  ↻daily
○  2:00 PM  Vet checkup (appointment)  [Rex]
○  8:00 AM  Breakfast (feeding)  [Rex]  ↻daily

Conflict Warnings
-----------------
⚠ 8:00 AM: 'Breakfast' overlaps 'Breakfast' (Rex & Whiskers)

Recurring — complete a daily task
---------------------------------
Completed: Morning walk  (Thu 07:30 AM)
Auto-scheduled: Morning walk  (Fri 07:30 AM)

Filter — by status
------------------
Completed: ['Morning walk']
Pending:   5 tasks
```

## Smarter Scheduling

The `Scheduler` is the algorithmic layer. Each feature maps to a named method in
[`pawpal_system.py`](pawpal_system.py):

| Feature | Method(s) | Notes |
| ------- | --------- | ----- |
| **Sort by time** | `Scheduler.sort_by_time()` | Orders tasks chronologically. Sorts on `datetime` objects directly (not `"HH:MM"` strings), so dates and times compare correctly. |
| **Sort by priority** | `Scheduler.sort_by_priority()` | Highest urgency first, ties broken by time. |
| **Filter by pet** | `Scheduler.filter_by_pet(name)` | Returns just that pet's tasks. |
| **Filter by status** | `Scheduler.filter_by_status(done)`, `Scheduler.pending()` | Split completed vs. outstanding tasks. |
| **Conflict detection** | `Scheduler.detect_conflicts()`, `Scheduler.conflict_warnings()` | Flags overlapping time windows via `Task.overlaps_with()` (duration-aware). `conflict_warnings()` returns readable strings and never raises. |
| **Recurring tasks** | `Task.next_occurrence()`, `Scheduler.complete_task(task)`, `Scheduler.expand_recurring(until)` | Completing a daily/weekly/monthly task auto-schedules its next occurrence using `timedelta`. |

## Project status

- [x] **Phase 1** — System design (UML + class skeletons)
- [x] **Phase 2** — OOP logic, CLI demo, and initial tests
- [x] **Phase 3** — Streamlit UI (`app.py`) wired to the logic layer
- [ ] Next — refinements, final UML, and reflection

## Design reflections

Design decisions and AI-collaboration notes are tracked in
[`reflection.md`](reflection.md).
