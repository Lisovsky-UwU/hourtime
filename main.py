from loguru import logger

from src.api import start_api
from src.config import APP_CONFIG_FILENAME, DEV_CONFIG_FILENAME, app_config, dev_config
from src.logger import configure_logger, start_log


def main() -> None:
    configure_logger(
        level=app_config.log.level,
        retention_days=app_config.log.retention,
        output_to_stdout=app_config.log.output_log_to_stdout,
        super_detailed_exeptions=dev_config.log_detailed_exceptions,
    )

    start_log(APP_CONFIG_FILENAME, DEV_CONFIG_FILENAME)

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


if __name__ == "__main__":
    main()

