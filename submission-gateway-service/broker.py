import os
import json
import aio_pika
from dotenv import load_dotenv
from models import Submission

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "submissions")

class MessageBroker:
    connection: aio_pika.RobustConnection = None
    channel: aio_pika.RobustChannel = None
    exchange: aio_pika.RobustExchange = None

broker = MessageBroker()

async def connect_to_rabbitmq():
    broker.connection = await aio_pika.connect_robust(RABBITMQ_URL)
    broker.channel = await broker.connection.channel()
    
    # Declare queue to ensure it exists
    await broker.channel.declare_queue(RABBITMQ_QUEUE, durable=True)
    print("Connected to RabbitMQ.")

async def close_rabbitmq_connection():
    if broker.connection:
        await broker.connection.close()
        print("Closed RabbitMQ connection.")

async def publish_submission(submission: Submission):
    """Publish a SubmissionCreated event to the message broker."""
    if not broker.channel:
        raise Exception("RabbitMQ channel not initialized")

    message_body = submission.model_dump_json()
    
    message = aio_pika.Message(
        body=message_body.encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )
    
    await broker.channel.default_exchange.publish(
        message,
        routing_key=RABBITMQ_QUEUE,
    )
    print(f"Published submission {submission.id} to queue {RABBITMQ_QUEUE}")
