import json
from typing import List

from langchain_core.tools import tool

from app.logging_config import logger
from app.schemas import FinalAnswerSchema


@tool(args_schema=FinalAnswerSchema)
def submit_final_answer(answer: str, sources_used: List[str], confidence_score: float) -> str:
    """
    Submit the final structured answer to the user.
    You MUST call this tool to end your turn, once you are done thinking and,
    if needed, calling other tools.
    """
    logger.info("Tool called: submit_final_answer.")
    # JSON is easy for the graph finalizer to parse into the API response shape.
    return json.dumps(
        {"answer": answer, "sources_used": sources_used, "confidence_score": confidence_score},
        ensure_ascii=False,
    )
"""Schema-backed tool used by the model to mark a response as complete."""
