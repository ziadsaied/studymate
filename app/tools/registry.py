from app.llm import agent_llm
from app.logging_config import logger
from app.tools.final_answer import submit_final_answer
from app.tools.memory_tools import recall_all_preferences, recall_user_preference, remember_user_preference
from app.tools.rag_tool import retrieve_internal_documents
from app.tools.web import define_term, web_search

# ToolNode executes only research/memory tools; final answers are handled by finalize().
research_tools = [
    web_search,
    define_term,
    retrieve_internal_documents,
    remember_user_preference,
    recall_user_preference,
    recall_all_preferences,
]
# The model sees the final-answer schema even though it bypasses ToolNode.
all_tools = research_tools + [submit_final_answer]
agent_llm_with_tools = agent_llm.bind_tools(all_tools)

logger.info("Agent tools bound (via agent-pool): %s", [t.name for t in all_tools])
"""Register tools and bind them to the agent model in one central place."""
