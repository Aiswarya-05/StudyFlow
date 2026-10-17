
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta
from winotify import Notification

# Use the database located beside this Python file.
DATABASE = Path(__file__).with_name("study_planner.db")

# Remember reminders already notified during this run.
notified_reminders = set()


def check_reminders():
    """Find due reminders and display Windows notifications."""
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%dT%H:%M")
    earliest_time = (now - timedelta(minutes=5)).strftime(
        "%Y-%m-%dT%H:%M"
    )

    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row

        tasks = connection.execute("""
            SELECT id, task, reminder_at
            FROM daily_tasks
            WHERE reminder_at IS NOT NULL
              AND reminder_at != ''
              AND completed = 0
              AND reminder_at <= ?
              AND reminder_at >= ?
        """, (current_time, earliest_time)).fetchall()

    for task in tasks:
        reminder_key = (task["id"], task["reminder_at"])

        if reminder_key in notified_reminders:
            continue

        notification = Notification(
            app_id="StudyFlow",
            title="Study Reminder",
            msg=f"Time to study: {task['task']}",
            duration="long"
        )

        notification.show()
        notified_reminders.add(reminder_key)

        print(f"Notification sent for: {task['task']}")


if __name__ == "__main__":
    print("StudyFlow reminder checker is running.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            check_reminders()
            time.sleep(15)
    except KeyboardInterrupt:
        print("\nReminder checker stopped.")
