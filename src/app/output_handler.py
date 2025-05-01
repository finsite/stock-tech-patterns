"""
Module to handle output of analysis results to a chosen output target.

This implementation logs the result, prints to stdout, and optionally publishes to a
message queue.
"""

import json
from typing import Any

from app.logger import setup_logger
from app.queue_sender import publish_to_queue

# Initialize logger
logger = setup_logger(__name__)


def send_to_output(data: dict[str, Any]) -> None:
    """
    Outputs processed analysis results to the configured output.

    Currently logs the output, prints to the console,
    and publishes to a queue.

    Args:
    ----
        data (dict[str, Any]): The processed analysis result.

    Returns:
    -------
        None
    """
    try:
        formatted_output = json.dumps(data, indent=4)

        # Log the output
        logger.info("Sending data to output:\n%s", formatted_output)

        # Print to stdout (useful in container logs)
        print(formatted_output)

        # Publish to message queue
        publish_to_queue([data])

    except Exception as e:
        logger.error("Failed to send output: %s", e)
