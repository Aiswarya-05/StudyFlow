
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path
from datetime import date

app = Flask(__name__)

# Database file inside the project folder.
DATABASE = Path(__file__).with_name("study_planner.db")


def get_db_connection():
    """Connect to the SQLite database."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection



def initialize_database():
    """Create database tables if they do not exist."""
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hours REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                duration INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (plan_id)
                    REFERENCES study_plans(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                task_date TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def upgrade_daily_tasks_table():
    """Add new task columns without deleting existing tasks."""
    with get_db_connection() as connection:
        cursor = connection.execute(
            "PRAGMA table_info(daily_tasks)"
        )

        existing_columns = {
            column["name"] for column in cursor.fetchall()
        }

        new_columns = {
            "priority": "TEXT NOT NULL DEFAULT 'Medium'",
            "deadline": "TEXT",
            "reminder_at": "TEXT"
        }

        for column_name, column_definition in new_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE daily_tasks ADD COLUMN "
                    f"{column_name} {column_definition}"
                )


        # Daily Task Checklist table.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                task_date TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def create_study_plan(hours, topics):
    """Divide study time equally between subjects."""
    total_minutes = round(hours * 60)
    base_minutes = total_minutes // len(topics)
    extra_minutes = total_minutes % len(topics)

    schedule = []
    current_minute = 0

    for index, topic in enumerate(topics):
        duration = base_minutes

        if index < extra_minutes:
            duration += 1

        start = current_minute
        end = start + duration

        schedule.append({
            "subject": topic,
            "duration": duration,
            "start": f"{start // 60:02d}:{start % 60:02d}",
            "end": f"{end // 60:02d}:{end % 60:02d}",
            "completed": 0
        })

        current_minute = end

    return schedule, total_minutes


def save_study_plan(hours, schedule):
    """Save a study plan and its sessions."""
    with get_db_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO study_plans (hours) VALUES (?)",
            (hours,)
        )

        plan_id = cursor.lastrowid

        for session in schedule:
            connection.execute("""
                INSERT INTO study_sessions
                (plan_id, subject, duration, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            """, (
                plan_id,
                session["subject"],
                session["duration"],
                session["start"],
                session["end"]
            ))

        return plan_id


def get_plan(plan_id):
    """Retrieve a saved plan and its sessions."""
    with get_db_connection() as connection:
        plan = connection.execute(
            "SELECT * FROM study_plans WHERE id = ?",
            (plan_id,)
        ).fetchone()

        if plan is None:
            return None, []

        sessions = connection.execute("""
            SELECT * FROM study_sessions
            WHERE plan_id = ?
            ORDER BY id
        """, (plan_id,)).fetchall()

    schedule = [
        {
            "id": session["id"],
            "subject": session["subject"],
            "duration": session["duration"],
            "start": session["start_time"],
            "end": session["end_time"],
            "completed": session["completed"]
        }
        for session in sessions
    ]

    return plan, schedule


def get_recent_plans():
    """Return the latest five saved study plans."""
    with get_db_connection() as connection:
        return connection.execute("""
            SELECT
                p.id,
                p.hours,
                p.created_at,
                COUNT(s.id) AS subject_count,
                COALESCE(SUM(s.completed), 0) AS completed_count
            FROM study_plans p
            LEFT JOIN study_sessions s ON s.plan_id = p.id
            GROUP BY p.id
            ORDER BY p.id DESC
            LIMIT 5
        """).fetchall()


def get_daily_tasks(task_date):
    """Retrieve tasks for the selected date."""
    with get_db_connection() as connection:
        return connection.execute("""
            SELECT *
            FROM daily_tasks
            WHERE task_date = ?
            ORDER BY completed ASC, id DESC
        """, (task_date,)).fetchall()


def valid_task_date(task_date):
    """Check that the date uses YYYY-MM-DD format."""
    try:
        date.fromisoformat(task_date)
        return True
    except (ValueError, TypeError):
        return False


@app.route("/", methods=["GET", "POST"])
def home():
    schedule = None
    error = None
    hours = ""
    subjects = ""
    total_minutes = 0
    plan_id = None

    if request.method == "POST":
        hours = request.form.get("hours", "").strip()
        subjects = request.form.get("subjects", "").strip()

        try:
            study_hours = float(hours)

            if not 0 < study_hours <= 24:
                raise ValueError(
                    "Study hours must be greater than 0 and at most 24."
                )

            cleaned_subjects = subjects.replace(" and ", ",")
            topics = [
                topic.strip()
                for topic in cleaned_subjects.split(",")
                if topic.strip()
            ]

            if not topics:
                raise ValueError("Please enter at least one subject.")

            if len(topics) > 12:
                raise ValueError("Please enter no more than 12 subjects.")

            if len({topic.casefold() for topic in topics}) != len(topics):
                raise ValueError("Please avoid duplicate subjects.")

            schedule, total_minutes = create_study_plan(
                study_hours, topics
            )

            plan_id = save_study_plan(study_hours, schedule)
            _, schedule = get_plan(plan_id)

        except ValueError as exc:
            error = str(exc)
        except Exception:
            app.logger.exception("Could not generate or save the plan.")
            error = "Could not save your plan. Check the terminal for details."
            schedule = None

    task_date = request.args.get("task_date", date.today().isoformat())

    if not valid_task_date(task_date):
        task_date = date.today().isoformat()

    recent_plans = get_recent_plans()
    daily_tasks = get_daily_tasks(task_date)

    return render_template(
        "index.html",
        schedule=schedule,
        error=error,
        hours=hours,
        subjects=subjects,
        total_minutes=total_minutes,
        plan_id=plan_id,
        recent_plans=recent_plans,
        daily_tasks=daily_tasks,
        task_date=task_date,
        today=date.today().isoformat()
    )


@app.route("/plan/<int:plan_id>")
def view_plan(plan_id):
    """Open a previously saved study plan."""
    plan, schedule = get_plan(plan_id)

    if plan is None:
        return "Study plan not found.", 404

    total_minutes = sum(item["duration"] for item in schedule)
    recent_plans = get_recent_plans()

    task_date = request.args.get("task_date", date.today().isoformat())

    if not valid_task_date(task_date):
        task_date = date.today().isoformat()

    daily_tasks = get_daily_tasks(task_date)

    return render_template(
        "index.html",
        schedule=schedule,
        error=None,
        hours=str(plan["hours"]),
        subjects=", ".join(item["subject"] for item in schedule),
        total_minutes=total_minutes,
        plan_id=plan_id,
        recent_plans=recent_plans,
        daily_tasks=daily_tasks,
        task_date=task_date,
        today=date.today().isoformat()
    )


@app.post("/session/<int:session_id>/toggle")
def toggle_session(session_id):
    """Mark a study session complete or incomplete."""
    with get_db_connection() as connection:
        session = connection.execute(
            "SELECT completed FROM study_sessions WHERE id = ?",
            (session_id,)
        ).fetchone()

        if session is None:
            return "Study session not found.", 404

        new_status = 0 if session["completed"] else 1

        connection.execute(
            "UPDATE study_sessions SET completed = ? WHERE id = ?",
            (new_status, session_id)
        )

        plan = connection.execute(
            "SELECT plan_id FROM study_sessions WHERE id = ?",
            (session_id,)
        ).fetchone()

    return redirect(url_for("view_plan", plan_id=plan["plan_id"]))



@app.post("/daily-task/add")
def add_daily_task():
    """Add a task with priority, deadline, and reminder."""

    task = request.form.get("task", "").strip()
    task_date = request.form.get(
        "task_date", date.today().isoformat()
    )

    priority = request.form.get("priority", "Medium")
    deadline = request.form.get("deadline", "").strip() or None
    reminder_at = (
        request.form.get("reminder_at", "").strip() or None
    )

    # Validate the selected task date.
    if not valid_task_date(task_date):
        task_date = date.today().isoformat()

    # Accept only these priority values.
    if priority not in {"High", "Medium", "Low"}:
        priority = "Medium"

    # Validate the optional deadline.
    if deadline:
        try:
            date.fromisoformat(deadline)
        except ValueError:
            deadline = None

    # Validate the optional reminder date and time.
    if reminder_at:
        try:
            from datetime import datetime
            datetime.strptime(reminder_at, "%Y-%m-%dT%H:%M")
        except ValueError:
            reminder_at = None

    if task:
        task = task[:200]

        with get_db_connection() as connection:
            connection.execute("""
                INSERT INTO daily_tasks
                    (task, task_date, priority, deadline, reminder_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                task,
                task_date,
                priority,
                deadline,
                reminder_at
            ))

    return redirect(url_for("home", task_date=task_date))



