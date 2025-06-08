"""Main application entry point for stock-tech-patterns.

This module initializes logging and starts the message processing loop.
"""

from app.utils.setup_logger import setup_logger
from app.queue_handler import consume_messages

# Set up logger for this module
logger = setup_logger("main")


def main() -> None:
    """Starts the chart pattern analysis message processing loop."""
    logger.info("Starting stock-tech-patterns processor...")
    try:
        consume_messages()
    except KeyboardInterrupt:
        logger.info("Chart pattern processor stopped by user.")
    except Exception as e:
        logger.exception("Fatal error occurred: %s", str(e))


if __name__ == "__main__":
    main()
