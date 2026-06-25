# PawPal+ — AI Interactions Log

A record of how I used an AI coding assistant on the optional extensions, kept
separate from `reflection.md` so the design narrative and the working log stay
distinct.

---

## Agent Workflow — Challenge 1 (Next Available Slot)

**Goal:** add a third algorithmic capability beyond the base requirements — a
"next available slot" finder that suggests the earliest free time for a new task.

**What I asked the agent to do**

> "Add a `next_available_slot(day, duration_minutes)` method to `Scheduler` that
> returns the earliest start time on `day` where a task of the given length fits
> without overlapping existing tasks, bounded by working hours. Add a demo to
> `main.py` and tests."

**Files modified**

| File | Change |
| ---- | ------ |
| `pawpal_system.py` | New `Scheduler.next_available_slot()` (greedy interval sweep); plus serialization helpers and `save_to_json`/`load_from_json` for Challenge 2. |
| `main.py` | New "Next Available Slot" section; emoji + `tabulate` table rendering (Challenge 4); priority view (Challenge 3); persistence round-trip (Challenge 2). |
| `app.py` | Persistence wired in (`load_from_json` on start, `save_to_json` on each run, reset button). |
| `tests/test_pawpal.py` | Added tests for the slot finder (gap found / day full) and JSON round-trip. |
| `requirements.txt`, `.gitignore` | Added `tabulate`; ignored `data.json`. |

**What the agent completed**

- A correct greedy sweep: sort the day's active tasks by time, advance a cursor
  to the end of the latest commitment, and return the first gap large enough.
- Returns `None` (not an exception) when the working window is full.
- Demo + 4 new passing tests (21 total).

**Manual corrections I made**

1. **Emoji alignment.** The first icon set used `🍽️`/`✂️`, which carry Unicode
   variation selectors and threw off `tabulate`'s column widths by one space. I
   swapped them for plain double-width emojis (`🥣`/`🛁`) so the grid lines up.
2. **Recurring-task projection.** The slot finder must compare against tasks as
   they fall *on the requested day*, so I project each task's time onto `day`
   (`datetime.combine(day, task.due.time())`) rather than trusting its stored
   base date — otherwise a daily task created last week wouldn't block today.
3. **Persistence boundary.** I had it ignore `data.json` in git (runtime data,
   not source) and made `load_from_json` return a fresh `Owner` when the file is
   absent instead of raising.

---

## Prompt Comparison — Challenge 5 (Weekly Rescheduling Logic)

> **Note:** Tool A is the solution produced by the assistant used to build
> PawPal+. Tool B is a real ChatGPT run of the same prompt, pasted in below.

**Task / prompt used**

> "Given a weekly recurring `Task` with a `due` datetime, write the logic to
> produce its next occurrence. Handle month/year boundaries correctly."

### Tool A — assistant used to build PawPal+

- **Output:** advance the due time with `datetime + timedelta(weeks=1)` inside
  `Task.next_occurrence()`, dispatching by a `Recurrence` enum; daily uses
  `timedelta(days=1)`, monthly uses a `calendar.monthrange` day-clamp helper.
- **Useful:** `timedelta(weeks=1)` is exact and rolls across month/year
  boundaries for free; using the enum keeps the branch readable.
- **Flawed / limited:** weekly rescheduling is computed from the task's stored
  `due` (its base occurrence), not from "today", so a long-skipped task advances
  one week from its original date rather than to the next *future* week.
- **Decision:** kept it — simple and correct for the common case; a "catch up to
  the next future occurrence" variant can be layered on later if needed.

### Tool B — ChatGPT

- **Model / tool:** ChatGPT
- **Output:**

```python
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from calendar import monthrange


class Recurrence(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass(frozen=True)
class Task:
    due: datetime
    recurrence: Recurrence = Recurrence.NONE

    def next_occurrence(self) -> "Task | None":
        if self.recurrence is Recurrence.NONE:
            return None
        if self.recurrence is Recurrence.DAILY:
            next_due = self.due + timedelta(days=1)
        elif self.recurrence is Recurrence.WEEKLY:
            next_due = self.due + timedelta(weeks=1)
        elif self.recurrence is Recurrence.MONTHLY:
            year = self.due.year
            month = self.due.month + 1
            if month > 12:
                month = 1
                year += 1
            day = min(self.due.day, monthrange(year, month)[1])
            next_due = self.due.replace(year=year, month=month, day=day)
        else:
            raise ValueError(f"Unsupported recurrence: {self.recurrence}")
        return replace(self, due=next_due)
```

- **Useful:**
  - Same core idea as mine, and it independently validated two of my design
    choices: `timedelta(weeks=1)` for weekly (Dec 29 → Jan 5 with no special
    casing) and `calendar.monthrange()` to clamp the day for monthly
    (Jan 31 → Feb 28). The worked examples made the boundary behavior easy to
    confirm.
  - `dataclasses.replace()` is a tidy one-liner for "copy with one field changed,"
    and the defensive `else: raise ValueError` is a nice touch.
- **Flawed (for *this* system):**
  - **`frozen=True` is incompatible with PawPal+.** My `Task` is mutable on
    purpose — `mark_complete()` sets `self.completed` and `Pet.add_task()` stamps
    `self.pet_name`. A frozen dataclass raises `FrozenInstanceError` on both.
  - **It doesn't reset `completed`.** `replace()` copies every field, so if the
    current task was already done, the next occurrence comes back
    `completed=True`. A freshly scheduled occurrence should start *not* done — my
    version sets `completed=False` explicitly. That's a real correctness bug for a
    scheduler.
  - `replace()` also interacts awkwardly with my auto-assigned `task_id`
    (`init=False`), which is why I construct a new `Task` explicitly.

### Final decision

I shipped **Tool A (the build assistant's version)**. The two agree on the hard
part — month/year boundaries — so it came down to fit and correctness, not the
weekly math (which is identical). Tool A builds a fresh `Task` with
`completed=False` and works with my mutable, auto-`task_id` design, whereas
ChatGPT's `frozen=True` + `replace()` would break `mark_complete()` and silently
carry the "done" flag into the next occurrence. ChatGPT's answer was still
valuable: it independently confirmed the `monthrange` day-clamp, which raised my
confidence in the monthly logic.