@app.post("/daily-task/<int:task_id>/toggle")
def toggle_daily_task(task_id):
    """Mark a daily task complete or incomplete."""
    with get_db_connection() as connection:
        task = connection.execute(
            "SELECT completed, task_date FROM daily_tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if task is None:
            return "Daily task not found.", 404

        new_status = 0 if task["completed"] else 1

        connection.execute(
            "UPDATE daily_tasks SET completed = ? WHERE id = ?",
            (new_status, task_id)
        )

        task_date = task["task_date"]

    return redirect(url_for("home", task_date=task_date))



@app.post("/daily-task/<int:task_id>/delete")
def delete_daily_task(task_id):
    """Delete a daily task."""
    with get_db_connection() as connection:
        task = connection.execute(
            "SELECT task_date FROM daily_tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if task is None:
            return "Daily task not found.", 404

        task_date = task["task_date"]

        connection.execute(
            "DELETE FROM daily_tasks WHERE id = ?",
            (task_id,)
        )

    return redirect(url_for("home", task_date=task_date))


@app.route("/edit-task/<int:task_id>", methods=["GET", "POST"])
def edit_daily_task(task_id):
    """Edit an existing daily task."""

    with get_db_connection() as connection:
        task = connection.execute(
            "SELECT * FROM daily_tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

    if task is None:
        return "Task not found.", 404

    if request.method == "POST":
        task_name = request.form.get("task", "").strip()
        priority = request.form.get("priority", "Medium")
        deadline = request.form.get("deadline", "").strip() or None
        reminder_at = (
            request.form.get("reminder_at", "").strip() or None
        )

        error = None

        if not task_name:
            error = "Task name cannot be empty."
        elif priority not in {"High", "Medium", "Low"}:
            error = "Please select a valid priority."

        if deadline:
            try:
                date.fromisoformat(deadline)
            except ValueError:
                error = "Please select a valid deadline."

        if reminder_at:
            from datetime import datetime
            try:
                datetime.strptime(reminder_at, "%Y-%m-%dT%H:%M")
            except ValueError:
                error = "Please select a valid reminder date and time."

        if error:
            return render_template(
                "edit_task.html",
                task=task,
                error=error
            )

        with get_db_connection() as connection:
            connection.execute("""
                UPDATE daily_tasks
                SET task = ?,
                    priority = ?,
                    deadline = ?,
                    reminder_at = ?
                WHERE id = ?
            """, (
                task_name[:200],
                priority,
                deadline,
                reminder_at,
                task_id
            ))

        return redirect(url_for(
            "home",
            task_date=task["task_date"]
        ))

    return render_template(
        "edit_task.html",
        task=task,
        error=None
    )

    """Delete a daily task."""
    with get_db_connection() as connection:
        task = connection.execute(
            "SELECT task_date FROM daily_tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if task is None:
            return "Daily task not found.", 404

        task_date = task["task_date"]

        connection.execute(
            "DELETE FROM daily_tasks WHERE id = ?",
            (task_id,)
        )

    return redirect(url_for("home", task_date=task_date))


# Create all tables when the app starts.
initialize_database()
upgrade_daily_tasks_table()


if __name__ == "__main__":
    app.run(debug=True)
