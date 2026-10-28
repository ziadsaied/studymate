"""Configure one consistent application logger for all StudyMate modules."""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
# Import this named logger instead of creating independent loggers in each module.
logger = logging.getLogger("studymate")
