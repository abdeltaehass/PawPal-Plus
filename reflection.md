# PawPal+ — Design & Reflection Log

This document tracks design intent and reflections on AI–human collaboration
across the project's phases.

---

## System Design

**Three core actions a PawPal+ user should be able to perform:**

1. **Register a pet.** The owner adds a pet to their account, capturing its
   name, species, breed, age, and any care notes.
2. **Schedule a care task.** The owner attaches a task — a feeding, walk,
   medication, or appointment — to a specific pet, with a due time, a priority,
   and an optional recurrence (daily / weekly / monthly).
3. **See today's agenda.** The owner views a single prioritized, conflict-aware
   list of everything due today across all of their pets.

---

## Phase 1 — System Design

### 1a. Initial design

I chose **four core classes plus three enums**:

| Class / Enum | Type | Responsibility |
| ------------ | ---- | -------------- |
| `Owner` | dataclass | The user. Owns a list of `Pet`s; can add/remove/look up pets and flatten every task across all pets. |
| `Pet` | dataclass | An animal. Holds its identity (species, breed, age, notes) and its own list of `Task`s. |
| `Task` | dataclass | One unit of care. Holds title, type, due time, duration, priority, recurrence, and completion state. Carries small helpers (`is_due_on`, `overlaps_with`, `next_occurrence`). |
| `Scheduler` | plain class | The algorithmic engine. Sorts tasks, surfaces today's/upcoming agendas, detects conflicts, and expands recurring tasks. |
| `TaskType`, `Priority`, `Recurrence` | enums | Constrain tasks to valid categories/urgencies/cadences instead of magic strings. |

**Responsibility split / reasoning:**

- I kept **data** (Owner, Pet, Task) separate from **behaviour** (Scheduler).
  Pets and Owners are essentially structured records, so `@dataclass` removes
  constructor/`__repr__` boilerplate. The `Scheduler`, by contrast, is mostly
  algorithms operating over a collection, so it is a plain class.
- I used **enums** for task type, priority, and recurrence so invalid states
  are unrepresentable and priority sorting becomes a simple integer comparison.
- `Task` carries a few *self-describing* helpers (does this task occur on a
  given day? does it overlap another task?) while *cross-task* logic (sorting,
  conflict detection across the whole list) lives in the `Scheduler`. This keeps
  each class's responsibilities focused.

