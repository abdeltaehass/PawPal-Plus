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
| **UI layer**     | _Streamlit app_     | Thin presentation layer over the logic (later)  |

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

## Project status

- [x] **Phase 1** — System design (UML + class skeletons)
- [ ] Phase 2 — Implement OOP logic
- [ ] Phase 3 — Scheduling algorithms (sort, conflicts, recurrence)
- [ ] Phase 4 — CLI demo + pytest suite
- [ ] Phase 5 — Streamlit UI
- [ ] Phase 6 — Polish, final UML, reflection

## Design reflections

Design decisions and AI-collaboration notes are tracked in
[`reflection.md`](reflection.md).
