import logging
from pathlib import Path

from scripts.snowflake_config import connect_snowflake, load_settings


# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS = load_settings()
DATABASE = SETTINGS["database"]
SCHEMAS = SETTINGS["schemas"]

EXPECTED = {
    SCHEMAS["bronze"]: {
        "CHAUFFEURS": 10_000,
        "VEHICULES": 8_000,
        "ENTREPOTS": 200,
        "EXPEDITIONS": 1_000_000,
        "LIVRAISONS": 1_000_000,
    },
    SCHEMAS["silver"]: {
        "CHAUFFEURS": 10_000,
        "VEHICULES": 8_000,
        "ENTREPOTS": 200,
        "EXPEDITIONS": 1_000_000,
        "LIVRAISONS": 1_000_000,
    },
    SCHEMAS["gold"]: {
        "DIM_PAYS": 10,
        "DIM_CHAUFFEUR": 10_000,
        "DIM_VEHICULE": 8_000,
        "DIM_ENTREPOT": 200,
        "FACT_EXPEDITION": 1_000_000,
        "FACT_LIVRAISON": 1_000_000,
        "KPI_GLOBAL": 1,
        "KPI_PAYS": 10,
        "KPI_ENTREPOTS": 200,
    },
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "validate_snowflake.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def connecter():
    return connect_snowflake("MIRAH_BI_LOGISTICS_VALIDATION")


def main():
    connexion = connecter()
    curseur = connexion.cursor()
    erreurs = []

    try:
        for schema, tables in EXPECTED.items():
            for table, attendu in tables.items():
                obtenu = curseur.execute(
                    f"SELECT COUNT(*) FROM {DATABASE}.{schema}.{table}"
                ).fetchone()[0]
                statut = "OK" if obtenu == attendu else "ERREUR"
                logger.info(
                    "%s.%s | attendu=%,d | obtenu=%,d | %s",
                    schema,
                    table,
                    attendu,
                    obtenu,
                    statut,
                )
                if obtenu != attendu:
                    erreurs.append(
                        f"{schema}.{table}: {obtenu:,} au lieu de {attendu:,}"
                    )

        silver = SCHEMAS["silver"]
        controles = {
            "Silver chauffeurs orphelins": """
                SELECT COUNT(*)
                FROM {silver}.VEHICULES v
                LEFT JOIN {silver}.CHAUFFEURS c USING (chauffeur_id)
                WHERE c.chauffeur_id IS NULL
            """.format(silver=silver),
            "Silver expéditions orphelines": """
                SELECT COUNT(*)
                FROM {silver}.EXPEDITIONS e
                LEFT JOIN {silver}.CHAUFFEURS c USING (chauffeur_id)
                LEFT JOIN {silver}.VEHICULES v USING (vehicule_id)
                WHERE c.chauffeur_id IS NULL OR v.vehicule_id IS NULL
            """.format(silver=silver),
            "Silver livraisons orphelines": """
                SELECT COUNT(*)
                FROM {silver}.LIVRAISONS l
                LEFT JOIN {silver}.EXPEDITIONS e USING (expedition_id)
                WHERE e.expedition_id IS NULL
            """.format(silver=silver),
        }

        for nom, requete in controles.items():
            obtenu = curseur.execute(requete).fetchone()[0]
            logger.info("%s | obtenu=%,d", nom, obtenu)
            if obtenu != 0:
                erreurs.append(f"{nom}: {obtenu:,}")

        if erreurs:
            raise ValueError("Validation Snowflake échouée : " + " | ".join(erreurs))

        logger.info("VALIDATION SNOWFLAKE : OK")
    finally:
        curseur.close()
        connexion.close()


if __name__ == "__main__":
    main()
