import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "orders")
    db_user: str = os.getenv("DB_USER", "orders_user")
    db_password: str = os.getenv("DB_PASSWORD", "orders_pass")

    kafka_bootstrap_servers: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS", "localhost:19092"
    )

    outbox_poll_interval_seconds: float = float(
        os.getenv("OUTBOX_POLL_INTERVAL_SECONDS", "2")
    )
    outbox_batch_size: int = int(os.getenv("OUTBOX_BATCH_SIZE", "50"))
    outbox_retry_limit: int = int(os.getenv("OUTBOX_RETRY_LIMIT", "5"))


settings = Settings()
