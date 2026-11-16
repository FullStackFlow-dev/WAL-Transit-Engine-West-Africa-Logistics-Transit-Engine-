import io
import logging
import sys
from pathlib import Path

from scripts.snowflake_config import connect_snowflake, load_settings


# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

SQL_FILES = {
    "silver": BASE_DIR / "sql" / "silver" / "002_transform_silver.sql",
    "gold": BASE_DIR / "sql" / "gold" / "002_transform_gold.sql",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "run_snowflake_sql.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def connecter():
    couche = sys.argv[1].lower()
    settings = load_settings()
    return connect_snowflake(
        "MIRAH_BI_LOGISTICS_TRANSFORM",
        schema=settings["schemas"][couche],
    )


def main():
    if len(sys.argv) != 2 or sys.argv[1].lower() not in SQL_FILES:
        raise SystemExit("Usage : python -m scripts.run_snowflake_sql silver|gold")

    couche = sys.argv[1].lower()
    chemin = SQL_FILES[couche]

    if not chemin.exists():
        raise FileNotFoundError(f"Fichier SQL introuvable : {chemin}")

    script = chemin.read_text(encoding="utf-8")
    settings = load_settings()
    for nom, schema in settings["schemas"].items():
        script = script.replace(f"{{{{{nom.upper()}_SCHEMA}}}}", schema)
    connexion = connecter()

    try:
        for curseur in connexion.execute_stream(io.StringIO(script)):
            logger.info("%s | %s", couche.upper(), curseur.sfqid)
        logger.info("TRANSFORMATION %s TERMINÉE AVEC SUCCÈS", couche.upper())
    finally:
        connexion.close()


if __name__ == "__main__":
    main()
