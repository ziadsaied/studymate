"""Central configuration shared by the API, graph, databases, and proxy."""

from dotenv import load_dotenv

# Load local secrets before any module reads provider credentials from the environment.
load_dotenv()

LANGSMITH_PROJECT = "Study Mate AI"

LITELLM_CONFIG_PATH = "config.yaml"
LITELLM_BASE_URL = "http://localhost:4000"
LITELLM_PORT = 4000

# These correspond to the provider-backed model entries in config.yaml.
REQUIRED_ENV_KEYS = ["GROQ_API_KEY_1", "OPENROUTER_API_KEY", "GEMINI_API_KEY"]
DEFAULT_KB_PATH = "Data Analysis Basics.pdf"
CHROMA_PERSIST_DIR = "./studymate_chroma_db"
CHROMA_COLLECTION_NAME = "studymate_knowledge_base"
RECORD_MANAGER_DB_URL = "sqlite:///studymate_record_manager.db"

LTM_DATABASE_FILE = "studymate_long_term_memory.db"
LTM_DATABASE_URL = f"sqlite:///{LTM_DATABASE_FILE}"

CHECKPOINT_DB_PATH = "studymate_checkpoints.sqlite"
# Older messages are summarized; only this many recent messages remain verbatim.
MAX_MESSAGES_TO_KEEP = 10
SUMMARIZE_AFTER_MESSAGES = 10

MAX_TOOL_ROUNDS = 3

# The browser UI is intentionally a local, single-user demo.
DEFAULT_USER_ID = "local_student"
