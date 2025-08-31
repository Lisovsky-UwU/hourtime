import asyncio

from loguru import logger

from src.api import start_api
from src.cache import AppCacher
from src.config import APP_CONFIG_FILENAME, DEV_CONFIG_FILENAME, app_config, dev_config
from src.database import DataBaseSession
from src.logger import configure_logger, start_log
from src.utils import do_migrate


def main() -> None:
    configure_logger(
        level=app_config.log.level,
        retention_days=app_config.log.retention,
        output_to_stdout=app_config.log.output_log_to_stdout,
        super_detailed_exeptions=dev_config.log_detailed_exceptions,
    )

    start_log(APP_CONFIG_FILENAME, DEV_CONFIG_FILENAME)

    do_migrate(app_config.db_postgres.connection_string_psycopg)

    logger.info("Initializing a database connection")
    DataBaseSession.create_engine()
    logger.success("Connection to the database has been successfully initialized")

    logger.info("Initializing application cache")
    AppCacher.setup_cache()
    logger.success("application cache has been successfully initialized")

    try:
        start_api(
            host=app_config.api_server.host,
            port=app_config.api_server.port,
            ssl_cert_path=app_config.api_server.cert_path or None,
            ssl_key_path=app_config.api_server.key_path or None,
        )

    except KeyboardInterrupt:
        logger.debug("Event received KeyboardInterrupt")
    except Exception as e:
        logger.exception(e)
        logger.critical("Unexpected shutdown of the application")
    else:
        logger.success("Regular shutdown of the application")
    finally:
        logger.info("Close connection to the database")
        asyncio.run(DataBaseSession.close_engine())
        logger.info("The database connection has been closed")

        logger.info("Close cache connection")
        asyncio.run(AppCacher.close_cache())
        logger.info("Cache connection has been closed")

        logger.success(f"{''.ljust(15, '=')} The app has shut down {''.ljust(15, '=')}")


if __name__ == "__main__":
    main()

