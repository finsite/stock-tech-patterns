"""Repo-specific configuration for stock-tech-patterns."""

from app.config_shared import *


def get_poller_name() -> str:
    """Return the name of the poller for this service."""
    return get_config_value("POLLER_NAME", "stock_tech_patterns")


def get_rabbitmq_queue() -> str:
    """Return the RabbitMQ queue name for this poller."""
    return get_config_value("RABBITMQ_QUEUE", "stock_tech_patterns_queue")


def get_dlq_name() -> str:
    """Return the Dead Letter Queue (DLQ) name for this poller."""
    return get_config_value("DLQ_NAME", "stock_tech_patterns_dlq")
