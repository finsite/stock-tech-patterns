"""Handles message queue consumption for RabbitMQ and SQS.

This module receives stock data, applies pattern analysis indicators,
and sends the processed results to the output handler.
"""

import json
import os
import time

import boto3
import pika
from botocore.exceptions import BotoCoreError, NoCredentialsError

from app.logger import setup_logger
from app.processor import analyze_patterns

logger = setup_logger(__name__)

# Determine queue type
QUEUE_TYPE = os.getenv("QUEUE_TYPE", "rabbitmq").lower()

# RabbitMQ config
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "stock_analysis")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "patterns_analysis_queue")
RABBITMQ_ROUTING_KEY = os.getenv("RABBITMQ_ROUTING_KEY", "#")
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

# SQS config
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "")
SQS_REGION = os.getenv("SQS_REGION", "us-east-1")

# Initialize SQS client
sqs_client = None
if QUEUE_TYPE == "sqs":
    try:
        sqs_client = boto3.client("sqs", region_name=SQS_REGION)
        logger.info(f"SQS client initialized for region {SQS_REGION}")
    except (BotoCoreError, NoCredentialsError) as e:
        logger.error("Failed to initialize SQS client: %s", e)
        sqs_client = None


def _connect_to_rabbitmq() -> pika.BlockingConnection:
    """Retries RabbitMQ connection up to 5 times before giving up."""
    retries = 5
    while retries > 0:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            params = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                virtual_host=RABBITMQ_VHOST,
                credentials=credentials,
            )
            conn = pika.BlockingConnection(params)
            if conn.is_open:
                logger.info("Connected to RabbitMQ")
                return conn
        except Exception as e:
            retries -= 1
            logger.warning("RabbitMQ connection failed: %s. Retrying in 5s...", e)
            time.sleep(5)
    raise ConnectionError("Could not connect to RabbitMQ after retries")


def _consume_rabbitmq() -> None:
    """Consume and process messages from RabbitMQ."""
    connection = _connect_to_rabbitmq()
    channel = connection.channel()

    channel.exchange_declare(exchange=RABBITMQ_EXCHANGE, exchange_type="topic", durable=True)
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    channel.queue_bind(
        exchange=RABBITMQ_EXCHANGE, queue=RABBITMQ_QUEUE, routing_key=RABBITMQ_ROUTING_KEY
    )

    def callback(ch, method, properties, body: bytes) -> None:
        """Args:
        ----
          ch:
          method:
          properties:
          body: bytes:
          body: bytes:
          body: bytes:

        Parameters
        ----------
        ch :
            param method:
        properties :
            param body: bytes:
        method :
            param body: bytes:
        body :
            bytes:
        body : bytes :

        body: bytes :


        Returns
        -------


        """
        try:
            message = json.loads(body)
            logger.info("Received message: %s", message)

            analyze_patterns(message)

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError:
            logger.error("Invalid JSON: %s", body)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error("Error processing message: %s", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
    logger.info("Waiting for messages from RabbitMQ...")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping RabbitMQ consumer...")
        channel.stop_consuming()
    finally:
        connection.close()
        logger.info("RabbitMQ connection closed.")


def _consume_sqs() -> None:
    """Consume and process messages from AWS SQS."""
    if not sqs_client or not SQS_QUEUE_URL:
        logger.error("SQS not initialized or missing queue URL.")
        return

    logger.info("Polling for SQS messages...")

    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=10,
            )

            for msg in response.get("Messages", []):
                try:
                    body = json.loads(msg["Body"])
                    logger.info("Received SQS message: %s", body)

                    analyze_patterns(body)

                    sqs_client.delete_message(
                        QueueUrl=SQS_QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"]
                    )
                    logger.info("Deleted SQS message: %s", msg["MessageId"])
                except Exception as e:
                    logger.error("Error processing SQS message: %s", e)
        except Exception as e:
            logger.error("SQS polling failed: %s", e)
            time.sleep(5)


def consume_messages() -> None:
    """Starts the appropriate message consumer based on QUEUE_TYPE."""
    if QUEUE_TYPE == "rabbitmq":
        _consume_rabbitmq()
    elif QUEUE_TYPE == "sqs":
        _consume_sqs()
    else:
        logger.error("Invalid QUEUE_TYPE specified. Use 'rabbitmq' or 'sqs'.")
