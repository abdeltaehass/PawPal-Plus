"""PawPal+ — Streamlit UI.

This is the presentation layer. It owns no business logic of its own: every
button and form delegates to the classes in ``pawpal_system``. The single
``Owner`` instance is kept in ``st.session_state`` so that pets and tasks added
in the browser survive Streamlit's top-to-bottom reruns.

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
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")


def get_owner() -> Owner:
    """Return the persisted Owner, creating an empty one on the first run."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name="You")
    return st.session_state.owner


owner = get_owner()

st.title("🐾 PawPal+")
st.caption("Smart pet care — feedings, walks, meds, and appointments, prioritized.")


# ---------------------------------------------------------------------------
# Sidebar — add a pet
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


# ---------------------------------------------------------------------------
# Main — schedule a task / today's schedule
# ---------------------------------------------------------------------------
schedule_col, today_col = st.columns(2)

with schedule_col:
    st.header("Schedule a Task")
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
    st.header("Today's Schedule")
    scheduler = Scheduler.from_owner(owner)
    todays = scheduler.today()
    if todays:
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
        st.write("Nothing scheduled for today yet.")

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.subheader("⚠️ Conflicts")
        for conflict in conflicts:
            when = conflict.first.due.strftime("%I:%M %p").lstrip("0")
            st.error(f"{conflict} at {when}")


# ---------------------------------------------------------------------------
# Pets overview
# ---------------------------------------------------------------------------
st.divider()
st.header("Your Pets")
if not owner.pets:
    st.write("No pets yet.")
else:
    for pet in owner.pets:
        with st.expander(
            f"{pet.name} — {pet.species}"
            + (f", {pet.breed}" if pet.breed else "")
            + f"  ·  {len(pet.get_tasks())} task(s)"
        ):
            tasks = pet.get_tasks()
            if tasks:
                for task in tasks:
                    st.write(str(task))
            else:
                st.write("No tasks scheduled.")
            if pet.notes:
                st.caption(f"Notes: {pet.notes}")
