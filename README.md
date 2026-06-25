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
- 🕳️ **Next available slot** — suggests the earliest free time that fits a new
  task within working hours.
- 💾 **Persistence** — pets and tasks are saved to `data.json` and reloaded
  between runs.
- 🖥️ **Two front ends** — a Streamlit web UI (`app.py`) and a CLI demo
  (`main.py`), both over the same logic layer, with a 21-test `pytest` suite.

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

Today — sorted by time
----------------------
╭────┬─────────┬──────────────┬──────────┬────────────┬──────────┬────────╮
│    │ Time    │ Task         │ Pet      │ Priority   │ Repeat   │ Done   │
├────┼─────────┼──────────────┼──────────┼────────────┼──────────┼────────┤
│ 🐕  │ 7:30 AM │ Morning walk │ Rex      │ Medium     │ daily    │        │
│ 🥣  │ 8:00 AM │ Breakfast    │ Rex      │ High       │ daily    │        │
│ 🥣  │ 8:00 AM │ Breakfast    │ Whiskers │ High       │ daily    │        │
│ 🏥  │ 2:00 PM │ Vet checkup  │ Rex      │ Critical   │ —        │        │
│ 💊  │ 7:00 PM │ Evening meds │ Rex      │ High       │ daily    │        │
╰────┴─────────┴──────────────┴──────────┴────────────┴──────────┴────────╯

Today — by priority, then time
------------------------------
╭────┬─────────┬──────────────┬──────────┬────────────┬──────────┬────────╮
│    │ Time    │ Task         │ Pet      │ Priority   │ Repeat   │ Done   │
├────┼─────────┼──────────────┼──────────┼────────────┼──────────┼────────┤
│ 🏥  │ 2:00 PM │ Vet checkup  │ Rex      │ Critical   │ —        │        │
│ 🥣  │ 8:00 AM │ Breakfast    │ Rex      │ High       │ daily    │        │
│ 🥣  │ 8:00 AM │ Breakfast    │ Whiskers │ High       │ daily    │        │
│ 💊  │ 7:00 PM │ Evening meds │ Rex      │ High       │ daily    │        │
│ 🐕  │ 7:30 AM │ Morning walk │ Rex      │ Medium     │ daily    │        │
╰────┴─────────┴──────────────┴──────────┴────────────┴──────────┴────────╯

Conflict Warnings
-----------------
⚠ 8:00 AM: 'Breakfast' overlaps 'Breakfast' (Rex & Whiskers)

Next Available Slot
-------------------
Earliest free 45-min slot today: 8:15 AM

Recurring — complete a daily task
---------------------------------
Completed: Morning walk  (Thu 07:30 AM)
Auto-scheduled: Morning walk  (Fri 07:30 AM)

Persistence
-----------
Saved 5 tasks to <tmpdir>/pawpal_demo.json
Reloaded 5 tasks for 2 pets: ['Rex', 'Whiskers']
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
| **Next available slot** | `Scheduler.next_available_slot(day, minutes)` | Greedy sweep that returns the earliest free start time within working hours, or `None` if the day is full. |

## Optional Extensions

Extra features built on top of the base requirements:

- **Next available slot (Challenge 1).** `Scheduler.next_available_slot(day,
  duration_minutes, start_hour=8, end_hour=20)` sorts the day's tasks, sweeps a
  cursor to the end of each commitment, and returns the first gap that fits.
  See the **Agent Workflow** log in [`ai_interactions.md`](ai_interactions.md).
- **Data persistence (Challenge 2).** Pets and tasks survive between runs via
  `save_to_json(owner)` / `load_from_json()` in `pawpal_system.py`. Each model
  (`Task`/`Pet`/`Owner`) has `to_dict()` / `from_dict()` that convert custom
  objects to/from plain dicts — enums map to their names/values and `datetime`
  uses ISO strings — so no external serialization library is needed. **Workflow:**
  the Streamlit app loads `data.json` on startup and rewrites it after every
  interaction; the sidebar's *Reset all data* button clears it. *Files modified:*
  `pawpal_system.py` (serialization + save/load), `app.py` (load/save wiring),
  `.gitignore` (ignore the runtime `data.json`).
- **Priority-first scheduling (Challenge 3).** `Task` carries a `Priority`
  (Low/Medium/High/Critical); `Scheduler.sort_by_priority()` orders by priority
  first, then time. See the *"Today — by priority"* table in the CLI output above.
- **Formatted output (Challenge 4).** The CLI uses per-type **emojis**
  (🐕 🥣 💊 🏥 🛁 📌) and renders schedules as boxed tables with the
  [`tabulate`](https://pypi.org/project/tabulate/) library (`render()` in
  `main.py`, `tablefmt="rounded_outline"`); the Streamlit UI mirrors this with
  `st.metric`, `st.dataframe`, and a consolidated `st.warning`.

AI-collaboration notes for these extensions live in
[`ai_interactions.md`](ai_interactions.md).

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
- **Extensions** — `next_available_slot()` finds the first gap and returns
  `None` on a full day; JSON save/load round-trips owner, pets, and task fields.

Successful run:

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
rootdir: .../PawPal+
collected 21 items

tests/test_pawpal.py .....................                               [100%]

============================== 21 passed in 0.03s ==============================
```

**Confidence level: ★★★★☆ (4/5).** All 21 tests pass and cover the core domain
model and every scheduling algorithm, including edge cases. I hold back the
fifth star because conflict detection compares tasks at their stored `due` time
rather than across projected recurrences (see reflection §2b), and the suite
does not yet exercise the Streamlit UI layer end-to-end.

## Project status

- [x] **Phase 1** — System design (UML + class skeletons)
- [x] **Phase 2** — OOP logic, CLI demo, and initial tests
- [x] **Phase 3** — Streamlit UI (`app.py`) wired to the logic layer
- [x] **Phase 4** — Algorithmic layer (sorting, filtering, conflicts, recurrence)
- [x] **Phase 5** — Automated test suite (21 tests)
- [x] **Phase 6** — UI polish, final UML, and reflection
- [x] **Extensions** — next-available-slot, JSON persistence, priority
  scheduling, and formatted (emoji/table) output

## Design reflections

Design decisions and AI-collaboration notes are tracked in
[`reflection.md`](reflection.md).
