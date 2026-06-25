"""PawPal+ — Streamlit UI.

This is the presentation layer. It owns no business logic of its own: every
button, filter, and view delegates to the classes in ``pawpal_system``. The
single ``Owner`` instance is kept in ``st.session_state`` so that pets and
tasks added in the browser survive Streamlit's top-to-bottom reruns.

Run with: ``streamlit run app.py``.
"""

from datetime import date, datetime, time

import streamlit as st

from pawpal_system import (
    Owner,
    Pet,
    Priority,
    Recurrence,
    Scheduler,
    Task,
    TaskType,
    load_from_json,
    save_to_json,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")


def get_owner() -> Owner:
    """Return the Owner, loading saved data from data.json on the first run."""
    if "owner" not in st.session_state:
        st.session_state.owner = load_from_json()
    return st.session_state.owner


def task_rows(tasks: list[Task]) -> list[dict]:
    """Flatten tasks into display rows for st.dataframe."""
    return [
        {
            "Time": t.due.strftime("%a %I:%M %p"),
            "Task": t.title,
            "Type": t.task_type.value.title(),
            "Pet": t.pet_name or "",
            "Priority": t.priority.name.title(),
            "Repeats": t.recurrence.value.title(),
            "Done": "✓" if t.completed else "",
        }
        for t in tasks
    ]


owner = get_owner()
scheduler = Scheduler.from_owner(owner)

st.title("🐾 PawPal+")
st.caption("Smart pet care — feedings, walks, meds, and appointments, prioritized.")


# ---------------------------------------------------------------------------
# Sidebar — manage pets
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Add a Pet")
    with st.form("add_pet", clear_on_submit=True):
        name = st.text_input("Name")
        species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        breed = st.text_input("Breed")
        age = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
        notes = st.text_area("Notes")
        if st.form_submit_button("Add pet"):
            if name.strip():
                owner.add_pet(
                    Pet(
                        name=name.strip(),
                        species=species,
                        breed=breed.strip(),
                        age=int(age),
                        notes=notes.strip(),
                    )
                )
                st.success(f"Added {name.strip()} 🐾")
            else:
                st.warning("Please enter a name.")

    if owner.pets:
        st.divider()
        remove = st.selectbox("Remove a pet", ["—"] + [p.name for p in owner.pets])
        if st.button("Remove", disabled=(remove == "—")):
            owner.remove_pet(remove)
            st.rerun()

    st.divider()
    st.caption("💾 Pets and tasks are saved to `data.json` automatically.")
    if st.button("🗑️ Reset all data"):
        st.session_state.owner = Owner(name="You")
        save_to_json(st.session_state.owner)
        st.rerun()


# ---------------------------------------------------------------------------
# At-a-glance metrics
# ---------------------------------------------------------------------------
m1, m2, m3 = st.columns(3)
m1.metric("Pets", len(owner.pets))
m2.metric("Tasks today", len(scheduler.today()))
m3.metric("Conflicts", len(scheduler.detect_conflicts()))

# Conflict warnings — consolidated into one owner-friendly callout.
warnings = scheduler.conflict_warnings()
if warnings:
    st.warning(
        "**Heads up — overlapping tasks:**\n\n"
        + "\n\n".join(f"- {w}" for w in warnings)
    )

st.divider()


# ---------------------------------------------------------------------------
# Schedule a task / today's schedule
# ---------------------------------------------------------------------------
schedule_col, today_col = st.columns(2)

with schedule_col:
    st.subheader("➕ Schedule a Task")
    if not owner.pets:
        st.info("Add a pet in the sidebar to start scheduling tasks.")
    else:
        with st.form("add_task", clear_on_submit=True):
            pet_name = st.selectbox("Pet", [p.name for p in owner.pets])
            title = st.text_input("Task", placeholder="Morning walk")
            task_type = st.selectbox("Type", [t.name.title() for t in TaskType])
            date_col, time_col = st.columns(2)
            with date_col:
                due_date = st.date_input("Date", value=date.today())
            with time_col:
                due_time = st.time_input("Time", value=time(8, 0))
            duration = st.number_input(
                "Duration (min)", min_value=5, max_value=480, value=30, step=5
            )
            priority = st.selectbox(
                "Priority", [p.name.title() for p in Priority], index=1
            )
            recurrence = st.selectbox("Repeats", [r.name.title() for r in Recurrence])
            if st.form_submit_button("Schedule task"):
                if title.strip():
                    pet = owner.get_pet(pet_name)
                    pet.add_task(
                        Task(
                            title=title.strip(),
                            task_type=TaskType[task_type.upper()],
                            due=datetime.combine(due_date, due_time),
                            duration_minutes=int(duration),
                            priority=Priority[priority.upper()],
                            recurrence=Recurrence[recurrence.upper()],
                        )
                    )
                    st.success(f"Scheduled “{title.strip()}” for {pet_name}")
                else:
                    st.warning("Please enter a task name.")

with today_col:
    st.subheader("📅 Today")
    todays = scheduler.today()
    if todays:
        st.caption("Tick a task to mark it done. Recurring tasks roll to the next date.")
        for task in todays:
            done = st.checkbox(
                str(task), value=task.completed, key=f"task_{task.task_id}"
            )
            if done and not task.completed:
                task.mark_complete()
                # A recurring task rolls forward: add its next occurrence to the pet.
                if task.recurrence is not Recurrence.NONE:
                    pet = owner.get_pet(task.pet_name)
                    upcoming = task.next_occurrence()
                    if pet is not None and upcoming is not None:
                        pet.add_task(upcoming)
    else:
        st.info("Nothing scheduled for today yet.")


# ---------------------------------------------------------------------------
# All tasks — sorted and filterable
# ---------------------------------------------------------------------------
st.divider()
st.subheader("🗂️ All Tasks")

if not owner.all_tasks():
    st.info("No tasks yet — schedule one above.")
else:
    pet_col, status_col = st.columns(2)
    pet_choice = pet_col.selectbox("Filter by pet", ["All"] + [p.name for p in owner.pets])
    status_choice = status_col.radio(
        "Filter by status", ["All", "Pending", "Completed"], horizontal=True
    )

    # Delegate filtering to the Scheduler, then sort chronologically.
    tasks = scheduler.filter_by_pet(pet_choice) if pet_choice != "All" else list(scheduler.tasks)
    if status_choice == "Pending":
        tasks = [t for t in tasks if not t.completed]
    elif status_choice == "Completed":
        tasks = [t for t in tasks if t.completed]
    tasks = sorted(tasks, key=lambda t: t.due)

    if tasks:
        st.dataframe(task_rows(tasks), use_container_width=True, hide_index=True)
    else:
        st.info("No tasks match those filters.")


# ---------------------------------------------------------------------------
# Pets overview
# ---------------------------------------------------------------------------
st.divider()
st.subheader("🐾 Your Pets")
if not owner.pets:
    st.write("No pets yet.")
else:
    for pet in owner.pets:
        with st.expander(
            f"{pet.name} — {pet.species}"
            + (f", {pet.breed}" if pet.breed else "")
            + f"  ·  {len(pet.get_tasks())} task(s)"
        ):
            tasks = sorted(pet.get_tasks(), key=lambda t: t.due)
            if tasks:
                st.table(task_rows(tasks))
            else:
                st.write("No tasks scheduled.")
            if pet.notes:
                st.caption(f"Notes: {pet.notes}")


# Persist after every interaction so data survives app restarts.
save_to_json(owner)
