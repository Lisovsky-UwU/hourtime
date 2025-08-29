import os
import sys
from enum import StrEnum
from typing import Any

from loguru import logger

from version import APP_VERSION

LOG_FORMAT = (
    "{time:HH:mm:ss.SSS} [<lvl>{level:<8}</lvl>] "
    "<{thread.name}>-{module}:{function}({line}) | <lvl>{message}</lvl>"
)


class LoggerLevel(StrEnum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    @classmethod
    def _missing_(cls, value: Any):
        # Converting the value to uppercase for comparison
        value = value.upper() if isinstance(value, str) else value
        try:
            return next(filter(lambda member: member.value == value, tuple(cls)))
        except StopIteration:
            raise ValueError(f"{value} is not a valid {cls.__name__}")  # noqa: B904


def configure_logger(
    level: LoggerLevel,
    retention_days: int,
    output_to_stdout: bool,
    super_detailed_exeptions: bool,
) -> None:
    logger.remove()

    logger.add(
        os.path.join("log", "{time:DD-MM-YYYY}.log"),
        rotation="00:00",
        compression="zip",
        retention=f"{retention_days} days",
        diagnose=super_detailed_exeptions,
        format=LOG_FORMAT,
        level=level,
    )
    if output_to_stdout:
        logger.add(
            sys.stdout,
            diagnose=super_detailed_exeptions,
            format=LOG_FORMAT,
            level=level,
        )

def start_log(app_config_filename: str, dev_config_filename: str) -> None:
    logger.success(f"{''.ljust(15, '=')} Start Hourtime. v{APP_VERSION} {''.ljust(15, '=')}")

    logger.trace("Read app config for log from \"{cfg_path}\"", cfg_path=app_config_filename)
    with open(app_config_filename, "r", encoding="utf-8") as cfg_file:
        logger.info(
            "Current app configuration \"{cfg_path}\":\n\n{cfg_text}\n",
            cfg_path=app_config_filename,
            cfg_text=cfg_file.read(),
        )

    logger.trace(
        "Check dev config is exists from \"{dev_cfg_path}\"",
        dev_cfg_path=dev_config_filename,
    )
    if os.path.exists(dev_config_filename):
        logger.trace(
            "Read dev config for log from \"{dev_cfg_path}\"",
            dev_cfg_path=dev_config_filename,
        )
        with open(dev_config_filename, "r", encoding="utf-8") as dev_cfg_file:
            logger.info(
                "Current dev configuration \"{dev_cfg_path}\":\n\n{dev_cfg_text}\n",
                dev_cfg_path=dev_config_filename,
                dev_cfg_text=dev_cfg_file.read(),
            )
    else:
        logger.trace("Do not have dev config")

