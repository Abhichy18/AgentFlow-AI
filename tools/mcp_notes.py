from memory.faiss_store import search_notes


def find_relevant_notes(goal_text: str, k: int = 4) -> list[str]:
    return search_notes(goal_text, k=k)
