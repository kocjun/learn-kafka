import signal
from typing import Callable, List

from confluent_kafka import Consumer, KafkaException, Message


def create_consumer(
    group_id: str,
    topics: List[str],
    bootstrap_servers: str = "localhost:19092",
) -> Consumer:
    
    config = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest", # 처음부터 읽기 (개발용)
        "enable.auto.commit": True,
    }
    consumer = Consumer(config)
    consumer.subscribe(topics)
    return consumer

def run_consumer_loop(
    consumer: Consumer,
    handle_message: Callable[[Message], None],
    poll_timeout: float = 1.0,
) -> None:
    running = True
    
    def stop(sig, frame):
        nonlocal running
        print("Stopping consumer...")
        running = False

    # Register graceful shutdown handlers
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    
    try:
        print("Starting consumer loop... Press Ctrl+C to stop.")
        while running:
            msg = consumer.poll(poll_timeout)
            if msg is None:
                continue

            if msg.error():
                raise KafkaException(msg.error())

            handle_message(msg)
    except KafkaException as exc:
        print(f"Kafka error: {exc}")
    finally:
        consumer.close()
        print("Consumer closed.")
            
              
    
