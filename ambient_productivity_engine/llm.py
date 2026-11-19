
"""
Ambient Productivity Engine
Safe productivity reporting and optional Ollama chat.
"""

import re

MODEL_NAME = "llama3.2:1b"


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def as_records(records):
    if records is None:
        return []
    if isinstance(records, dict):
        return [records]
    try:
        return list(records)
    except (TypeError, ValueError):
        return []


def get_value(record, *keys, default=""):
    if record is None:
        return default

    for key in keys:
        try:
            if isinstance(record, dict):
                value = record.get(key)
            else:
                try:
                    value = record[key]
                except (KeyError, IndexError, TypeError):
                    value = getattr(record, key, None)

            if value is not None and str(value).strip():
                return value
        except Exception:
            continue

    return default


def safe_number(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return default


def clean_text(value, default="Not recorded"):
    if value is None or not str(value).strip():
        return default
    return str(value).strip()


def format_minutes(minutes):
    total = max(0, int(safe_number(minutes)))
    hours, mins = divmod(total, 60)

    if hours and mins:
        return f"{hours} hours {mins} minutes"
    if hours:
        return f"{hours} hours"
    return f"{mins} minutes"


def get_duration(record):
    return max(
        0,
        safe_number(
            get_value(
                record,
                "duration_minutes",
                "duration",
                "minutes",
                "time_spent",
                default=0,
            )
        ),
    )


def get_title(record):
    return clean_text(
        get_value(
            record,
            "title",
            "task_name",
            "activity_type",
            "activity_name",
            "activity",
            "goal_name",
            "goal",
            "name",
            "task",
        )
    )


# --------------------------------------------------
# MEMORY ANSWER HELPERS
# --------------------------------------------------

def extract_field(context, field, next_fields=()):
    """Extract a labelled field without including the next memory field."""

    if not context:
        return ""

    following_labels = [
        re.escape(item)
        for item in next_fields
    ]

    # Stop at the next known label, even if punctuation or
    # extra spaces appear before it.
    all_labels = [
        "Mood",
        "Energy",
        "Energy level",
        "What went well",
        "Challenges",
        "Learnings",
        "Tomorrow's focus",
        "Tomorrow’s focus",
        "Description",
        "Priority",
        "Deadline",
        "Status",
        "Progress",
        "Task",
        "Activity",
        "Goal",
    ]

    for label in all_labels:
        if label.lower() != field.lower():
            following_labels.append(re.escape(label))

    ending = (
        r"(?=\s*(?:[.;]\s*)?(?:"
        + "|".join(set(following_labels))
        + r")\s*:|$)"
    )

    pattern = (
        re.escape(field)
        + r"\s*:\s*(.*?)"
        + ending
    )

    match = re.search(
        pattern,
        context,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        value = match.group(1).strip().rstrip(".; ")

        if value.lower() not in (
            "",
            "not recorded",
            "none",
            "n/a",
        ):
            return value

    return ""

# answer common questions


def answer_common_question(question, context):
    """Answer common questions using retrieved memories."""

    q = question.lower().strip()
    text = context or ""

    # Helper: extract activities from retrieved context.
    activities = re.findall(
        r"Activity:\s*(.*?)\.\s*Duration:\s*(\d+(?:\.\d+)?)\s*minutes",
        text,
        flags=re.IGNORECASE,
    )

    # 1. Activity durations and total time
    activity_question = any(
        phrase in q
        for phrase in (
            "activity", "activities", "how much time",
            "total time", "time did i spend", "time spent",
            "duration", "focus time",
        )
    )

    if activity_question and activities:
        total = sum(float(duration) for _, duration in activities)
        details = "\n".join(
            f"- {name.strip()}: {duration} minutes"
            for name, duration in activities
        )
        total_minutes = int(total) if total.is_integer() else total

        return (
            f"Your recorded activities:\n{details}\n\n"
            f"Total time: {total_minutes} minutes "
            f"({format_minutes(total_minutes)})."
        )

    # 2. Goal status and completion
    goal_question = any(
        phrase in q
        for phrase in (
            "goal", "goals", "machine learning",
            "goal status", "goal progress",
        )
    )

    if goal_question:
        goal_pattern = re.compile(
            r"Goal:\s*(.*?)"
            r"(?=\s*(?:Description|Deadline|Progress|Status)\s*:|$)"
            r"(.*?)"
            r"(?=Goal:|Activity:|Task:|Daily Reflection:|$)",
            flags=re.IGNORECASE | re.DOTALL,
        )

        goals = list(goal_pattern.finditer(text))

        if goals:
            # Prefer the goal mentioned in the question.
            selected = None
            for goal in goals:
                name = goal.group(1).strip().rstrip(".; ")
                if name and (
                    name.lower() in q
                    or any(word in q for word in name.lower().split())
                ):
                    selected = goal
                    break

            if selected is None and len(goals) == 1:
                selected = goals[0]

            if selected:
                name = selected.group(1).strip().rstrip(".; ")
                record = selected.group(0)

                progress_match = re.search(
                    r"Progress:\s*(\d+(?:\.\d+)?)\s*(?:%|percent)?",
                    record,
                    flags=re.IGNORECASE,
                )
                status_match = re.search(
                    r"Status:\s*([^.;\n]+)",
                    record,
                    flags=re.IGNORECASE,
                )

                progress = (
                    float(progress_match.group(1))
                    if progress_match else None
                )
                status = (
                    status_match.group(1).strip()
                    if status_match else "Not recorded"
                )

                if (
                    (progress is not None and progress >= 100)
                    or status.lower() in ("completed", "complete", "done")
                ):
                    if progress is not None:
                        return (
                            f"Your goal, {name}, is completed. "
                            f"Your saved progress is {progress:g}%."
                        )
                    return f"Your goal, {name}, is completed."

                if progress is not None:
                    return (
                        f"Your saved goal is {name}. "
                        f"Progress: {progress:g}%. Status: {status}."
                    )

                return f"Your saved goal is {name}. Status: {status}."

    # 3. Challenges
    
    
    # 2. Pending and unfinished tasks
    pending_question = any(
        phrase in q
        for phrase in (
            "pending task",
            "pending tasks",
            "unfinished task",
            "unfinished tasks",
            "tasks still pending",
            "which of my tasks",
            "which tasks are pending",
            "incomplete task",
            "incomplete tasks",
        )
    )

    if pending_question:
        # Extract task records individually.
        task_pattern = re.compile(
            r"Task:\s*(.*?)\.\s*"
            r"Description:\s*(.*?)\.\s*"
            r"Priority:\s*(.*?)\.\s*"
            r"Deadline:\s*(.*?)\.\s*"
            r"Status:\s*([^.;\n]+)",
            flags=re.IGNORECASE,
        )

        task_matches = task_pattern.findall(text)

        if not task_matches:
            return (
                "I couldn't verify the task status from the "
                "retrieved records. Please check your Tasks page."
            )

        pending_tasks = [
            (name.strip(), status.strip())
            for name, description, priority, deadline, status
            in task_matches
            if status.strip().lower()
            not in ("completed", "complete", "done")
        ]

        if pending_tasks:
            details = "\n".join(
                f"- {name}: {status}"
                for name, status in pending_tasks
            )
            return "Your unfinished tasks are:\n" + details

        return "You have no pending tasks in your retrieved records."


    # 4. Learnings — avoid treating "Machine Learning goal"
    # as a reflection question.
    learning_question = any(
        phrase in q
        for phrase in (
            "what did i learn", "what have i learned",
            "what did i learn about", "my learnings",
            "learnings from", "what i learned",
        )
    )

    if learning_question:
        learning = extract_field(
            text,
            "Learnings",
            (
                "Tomorrow's focus", "Tomorrow’s focus",
                "Challenges", "Mood", "Energy level", "Energy",
            ),
        )
        if learning:
            return (
                "Based on your saved reflection, "
                f"you learned: {learning}."
            )

    # 5. Tomorrow's focus
    if any(
        phrase in q
        for phrase in ("tomorrow", "focus on next", "next day")
    ):
        focus = extract_field(
            text,
            "Tomorrow's focus",
            ("Mood", "Energy", "Challenges", "Learnings"),
        )
        if not focus:
            focus = extract_field(
                text,
                "Tomorrow’s focus",
                ("Mood", "Energy", "Challenges", "Learnings"),
            )
        if focus:
            return f"Your recorded focus is: {focus}."

    # 6. Productivity recommendations
    recommendation_question = any(
        phrase in q
        for phrase in (
            "recommendation", "recommendations", "recommend",
            "how can i improve my productivity",
            "what should i do next", "what should i work on next",
            "what should i work on", "what next",
            "productivity advice", "suggestions", "suggest",
            "based on my saved records", "based on my records",
        )
    )

    if recommendation_question:
        recommendations = []

        challenge = extract_field(
            text,
            "Challenges",
            (
                "Learnings", "Tomorrow's focus",
                "Tomorrow’s focus", "Mood", "Energy level", "Energy",
            ),
        )

        focus = extract_field(
            text,
            "Tomorrow's focus",
            ("Mood", "Energy", "Challenges", "Learnings"),
        )
        if not focus:
            focus = extract_field(
                text,
                "Tomorrow’s focus",
                ("Mood", "Energy", "Challenges", "Learnings"),
            )

        # Extract each task and its own status.
        task_pattern = re.compile(
            r"Task:\s*(.*?)\.\s*Description:\s*(.*?)\.\s*"
            r"Priority:\s*(.*?)\.\s*Deadline:\s*(.*?)\.\s*"
            r"Status:\s*([^.;\n]+)",
            flags=re.IGNORECASE,
        )

        pending_tasks = [
            (name.strip(), priority.strip(), status.strip())
            for name, _, priority, _, status in task_pattern.findall(text)
            if status.strip().lower() not in ("completed", "complete", "done")
        ]

        if pending_tasks:
            recommendations.append("Prioritize your unfinished tasks:")
            for name, priority, status in pending_tasks:
                recommendations.append(
                    f"Work on {name} (priority: {priority}, status: {status})."
                )

        if focus:
            recommendations.append(
                f"Continue with your recorded focus: {focus}."
            )

        if challenge:
            recommendations.append(
                f"Work on your recorded challenge: {challenge}."
            )

        if activities:
            total = sum(float(duration) for _, duration in activities)
            total_minutes = int(total) if total.is_integer() else total
            recommendations.append(
                f"You recorded {format_minutes(total_minutes)} of activity. "
                "Continue tracking your time and take breaks when needed."
            )

        if recommendations:
            return (
                "Based on your saved records, here are my suggestions:\n\n"
                + "\n".join(f"- {item}" for item in recommendations)
            )

    return None


# --------------------------------------------------
# CONVERT RECORDS TO TEXT
# --------------------------------------------------

def records_to_text(records, record_type="record"):
    records = as_records(records)

    if not records:
        return f"No {record_type} records found."

    lines = []

    for index, record in enumerate(records, start=1):
        if record_type == "task":
            lines.append(
                f"{index}. Task: {get_title(record)}; "
                f"Status: {clean_text(get_value(record, 'status'))}; "
                f"Priority: {clean_text(get_value(record, 'priority'))}; "
                f"Deadline: {clean_text(get_value(record, 'deadline'))}"
            )

        elif record_type == "activity":
            lines.append(
                f"{index}. Activity: {get_title(record)}; "
                f"Duration: {int(get_duration(record))} minutes; "
                f"Date: {clean_text(get_value(record, 'date'))}; "
                f"Description: "
                f"{clean_text(get_value(record, 'description'))}"
            )

        elif record_type == "goal":
            progress = safe_number(
                get_value(
                    record,
                    "progress",
                    "progress_percentage",
                    "progress_percent",
                )
            )

            lines.append(
                f"{index}. Goal: {get_title(record)}; "
                f"Progress: {progress:g}%; "
                f"Status: {clean_text(get_value(record, 'status'))}; "
                f"Deadline: {clean_text(get_value(record, 'deadline'))}"
            )

        elif record_type == "reflection":
            lines.append(
                f"{index}. Date: {clean_text(get_value(record, 'date'))}; "
                f"Mood: {clean_text(get_value(record, 'mood'))}; "
                f"Energy: {clean_text(get_value(record, 'energy_level'))}; "
                f"Accomplishments: "
                f"{clean_text(get_value(record, 'accomplishments'))}; "
                f"Challenges: "
                f"{clean_text(get_value(record, 'challenges'))}; "
                f"Learnings: "
                f"{clean_text(get_value(record, 'learnings'))}; "
                f"Tomorrow's focus: "
                f"{clean_text(get_value(record, 'tomorrow_focus'))}"
            )

        else:
            lines.append(str(record))

    return "\n".join(lines)


# --------------------------------------------------
# OPTIONAL OLLAMA RESPONSE
# --------------------------------------------------

def generate_response(prompt, context=""):
    """Answer questions using retrieved memories and optional Ollama."""

    question = str(prompt or "").strip()
    context_text = str(context or "").strip()

    if not question:
        return "Please enter a question."

    if not context_text:
        return (
            "No saved memories were retrieved. "
            "Please refresh your personal memory and try again."
        )

    direct_answer = answer_common_question(
        question,
        context_text,
    )

    if direct_answer:
        return direct_answer

    try:
        import ollama

        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a personal productivity assistant. "
                        "Answer using only the supplied saved records and the user's question. "
                        "Never invent facts, tasks, dates, durations, achievements, or personal information. "
                        "Recording an activity does not mean the activity or project was completed. "
                        "Only say a task or goal is completed when its saved status explicitly says "
                        "Completed, Complete, or Done. "
                        "Do not assume a goal description proves that its work has been completed. "
                        "If the answer is not available in the supplied records, say so clearly. "
                        "Never recommend a task marked Completed. "
                        "Prioritize pending tasks when they appear in the records. "
                        "Use recorded challenges and tomorrow's focus when relevant. "
                        "Clearly distinguish saved facts from recommendations. "
                        "When summarizing records, mention only facts explicitly supported "
                        "by the retrieved context. Do not combine completed tasks and goals "
                        "with activities to claim everything was completed. "
                        "Do not claim deadlines were met unless the records explicitly confirm "
                        "that. If asked for a specific number of bullet points, provide exactly "
                        "that number. "
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Saved memories:\n{context_text}\n\n"
                        f"Question: {question}"
                    ),
                },
            ],
            options={
                "temperature": 0,
                "num_ctx": 2048,
                "num_predict": 200,
            },
            keep_alive=0,
        )

        answer = response.get("message", {}).get("content", "")
        return answer.strip() or "The AI returned an empty response."

    except ImportError:
        return (
            "The Ollama Python package is missing. Install it with: "
            "venv\\Scripts\\python.exe -m pip install ollama"
        )

    except Exception as error:
        return (
            "The AI model is unavailable. Your saved records are unchanged. "
            f"Details: {error}"
        )


