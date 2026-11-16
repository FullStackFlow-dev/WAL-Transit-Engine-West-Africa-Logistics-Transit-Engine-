import os
from pathlib import Path

import snowflake.connector
import yaml
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent


def load_settings():
    load_dotenv(BASE_DIR / ".env", override=True)
    environment = os.getenv("APP_ENV", "local").lower()
    config_path = BASE_DIR / "config" / f"{environment}.yaml"
    if not config_path.is_file():
        raise ValueError(f"Environnement APP_ENV inconnu : {environment}")

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    snowflake = config.get("snowflake", {})
    settings = {
        "environment": environment,
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR", "externalbrowser"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE") or snowflake.get("role"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE") or snowflake.get("warehouse"),
        "database": os.getenv("SNOWFLAKE_DATABASE") or snowflake.get("database"),
        "schemas": {
            "bronze": snowflake.get("bronze_schema", "BRONZE"),
            "silver": snowflake.get("silver_schema", "SILVER"),
            "gold": snowflake.get("gold_schema", "GOLD"),
        },
    }
    if not settings["database"]:
        raise ValueError(
            "Base Snowflake absente : définissez SNOWFLAKE_DATABASE ou choisissez APP_ENV=dev/prod."
        )
    if not settings["warehouse"]:
        raise ValueError(
            "Warehouse Snowflake absent : définissez SNOWFLAKE_WAREHOUSE ou choisissez APP_ENV=dev/prod."
        )
    return settings


def connect_snowflake(query_tag, schema=None):
    settings = load_settings()
    if settings["authenticator"].lower() == "snowflake" and not settings["password"]:
        raise ValueError(
            "SNOWFLAKE_PASSWORD est requis lorsque SNOWFLAKE_AUTHENTICATOR=snowflake."
        )
    parameters = {
        "account": settings["account"],
        "user": settings["user"],
        "authenticator": settings["authenticator"],
        "enable_server_session_keep_alive_auto_detection": False,
        "session_parameters": {"QUERY_TAG": query_tag},
    }
    for key in ("role", "warehouse", "database"):
        if settings[key]:
            parameters[key] = settings[key]
    if schema:
        parameters["schema"] = schema
    if settings["password"] and settings["authenticator"].lower() == "snowflake":
        parameters["password"] = settings["password"]
    return snowflake.connector.connect(**parameters)
