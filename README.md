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

## Features

- 🐾 **Pet & task management** — register pets and attach care tasks (feeding,
  walk, medication, appointment, grooming) with a time, duration, and priority.
- ⏱️ **Sorting** — order tasks by time (`sort_by_time`) or by urgency
  (`sort_by_priority`).
- 🔎 **Filtering** — slice tasks by pet (`filter_by_pet`) or completion status
  (`filter_by_status` / `pending`).
- ⚠️ **Conflict warnings** — duration-aware overlap detection that surfaces
  human-readable warnings instead of crashing.
- 🔁 **Recurring tasks** — daily / weekly / monthly tasks that automatically roll
  to their next occurrence when completed.
- 📅 **Today & upcoming views** — see what's due today or across the next week.
- 🖥️ **Two front ends** — a Streamlit web UI (`app.py`) and a CLI demo
  (`main.py`), both over the same logic layer, with a 17-test `pytest` suite.

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

See [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) for the full UML class
diagram of the finished system (the Phase 1 draft is preserved at
[`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd)).

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

## Demo Walkthrough

### What you can do in the app (`streamlit run app.py`)

- **Add a pet** from the sidebar (name, species, breed, age, notes).
- **Schedule a task** for any pet — choose a type, date, time, duration,
  priority, and how often it repeats.
- **Watch the metrics** update live: pets, tasks due today, and active conflicts.
- **Work today's list**: tick a task to complete it; recurring tasks
  automatically roll forward to their next date.
- **Browse all tasks** in a sortable table, filtered by pet and/or status.
- **See conflict warnings** surfaced as one friendly callout whenever two tasks
  overlap in time.

### Example workflow

1. Add a pet **Rex** (dog).
2. Schedule **"Morning walk"** at 7:30 AM, repeating **Daily**.
3. Schedule **"Breakfast"** at 8:00 AM for Rex and another **"Breakfast"** at
   8:00 AM for a second pet, **Whiskers** → PawPal+ flags the 8:00 AM overlap.
4. Open **Today** and tick *Morning walk* → it's marked done and tomorrow's walk
   is scheduled automatically.

### Scheduler behaviors on display

- **Sorting** — today's list and the all-tasks table come back in time order.
- **Filtering** — narrow the table by pet or by completed/pending status.
- **Conflict warnings** — overlapping windows are detected and explained.
- **Recurrence** — completing a daily/weekly/monthly task spawns the next one.

### Sample CLI output

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

## Testing PawPal+

Run the automated suite from the project root:

```bash
python -m pytest
```

The suite (`tests/test_pawpal.py`) covers both happy paths and edge cases:

- **Core** — task completion toggles status; adding tasks grows a pet's list;
  `Owner.all_tasks()` flattens tasks across pets.
- **Sorting** — `sort_by_time()` returns tasks chronologically regardless of
  insertion order; `sort_by_priority()` ranks the most urgent task first.
- **Filtering** — `filter_by_pet()` and `filter_by_status()` / `pending()`
  return the right subsets.
- **Conflict detection** — exact same-time tasks and overlapping-duration tasks
  are flagged; separate times are not; warnings come back as strings.
- **Recurrence** — completing a daily task schedules the next day, a weekly task
  the next week, and a one-off task spawns nothing.
- **Edge cases** — empty pet, owner with no pets, and an empty scheduler all
  behave safely without raising.

Successful run:

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
rootdir: .../PawPal+
collected 17 items

tests/test_pawpal.py .................                                   [100%]

============================== 17 passed in 0.01s ==============================
```

**Confidence level: ★★★★☆ (4/5).** All 17 tests pass and cover the core domain
model and every scheduling algorithm, including edge cases. I hold back the
fifth star because conflict detection compares tasks at their stored `due` time
rather than across projected recurrences (see reflection §2b), and the suite
does not yet exercise the Streamlit UI layer end-to-end.

## Project status

- [x] **Phase 1** — System design (UML + class skeletons)
- [x] **Phase 2** — OOP logic, CLI demo, and initial tests
- [x] **Phase 3** — Streamlit UI (`app.py`) wired to the logic layer
- [x] **Phase 4** — Algorithmic layer (sorting, filtering, conflicts, recurrence)
- [x] **Phase 5** — Automated test suite (17 tests)
- [x] **Phase 6** — UI polish, final UML, and reflection

## Design reflections

Design decisions and AI-collaboration notes are tracked in
[`reflection.md`](reflection.md).
