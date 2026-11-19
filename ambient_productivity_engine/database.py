
import sqlite3
import os
from pathlib import Path


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "productivity.db"


def get_connection():
    """Connect to the existing SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_db():
    """
    Create missing tables without deleting existing tables or records.
    """

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT DEFAULT 'Medium',
                deadline TEXT DEFAULT '',
                estimated_minutes INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Pending'
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_name TEXT NOT NULL,
                duration INTEGER DEFAULT 0,
                date TEXT DEFAULT '',
                description TEXT DEFAULT ''
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                deadline TEXT DEFAULT '',
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'In Progress'
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT DEFAULT '',
                reflection TEXT NOT NULL
            )
        """)


# --------------------------------------------------
# TASK FUNCTIONS
# --------------------------------------------------

def get_tasks():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM tasks ORDER BY id DESC"
        ).fetchall()


def add_task(
    title,
    description="",
    priority="Medium",
    deadline="",
    estimated_minutes=0,
):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO tasks (
                title, description, priority,
                deadline, estimated_minutes, status
            )
            VALUES (?, ?, ?, ?, ?, 'Pending')
        """, (
            title,
            description,
            priority,
            deadline,
            estimated_minutes,
        ))

        return cursor.lastrowid


def update_task_status(task_id, status):
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )


def update_task(task_id, **kwargs):
    allowed_fields = {
        "title",
        "description",
        "priority",
        "deadline",
        "estimated_minutes",
        "status",
    }

    fields = {
        key: value
        for key, value in kwargs.items()
        if key in allowed_fields
    }

    if not fields:
        return

    assignments = ", ".join(
        f"{field} = ?" for field in fields
    )

    values = list(fields.values()) + [task_id]

    with get_connection() as conn:
        conn.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?",
            values,
        )


# --------------------------------------------------
# ACTIVITY FUNCTIONS
# --------------------------------------------------

def get_activities():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM activities ORDER BY id DESC"
        ).fetchall()


def add_activity(
    activity_name,
    duration,
    activity_date="",
    description="",
):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO activities (
                activity_name, duration, date, description
            )
            VALUES (?, ?, ?, ?)
        """, (
            activity_name,
            duration,
            activity_date,
            description,
        ))

        return cursor.lastrowid


# --------------------------------------------------
# GOAL FUNCTIONS
# --------------------------------------------------

def get_goals():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM goals ORDER BY id DESC"
        ).fetchall()


def add_goal(
    title,
    description="",
    deadline="",
):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO goals (
                title, description, deadline, progress, status
            )
            VALUES (?, ?, ?, 0, 'In Progress')
        """, (
            title,
            description,
            deadline,
        ))

        return cursor.lastrowid


def update_goal(goal_id, progress, status=None):
    progress = max(0, min(100, int(progress)))

    if status is None:
        status = (
            "Completed"
            if progress == 100
            else "In Progress"
        )

    with get_connection() as conn:
        conn.execute("""
            UPDATE goals
            SET progress = ?, status = ?
            WHERE id = ?
        """, (
            progress,
            status,
            goal_id,
        ))


# --------------------------------------------------
# REFLECTION FUNCTIONS
# --------------------------------------------------

def add_reflection(
    date,
    mood="",
    energy_level=3,
    accomplishments="",
    challenges="",
    learnings="",
    tomorrow_focus=""
):
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect("data/productivity.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reflections (
            date,
            mood,
            energy_level,
            accomplishments,
            challenges,
            learnings,
            tomorrow_focus
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            date,
            mood,
            energy_level,
            accomplishments,
            challenges,
            learnings,
            tomorrow_focus
        )
    )

    conn.commit()
    conn.close()


def get_reflections():
    conn = sqlite3.connect("data/productivity.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, date, mood, energy_level,
               accomplishments, challenges,
               learnings, tomorrow_focus, created_at
        FROM reflections
        ORDER BY date DESC, id DESC
        """
    )

    reflections = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return reflections


# --------------------------------------------------
# INITIALIZE DATABASE
# --------------------------------------------------

init_db()