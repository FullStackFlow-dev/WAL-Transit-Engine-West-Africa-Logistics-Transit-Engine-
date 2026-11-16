import logging
from pathlib import Path

from scripts.snowflake_config import connect_snowflake, load_settings


# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS = load_settings()
DATABASE = SETTINGS["database"]
SCHEMA = SETTINGS["schemas"]["bronze"]
STAGE = f"{DATABASE}.{SCHEMA}.LOGISTICS_STAGE"
FILE_FORMAT = f"{DATABASE}.{SCHEMA}.JSON_LINES_FORMAT"

FILES = {
    "CHAUFFEURS": "chauffeurs.json",
    "VEHICULES": "vehicules.json",
    "ENTREPOTS": "entrepots.json",
    "EXPEDITIONS": "expeditions.json",
    "LIVRAISONS": "livraisons.json",
}

COPY_SELECTS = {
    "CHAUFFEURS": """
        $1:chauffeur_id::NUMBER,
        $1:nom::VARCHAR,
        $1:pays::VARCHAR,
        $1:ville::VARCHAR,
        $1:date_integration::DATE,
        $1:statut::VARCHAR,
        $1:source_system::VARCHAR,
        $1:batch_id::VARCHAR,
        $1:ingested_at::TIMESTAMP_NTZ
    """,
    "VEHICULES": """
        $1:vehicule_id::NUMBER,
        $1:chauffeur_id::NUMBER,
        $1:pays::VARCHAR,
        $1:ville::VARCHAR,
        $1:type_vehicule::VARCHAR,
        $1:marque::VARCHAR,
        $1:annee::NUMBER,
        $1:capacite_kg::NUMBER,
        $1:capacite_m3::NUMBER(12,2),
        $1:statut::VARCHAR,
        $1:source_system::VARCHAR,
        $1:batch_id::VARCHAR,
        $1:ingested_at::TIMESTAMP_NTZ
    """,
    "ENTREPOTS": """
        $1:entrepot_id::NUMBER,
        $1:nom_entrepot::VARCHAR,
        $1:pays::VARCHAR,
        $1:ville::VARCHAR,
        $1:capacite_m3::NUMBER(14,2),
        $1:volume_stocke_m3::NUMBER(14,2),
        $1:taux_occupation_pct::NUMBER(7,2),
        $1:statut::VARCHAR,
        $1:source_system::VARCHAR,
        $1:batch_id::VARCHAR,
        $1:ingested_at::TIMESTAMP_NTZ
    """,
    "EXPEDITIONS": """
        $1:expedition_id::NUMBER,
        $1:chauffeur_id::NUMBER,
        $1:vehicule_id::NUMBER,
        $1:entrepot_origine_id::NUMBER,
        $1:entrepot_destination_id::NUMBER,
        $1:pays_origine::VARCHAR,
        $1:ville_origine::VARCHAR,
        $1:pays_destination::VARCHAR,
        $1:ville_destination::VARCHAR,
        $1:date_expedition::TIMESTAMP_NTZ,
        $1:date_livraison_prevue::TIMESTAMP_NTZ,
        $1:type_marchandise::VARCHAR,
        $1:poids_kg::NUMBER(14,2),
        $1:volume_m3::NUMBER(14,2),
        $1:distance_km::NUMBER(14,2),
        $1:cout_transport_xof::NUMBER(18,2),
        $1:statut_expedition::VARCHAR,
        $1:source_system::VARCHAR,
        $1:batch_id::VARCHAR,
        $1:ingested_at::TIMESTAMP_NTZ
    """,
    "LIVRAISONS": """
        $1:livraison_id::NUMBER,
        $1:expedition_id::NUMBER,
        $1:chauffeur_id::NUMBER,
        $1:vehicule_id::NUMBER,
        $1:date_livraison_prevue::TIMESTAMP_NTZ,
        $1:date_livraison_reelle::TIMESTAMP_NTZ,
        $1:statut_livraison::VARCHAR,
        $1:incident::VARCHAR,
        $1:pays_destination::VARCHAR,
        $1:ville_destination::VARCHAR,
        $1:source_system::VARCHAR,
        $1:batch_id::VARCHAR,
        $1:ingested_at::TIMESTAMP_NTZ
    """,
}

EXPECTED = {
    "CHAUFFEURS": 10_000,
    "VEHICULES": 8_000,
    "ENTREPOTS": 200,
    "EXPEDITIONS": 1_000_000,
    "LIVRAISONS": 1_000_000,
}


# LOGGING

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "load_bronze_snowflake.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# CONNEXION

def connecter():
    return connect_snowflake("MIRAH_BI_LOGISTICS_BRONZE_LOAD", schema=SCHEMA)


# CHARGEMENT

def main():
    for fichier in FILES.values():
        chemin = BRONZE_DIR / fichier
        if not chemin.exists():
            raise FileNotFoundError(f"Fichier Bronze introuvable : {chemin}")

    connexion = connecter()
    curseur = connexion.cursor()

    try:
        curseur.execute(f"USE DATABASE {DATABASE}")
        curseur.execute(f"USE SCHEMA {SCHEMA}")
        curseur.execute(
            f"CREATE FILE FORMAT IF NOT EXISTS {FILE_FORMAT} "
            "TYPE = JSON COMPRESSION = AUTO STRIP_OUTER_ARRAY = FALSE"
        )
        curseur.execute(f"CREATE STAGE IF NOT EXISTS {STAGE}")

        for table, fichier in FILES.items():
            chemin = (BRONZE_DIR / fichier).resolve()
            uri = f"file://{chemin.as_posix()}"
            dossier_stage = table.lower()

            logger.info("Chargement de %s", table)
            curseur.execute(f"REMOVE @{STAGE}/{dossier_stage}")
            curseur.execute(
                f"PUT '{uri}' @{STAGE}/{dossier_stage} "
                "AUTO_COMPRESS=TRUE OVERWRITE=TRUE PARALLEL=4"
            )
            curseur.execute(f"TRUNCATE TABLE {DATABASE}.{SCHEMA}.{table}")

            copy_sql = f"""
                COPY INTO {DATABASE}.{SCHEMA}.{table}
                FROM (
                    SELECT {COPY_SELECTS[table]}
                    FROM @{STAGE}/{dossier_stage}
                )
                FILE_FORMAT = (FORMAT_NAME = '{FILE_FORMAT}')
                ON_ERROR = 'ABORT_STATEMENT'
                FORCE = TRUE
            """
            resultats = curseur.execute(copy_sql).fetchall()
            logger.info("COPY %s : %s", table, resultats)

            obtenu = curseur.execute(
                f"SELECT COUNT(*) FROM {DATABASE}.{SCHEMA}.{table}"
            ).fetchone()[0]
            attendu = EXPECTED[table]

            if obtenu != attendu:
                raise ValueError(
                    f"{table}: {obtenu:,} lignes au lieu de {attendu:,}"
                )

            logger.info("%s : %,d lignes | OK", table, obtenu)

        logger.info("CHARGEMENT BRONZE SNOWFLAKE TERMINÉ AVEC SUCCÈS")
    finally:
        curseur.close()
        connexion.close()


if __name__ == "__main__":
    main()
