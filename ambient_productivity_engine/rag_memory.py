
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from database import (
    get_tasks,
    get_activities,
    get_goals,
    get_reflections,
)


# --------------------------------------------------
# 1. CHROMADB CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_memory"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="productivity_memories",
    embedding_function=embedding_function,
)


# --------------------------------------------------
# 2. HELPER FUNCTIONS
# --------------------------------------------------

def get_value(record, *keys, default=""):
    """Read a value from a dictionary or SQLite Row."""
    for key in keys:
        try:
            value = record.get(key)
        except AttributeError:
            try:
                value = record[key]
            except (KeyError, IndexError, TypeError):
                value = None

        if value is not None:
            return value

    return default


def clean_text(value):
    """Convert a value into safe, readable text."""
    if value is None or str(value).strip() == "":
        return "Not recorded"
    return str(value).strip()


# --------------------------------------------------
# 3. COLLECT TASKS, ACTIVITIES, GOALS AND REFLECTIONS
# --------------------------------------------------

def collect_memories():
    memories = []

    # Tasks
    for item in get_tasks():
        record_id = get_value(item, "id")

        text = (
            f"Task: {clean_text(get_value(item, 'title', 'task_name', 'name'))}. "
            f"Description: {clean_text(get_value(item, 'description'))}. "
            f"Priority: {clean_text(get_value(item, 'priority'))}. "
            f"Deadline: {clean_text(get_value(item, 'deadline'))}. "
            f"Status: {clean_text(get_value(item, 'status'))}."
        )

        memories.append({
            "id": f"task_{record_id}",
            "text": text,
            "metadata": {
                "source": "task",
                "record_id": str(record_id),
            },
        })

    # Activities
    for item in get_activities():
        record_id = get_value(item, "id")

        text = (
            f"Activity: {clean_text(get_value(item, 'activity_type', 'activity', 'name'))}. "
            f"Duration: {clean_text(get_value(item, 'duration_minutes', 'duration'))} minutes. "
            f"Date: {clean_text(get_value(item, 'date'))}. "
            f"Description: {clean_text(get_value(item, 'description'))}."
        )

        memories.append({
            "id": f"activity_{record_id}",
            "text": text,
            "metadata": {
                "source": "activity",
                "record_id": str(record_id),
            },
        })

    # Goals
    for item in get_goals():
        record_id = get_value(item, "id")

        text = (
            f"Goal: {clean_text(get_value(item, 'title', 'goal_name', 'name'))}. "
            f"Description: {clean_text(get_value(item, 'description'))}. "
            f"Deadline: {clean_text(get_value(item, 'deadline'))}. "
            f"Progress: {clean_text(get_value(item, 'progress'))} percent. "
            f"Status: {clean_text(get_value(item, 'status'))}."
        )

        memories.append({
            "id": f"goal_{record_id}",
            "text": text,
            "metadata": {
                "source": "goal",
                "record_id": str(record_id),
            },
        })

    # Daily reflections
    for item in get_reflections():
        record_id = get_value(item, "id")
        reflection_date = get_value(item, "date")

        text = (
            f"Daily Reflection. "
            f"Date: {clean_text(reflection_date)}. "
            f"Mood: {clean_text(get_value(item, 'mood'))}. "
            f"Energy level: {clean_text(get_value(item, 'energy_level'))} out of 5. "
            f"What went well: "
            f"{clean_text(get_value(item, 'accomplishments'))}. "
            f"Challenges: "
            f"{clean_text(get_value(item, 'challenges'))}. "
            f"Learnings: "
            f"{clean_text(get_value(item, 'learnings'))}. "
            f"Tomorrow's focus: "
            f"{clean_text(get_value(item, 'tomorrow_focus'))}."
        )

        memories.append({
            # Reuses the existing ID to update the same reflection.
            "id": f"reflection_{record_id}",
            "text": text,
            "metadata": {
                "source": "reflection",
                "record_id": str(record_id),
                "date": str(reflection_date or ""),
            },
        })

    return memories


# --------------------------------------------------
# 4. REFRESH CHROMADB MEMORY
# --------------------------------------------------

def refresh_personal_memory():
    """Insert or update current database records in ChromaDB."""
    memories = collect_memories()

    if not memories:
        return 0

    collection.upsert(
        ids=[item["id"] for item in memories],
        documents=[item["text"] for item in memories],
        metadatas=[item["metadata"] for item in memories],
    )

    return len(memories)


# --------------------------------------------------
# 5. DETECT QUESTION CATEGORY
# --------------------------------------------------


def detect_category(question):
    question = question.lower()

    goal_words = [
        "goal", "goals", "progress", "deadline", "target",
    ]

    task_words = [
        "task", "tasks", "pending", "to-do", "todo",
    ]

    activity_words = [
        "activity", "activities", "minutes",
        "focus time", "spent time", "practice session",
    ]

    reflection_words = [
        "reflection", "learn", "learnt", "learning",
        "mood", "energy", "went well", "challenge",
        "tomorrow", "focus", "accomplishment",
        "what did i do", "what did i improve",
    ]

    # Check goals first because "Machine Learning"
    # contains "learning".
    if any(word in question for word in goal_words):
        return "goal"

    if any(word in question for word in task_words):
        return "task"

    if any(word in question for word in activity_words):
        return "activity"

    if any(word in question for word in reflection_words):
        return "reflection"

    return None



# --------------------------------------------------
# 6. SEARCH PERSONAL MEMORY
# --------------------------------------------------

def search_personal_memory(question, n_results=5):
    """Retrieve relevant memories from ChromaDB."""

    # Keep memory synchronized with the current SQLite records.
    refresh_personal_memory()

    category = detect_category(question)

    count = collection.count()
    if count == 0:
        return []

    query_args = {
        "query_texts": [question],
        "n_results": min(n_results, count),
        "include": ["documents", "metadatas", "distances"],
    }

    if category:
        query_args["where"] = {"source": category}

    results = collection.query(**query_args)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    memories = []

    for index, document in enumerate(documents):
        metadata = metadatas[index] or {}

        memories.append({
            "text": document,
            "source": metadata.get("source", "unknown"),
            "record_id": metadata.get("record_id", ""),
            "metadata": metadata,
            "distance": (
                distances[index] if index < len(distances) else None
            ),
        })

    return memories


# --------------------------------------------------
# 7. OPTIONAL: MANUALLY REFRESH MEMORY
# --------------------------------------------------

if __name__ == "__main__":
    total = refresh_personal_memory()
    print(f"Personal memory refreshed successfully. Records indexed: {total}")

    print("\nTesting reflection retrieval:")
    results = search_personal_memory(
        "What did I learn on October 9, 2026?"
    )

    for memory in results:
        print(f"\nSource: {memory['source']}")
        print(f"Record ID: {memory['record_id']}")
        print(f"Memory: {memory['text']}")