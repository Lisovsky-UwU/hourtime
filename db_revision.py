import sys

from alembic import command
from loguru import logger

from src.config import app_config, dev_config
from src.logger import configure_logger
from src.utils import alembic_cfg


def checkout_revision(connection_string: str | None = None) -> None:
    configure_logger(
        level=app_config.log.level,
        retention_days=app_config.log.retention,
        output_to_stdout=app_config.log.output_log_to_stdout,
        super_detailed_exeptions=dev_config.log_detailed_exceptions,
    )
    logger.success(f"{''.ljust(15, '=')} Performing a database revision {''.ljust(15, '=')}")
    if connection_string is None:
        connection_string = app_config.db_postgres.connection_string_psycopg
    try:
        with alembic_cfg(connection_string) as cfg:
            command.revision(
                cfg,
                message=sys.argv[1] if len(sys.argv) > 1 else None,
                autogenerate=True,
            )
        logger.success("The database revision was completed successfully")
    except Exception as e:
        logger.exception(f"The database revision error: {e}")
    logger.success(f"{''.ljust(15, '=')} The database revision is completed {''.ljust(15, '=')}")


if __name__ == "__main__":
    checkout_revision()

