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

> ⚠️ **Honesty note:** I only have one assistant wired into this environment, so
> I have filled in **Tool A** from the solution actually produced here. **Tool B**
> is left as a template — to finish Challenge 5, run the *same* prompt through a
> second assistant (e.g., Gemini, ChatGPT, or Copilot) and paste its result. I
> did not invent another model's output.

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

### Tool B — _(second assistant — to be completed)_

- **Model / tool:** _e.g., Gemini / ChatGPT / Copilot_
- **Output:** _paste here_
- **Useful:** _…_
- **Flawed:** _…_

### Final decision

_Compare the two and record which approach you shipped and why._
