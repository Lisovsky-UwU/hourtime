import os

from src.ext.parametrica import Field, Fieldset, Parametrica
from src.ext.parametrica.io import VirtualYAMLFileConfigIO, YAMLFileConfigIO
from src.logger import LoggerLevel
from src.utils import generate_random_string

if not os.path.exists("data/"):
    os.mkdir("data/")

APP_CONFIG_FILENAME = os.path.join("data", "config.yaml")
DEV_CONFIG_FILENAME = "dev.yaml"


class PostgreSettings(Fieldset):
    host = Field[str]("127.0.0.1").label("Database host")
    port = Field[int](5432).label("Database port")
    db_name = Field[str]("").label("Database name")
    username = Field[str]("").label("User to access database")
    password = Field[str]("").label("Password for database user")

    @property
    def connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"


class ApiSettings(Fieldset):
    host = Field[str]("0.0.0.0").label("API address (default 0.0.0.0 - host to all networks)")
    port = Field[int](80).label("API port")
    cert_path = Field[str]("").label("The path to the certificate file") \
        .hint("If left blank, the HTTP protocol will be used")
    key_path = Field[str]("").label("The path to the key certificate file") \
        .hint("If left blank, the HTTP protocol will be used")


class AppSettings(Fieldset):
    hash_salt = Field[str](generate_random_string).label("Salt for generate user tokens")


class LogSettings(Fieldset):
    level = Field[LoggerLevel](LoggerLevel.INFO).label("Logger level").hint(
        f'Available values: {", ".join(val.value for val in LoggerLevel)}',
    )
    retention = Field[int](10).label("How many days are the old logs stored")
    max_log_file_size = Field[int](100).label("Maximum log file size in MB")
    output_log_to_stdout = Field[bool](False).label("Output logs in StdOut")


class AppConfig(Parametrica):
    db_postgres = Field[PostgreSettings]().label("Parameters for connection to PostgreSQL")
    api_server = Field[ApiSettings]().label("Parameters for API")
    app = Field[AppSettings]().label("Parameters for app")
    log = Field[LogSettings]().label("Parameters for logger")


class DevConfig(Parametrica):
    log_detailed_exceptions = Field[bool](False).label(
        "Detailed exceptions of the EXCEPTION level in the stdout logs",
    )


app_config = AppConfig(YAMLFileConfigIO(APP_CONFIG_FILENAME, export_comments=True))
dev_config = DevConfig(VirtualYAMLFileConfigIO(DEV_CONFIG_FILENAME))

