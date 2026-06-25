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

## Phase 2 — _(pending)_

## Phase 3 — _(pending)_

## Phase 4 — _(pending)_

## Phase 5 — _(pending)_

## Phase 6 — _(pending)_