**Relationships:** `Owner` 1→* `Pet` 1→* `Task`; the `Scheduler` aggregates
`Task`s (it references them, it does not own the pets). See
[`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd).

### 1b. Design changes

_(Record here any changes made after asking the AI assistant to review the
skeleton — what changed and why. Examples to consider:)_

- **Auto-assigned `task_id`.** Added a module-level counter so every `Task`
  gets a stable unique id without the caller supplying one — needed so
  `Pet.remove_task` / conflict reports can reference tasks unambiguously.
- **`pet_name` back-reference on `Task`.** Added so the `Scheduler` (which only
  sees a flat list of tasks) can still report *which* pet a task belongs to,
  without forcing a full bidirectional object reference.
- **`Conflict` dataclass.** Introduced a small value type instead of returning
  bare tuples from `detect_conflicts`, so conflict results are self-documenting.

> _Update this section as the AI review surfaces missing relationships or logic
> bottlenecks._

---

## Phase 2 — Implementation (CLI-first)

I implemented all four classes and verified them from the terminal before any UI.

**Key decisions while fleshing out the logic:**

- **Scheduler ↔ Owner boundary.** Rather than give the `Scheduler` knowledge of
  pets, I added `Owner.all_tasks()` (which flattens every pet's task list) and a
  `Scheduler.from_owner(owner)` constructor. The scheduler only ever sees a flat
  list of `Task`s, which keeps it decoupled from the ownership hierarchy.
- **Readable output.** A raw list of dataclass `repr`s was unreadable, so I gave
  `Task` a `__str__` that renders a one-line summary (status • time • title •
  pet • recurrence). The demo prints those directly.
- **Conflict detection** compares each pair of *active* (non-completed) tasks via
  `Task.overlaps_with`, a simple `[due, end)` interval overlap. This is correct
  for concrete same-day tasks; recurring tasks are compared at their base
  occurrence (full per-day expansion is available via `expand_recurring`).
- **Recurrence** is modeled by `next_occurrence()` returning a fresh dated `Task`,
  so `expand_recurring(until)` can walk the chain to materialize a date range.

**Verification:** `python main.py` prints today's schedule, a priority view, the
detected breakfast conflict, and a completed task. `python -m pytest` runs three
checks (completion toggles status, adding a task grows a pet's list, overlapping
tasks are flagged) — all passing.



## Phase 3 — Wiring the Streamlit UI to the logic

The UI (`app.py`) is a thin layer; all behaviour lives in `pawpal_system`.

- **Imports.** `app.py` imports `Owner`, `Pet`, `Task`, the three enums, and
  `Scheduler` from `pawpal_system` — no domain logic is duplicated in the UI.
- **Persistence via `st.session_state`.** Streamlit reruns the whole script on
  every interaction, so a fresh `Owner()` at the top would wipe the data each
  click. I guard it with `if "owner" not in st.session_state`, so a single
  `Owner` lives across reruns and accumulates pets/tasks.
- **Wiring actions to methods.** The "Add a Pet" form calls `owner.add_pet(...)`;
  the "Schedule a Task" form calls `pet.add_task(...)`; "Today's Schedule" is
  rendered from `Scheduler.from_owner(owner).today()` and conflicts from
  `detect_conflicts()`. Completion checkboxes call `task.mark_complete()`.

**Verification:** Streamlit's `AppTest` harness runs `app.py` headlessly with
zero exceptions; simulating the "Add pet" form creates a real `Pet` in
`st.session_state` that survives the rerun — confirming the bridge works.



## Phase 4 — Algorithmic Layer

### 2a. What I added

- **Sorting:** `sort_by_time()` / `sort_by_priority()`.
- **Filtering:** `filter_by_pet()`, `filter_by_status()`, `pending()`.
- **Conflict handling:** `detect_conflicts()` plus `conflict_warnings()`, which
  returns readable strings rather than raising.
- **Recurring tasks:** `complete_task()` marks a task done and, if it recurs,
  auto-creates the next occurrence with `timedelta` (`Task.next_occurrence()`).

One deliberate choice: I sort on `datetime` objects, not `"HH:MM"` strings. The
AI suggestion to parse/compare time strings would work, but native `datetime`
sorting is both clearer and correct across day boundaries, so I kept mine.

### 2b. Tradeoffs

**Conflict detection compares each task at its single stored `due` time, not
across projected recurrences.** I chose *duration-aware* overlap
(`Task.overlaps_with`, comparing `[due, due+duration)` windows) over naive
exact-time matching — that is more accurate for back-to-back tasks. The tradeoff
is that two *recurring* tasks are only flagged when their stored `due` dates land
on the same day; two daily tasks that collide every morning but whose base dates
differ would slip past `detect_conflicts()`. I accepted this because the per-day
views (`tasks_for_day`, `expand_recurring`) already surface those collisions on
demand, and projecting every recurrence pair would add cost and complexity out of
proportion to a household-scale app.

A secondary tradeoff: conflict detection is `O(n²)` pairwise
(`itertools.combinations`). For a handful of pets and tasks this is trivially
fast and far more readable than a sort-and-sweep; I'd revisit it only if a single
owner ever had hundreds of tasks.



## Phase 5 — Testing & Verification

I grew the suite to **17 tests** in `tests/test_pawpal.py`, split into happy
paths (sorting, filtering, recurrence, conflicts) and edge cases (empty pet,
owner with no pets, empty scheduler, one-off completion, non-overlapping times).

The brief's three required checks are covered explicitly:

- **Sorting correctness** — `test_sort_by_time_orders_chronologically` adds
  tasks out of order and asserts the hours come back `[7, 8, 14, 19]`.
- **Recurrence** — `test_completing_daily_task_schedules_next_day` confirms
  completing a daily task creates a second task one day later.
- **Conflict detection** — `test_detect_conflicts_finds_exact_duplicate_time`
  plus `test_overlapping_durations_conflict` and a negative
  `test_separate_times_do_not_conflict`.

**Confidence: 4/5.** The logic layer is well covered; the missing star reflects
the recurrence/conflict tradeoff in §2b and the lack of end-to-end UI tests.



## Phase 6 — Polish & AI Strategy

### Bringing the smart logic into the UI

The Streamlit app now mirrors the algorithmic layer instead of just storing data:
a metrics row (pets / tasks today / conflicts), a consolidated conflict callout,
a sortable + filterable all-tasks table, and per-pet task tables. Every view
calls the `Scheduler` (`today`, `sort_by_time`, `filter_by_pet`,
`conflict_warnings`, `detect_conflicts`) rather than re-implementing logic.

**Conflict presentation choice.** I surface conflicts as a single `st.warning`
that lists each clash with its time and the pets involved, rather than one red
`st.error` per pair. A warning (not an error) signals "review this" without
implying the app broke, and grouping keeps a busy schedule from drowning in
alerts — the most helpful framing for a pet owner.

### Reflecting on AI strategy

- **Most effective features.** Agent/multi-file editing was the biggest win for
  the scheduler: a single change to "complete a recurring task" touched
  `pawpal_system.py`, `app.py`, and the tests together, keeping them consistent.
  Inline generation of the `pytest` suite (happy paths + edge cases) and quick
  docstring passes were also high-leverage.
- **A suggestion I rejected/modified.** The assistant proposed sorting times by
  comparing `"HH:MM"` strings. I rejected it in favor of sorting on `datetime`
  objects — it is clearer and stays correct across day boundaries (a string sort
  would mis-order tasks spanning midnight or different dates). I also turned a
  proposed "exact same start time" conflict check into duration-aware overlap
  (`Task.overlaps_with`) so back-to-back tasks that bleed over are caught.
- **Separate chat sessions per phase.** Keeping design, algorithms, and testing
  in their own sessions stopped context from bleeding together — the testing
  session stayed focused on edge cases instead of re-litigating design, and each
  session's history stayed short and on-topic, which made the suggestions sharper.

### Being the "lead architect"

The AI was fastest at producing *plausible* code, but plausible isn't the same as
*coherent with my design*. My job as the human was to hold the architecture: keep
data classes (`Owner`/`Pet`/`Task`) separate from the behaviour-heavy `Scheduler`,
insist on enums over magic strings, decide where each responsibility lived
(self-describing checks on `Task`, cross-task logic on `Scheduler`), and reject
"clever" suggestions that read worse than the obvious version. The most valuable
thing I did was say *no* to accidental complexity and keep the system small,
testable, and explainable — the AI accelerated the typing, but the design
decisions and the verification (CLI demo + 17 tests) were mine to own.

