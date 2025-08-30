import os
import secrets
import string
from contextlib import contextmanager
from hashlib import sha1
from typing import Any, Generator

from alembic import command, config
from loguru import logger


def generate_random_string(length: int = 30) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(characters) for _ in range(length))


def calculate_hash(data: str, salt: str) -> str:
    return sha1(f"{salt}{data}{salt}".encode(errors="replace")).hexdigest()


@contextmanager
def alembic_cfg(db_connection_string: str) -> Generator[config.Config, Any, Any]:
    script_location = None
    cfg = config.Config()
    script_location = os.path.join(os.getcwd(), "migrations")

    cfg.set_main_option("script_location", script_location)
    cfg.set_main_option("sqlalchemy.url", db_connection_string)
    cfg.set_main_option("version_path_separator", "os")
    cfg.set_main_option("prepend_sys_path", ".")

    yield cfg


def do_migrate(db_connection_string: str) -> None:
    try:
        logger.info("Checking and applying database migrations")
        with alembic_cfg(db_connection_string) as cfg:
            command.upgrade(cfg, "head")
        logger.success("All migrations are complited")
    except Exception as e:
        logger.exception("Error to apply database migrations")
        raise e