# --------------------------------------------------
# RULE-BASED PRODUCTIVITY REPORT
# --------------------------------------------------

def build_fallback_summary(
    tasks=None,
    activities=None,
    goals=None,
    reflections=None,
    focus_time=0,
    productivity_score=0,
):
    tasks = as_records(tasks)
    activities = as_records(activities)
    goals = as_records(goals)
    reflections = as_records(reflections)

    completed_tasks = [
        task for task in tasks
        if str(get_value(task, "status")).strip().lower()
        in ("completed", "complete", "done")
    ]

    activity_minutes = sum(
        get_duration(activity) for activity in activities
    )

    lines = [
        "## Summary",
        "",
        f"- Tasks completed: {len(completed_tasks)} of {len(tasks)}.",
        f"- Recorded activity time: {format_minutes(activity_minutes)}.",
        f"- Dashboard focus time: {format_minutes(focus_time)}.",
        f"- Saved goals: {len(goals)}.",
        f"- Saved reflections: {len(reflections)}.",
        f"- Productivity score: {safe_number(productivity_score):g}.",
        "",
        "## Strengths",
        "",
    ]

    if completed_tasks:
        for task in completed_tasks:
            lines.append(
                f"- Completed the task **{get_title(task)}**."
            )
    else:
        lines.append("- No completed tasks are recorded yet.")

    for activity in activities:
        lines.append(
            f"- Recorded **{get_title(activity)}** for "
            f"{int(get_duration(activity))} minutes."
        )

    learning_items = []
    accomplishments = []

    for reflection in reflections:
        learning = get_value(reflection, "learnings")
        accomplishment = get_value(reflection, "accomplishments")

        if learning and str(learning).strip():
            learning_items.append(str(learning).strip())

        if accomplishment and str(accomplishment).strip():
            accomplishments.append(str(accomplishment).strip())

    if accomplishments:
        lines.append(
            f"- Reflection accomplishment: "
            f"{accomplishments[-1].rstrip('.')}."
        )

    if learning_items:
        lines.append(
            f"- Learning recorded: {learning_items[-1].rstrip('.')}."
        )

    lines.extend(["", "## Areas for Improvement", ""])

    challenges = []
    tomorrow_focuses = []

    for reflection in reflections:
        challenge = get_value(reflection, "challenges")
        focus = get_value(
            reflection,
            "tomorrow_focus",
            "tomorrow_focuses",
        )

        if challenge and str(challenge).strip():
            challenges.append(str(challenge).strip())

        if focus and str(focus).strip():
            tomorrow_focuses.append(str(focus).strip())

    if challenges:
        for challenge in dict.fromkeys(challenges):
            lines.append(
                f"- Work on the recorded challenge: {challenge}"
            )
    else:
        lines.append("- No specific challenges are recorded.")

    if not activities:
        lines.append("- Record your activities and their duration.")

    lines.extend(["", "## Recommendations for Tomorrow", ""])

    if tomorrow_focuses:
        for focus in dict.fromkeys(tomorrow_focuses):
            lines.append(
                f"- Continue with your recorded focus: {focus}"
            )
    else:
        lines.append(
            "- Add a specific focus to your next daily reflection."
        )

    if challenges:
        lines.append(
            "- Set aside a manageable practice session for one "
            "recorded challenge."
        )

    if activities:
        total_activity_minutes = sum(
            get_duration(activity) for activity in activities
        )
        lines.append(
            f"- You recorded {format_minutes(total_activity_minutes)} "
            "of activity. Continue tracking your time consistently."
        )

    lines.extend(["", "## Goal Progress", ""])

    if goals:
        for goal in goals:
            title = get_title(goal)

            raw_progress = get_value(
                goal,
                "progress",
                "progress_percentage",
                "progress_percent",
                default=None,
            )

            if raw_progress is None or str(raw_progress).strip() == "":
                progress_text = "Not recorded"
            else:
                progress_text = f"{safe_number(raw_progress):g}%"

            status = clean_text(get_value(goal, "status"))
            deadline = clean_text(get_value(goal, "deadline"))

            lines.append(
                f"- **{title}:** {progress_text} progress; "
                f"status: {status}; deadline: {deadline}."
            )
    else:
        lines.append("- No saved goals found.")

    return "\n".join(lines)


def generate_productivity_summary(
    tasks=None,
    activities=None,
    goals=None,
    reflections=None,
    focus_time=0,
    productivity_score=0,
    **kwargs,
):
    """Generate the dashboard report without requiring Ollama."""

    return build_fallback_summary(
        tasks=tasks,
        activities=activities,
        goals=goals,
        reflections=reflections,
        focus_time=focus_time,
        productivity_score=productivity_score,
    )


# --------------------------------------------------
# AI MEMORY CHAT
# --------------------------------------------------

def ask_productivity_question(question, context=""):
    question = str(question or "").strip()

    if not question:
        return "Please enter a question."

    return generate_response(question, context=context)
