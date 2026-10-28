import asyncio

from app.bootstrap import shutdown, startup
from app.memory.store import get_user_sidebar_history
from app.rag.ingestion import add_uploaded_pdf
from app.service import run_agentic_rag


async def ask_studymate(question: str, session_id: str, user_id: str = None) -> dict:
    """Call the same service layer as the web UI with convenient demo arguments."""
    payload = {"query": question, "session_id": session_id}
    if user_id is not None:
        payload["user_id"] = user_id
    result = await run_agentic_rag(payload)
    if "error" in result:
        print(f"Error: {result['error']}")
    return result


def format_answer(result: dict) -> str:
    """Render a service result in a readable command-line format."""
    if "error" in result:
        return f"Error: {result['error']}"
    sources = ", ".join(result.get("sources_used", [])) or "none"
    return f"{result.get('answer', '')}\n\nSources: {sources}"


async def main() -> None:
    """Run a sequence of representative StudyMate conversations."""
    startup()
    try:
        # The first questions demonstrate retrieval, follow-ups, and exact-question caching.
        result1 = await ask_studymate("What is overfitting in machine learning?", session_id="student_Ziad")
        print(format_answer(result1))

        result1_followup = await ask_studymate("Can you give me a simple real-life example of it?", session_id="student_Ziad")
        print(format_answer(result1_followup))

        result1_repeat = await ask_studymate("What is overfitting in machine learning?", session_id="student_Ziad")
        print(format_answer(result1_repeat))

        tool_answer_ziad = await ask_studymate(
            "Search the web for a recent technique to reduce the problem we discussed earlier.",
            session_id="student_Ziad",
        )
        print(format_answer(tool_answer_ziad))

        rag_answer_default_kb = await ask_studymate(
            "Based on my study materials, summarize the main topic they cover.",
            session_id="student_Ziad",
        )
        print(format_answer(rag_answer_default_kb))

        # This simulates the browser upload endpoint using a local file instead.
        student_uploaded_pdf_path = "Sec RAG.pdf"
        add_uploaded_pdf(student_uploaded_pdf_path)
        rag_answer_uploaded = await ask_studymate(
            f"Based on {student_uploaded_pdf_path}, what are the main points it covers?",
            session_id="student_Ziad",
        )
        print(format_answer(rag_answer_uploaded))

        rag_fallback_answer = await ask_studymate(
            "According to my study materials, who won the most recent Nobel Prize in Physics?",
            session_id="student_Ziad",
        )
        print(format_answer(rag_fallback_answer))

        remember_result = await ask_studymate(
            "Please remember for the future that my favorite programming language is Python.",
            session_id="student_Ziad",
        )
        print(format_answer(remember_result))

        # A different thread but the same user_id verifies long-term memory survives chats.
        recall_result = await ask_studymate(
            "What's my favorite programming language?",
            session_id="student_Ziad_new_thread",
            user_id="student_Ziad",
        )
        print(format_answer(recall_result))

        for row in get_user_sidebar_history("student_Ziad"):
            print(row)
    finally:
        shutdown()


if __name__ == "__main__":
    asyncio.run(main())
"""End-to-end command-line demonstration of chat, retrieval, web, and memory flows."""
