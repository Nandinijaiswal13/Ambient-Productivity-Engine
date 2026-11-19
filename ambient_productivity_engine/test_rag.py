
from rag_memory import (
    refresh_personal_memory,
    search_personal_memory,
)

print("Indexing productivity records...")

count = refresh_personal_memory()

print(f"Records indexed: {count}")

question = input(
    "\nAsk a question about your productivity history: "
)

results = search_personal_memory(question, n_results=5)

print("\nRETRIEVED MEMORIES")
print("=" * 40)

if not results:
    print("No matching memories found.")
else:
    for i, memory in enumerate(results, start=1):
        print(f"\nMemory {i}: {memory['source']}")
        print(memory["document"])