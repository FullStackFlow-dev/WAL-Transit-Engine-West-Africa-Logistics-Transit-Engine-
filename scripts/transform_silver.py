import gzip
import logging
from pathlib import Path

import pandas as pd


# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "silver"
LOG_DIR = BASE_DIR / "logs"

SILVER_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 100_000

FILES = {
    "chauffeurs": "chauffeurs.json",
    "vehicules": "vehicules.json",
    "entrepots": "entrepots.json",
    "expeditions": "expeditions.json",
    "livraisons": "livraisons.json",
}

PRIMARY_KEYS = {
    "chauffeurs": "chauffeur_id",
    "vehicules": "vehicule_id",
    "entrepots": "entrepot_id",
    "expeditions": "expedition_id",
    "livraisons": "livraison_id",
}

PAYS = {
    "Sénégal",
    "Côte d'Ivoire",
    "Mali",
    "Guinée",
    "Burkina Faso",
    "Bénin",
    "Togo",
    "Mauritanie",
    "Ghana",
    "Gambie",
}


# LOGGING

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            LOG_DIR / "transform_silver.log",
            encoding="utf-8",
        ),
    ],
)

logger = logging.getLogger(__name__)


# OUTILS

def nettoyer_texte(df):
    for colonne in df.columns:
        if (
            df[colonne].dtype == "object"
            or pd.api.types.is_string_dtype(df[colonne])
        ):
            df[colonne] = df[colonne].map(
                lambda valeur: valeur.strip()
                if isinstance(valeur, str)
                else valeur
            )
    return df


def convertir_dates(df, colonnes):
    for colonne in colonnes:
        if colonne in df.columns:
            df[colonne] = pd.to_datetime(
                df[colonne],
                errors="coerce",
            )
    return df


def convertir_entiers(df, colonnes):
    for colonne in colonnes:
        if colonne in df.columns:
            df[colonne] = pd.to_numeric(
                df[colonne],
                errors="coerce",
            ).astype("Int64")
    return df


def convertir_numeriques(df, colonnes):
    for colonne in colonnes:
        if colonne in df.columns:
            df[colonne] = pd.to_numeric(
                df[colonne],
                errors="coerce",
            )
    return df


def finaliser(df, nom):
    cle_primaire = PRIMARY_KEYS[nom]
    df = df.dropna(subset=[cle_primaire])
    df = df.drop_duplicates(
        subset=[cle_primaire],
        keep="last",
    )
    df["silver_processed_at"] = pd.Timestamp.now()
    return df.reset_index(drop=True)


def compter_lignes_csv_gzip(chemin):
    with gzip.open(chemin, "rt", encoding="utf-8") as fichier:
        total = sum(1 for ligne in fichier if ligne.strip())
    return max(total - 1, 0)


# TRANSFORMATIONS

def transformer_chauffeurs(df):
    df = nettoyer_texte(df)
    df = convertir_entiers(df, ["chauffeur_id"])
    df = convertir_dates(
        df,
        ["date_integration", "ingested_at"],
    )
    df = df[df["pays"].isin(PAYS)].copy()
    df = df[
        df["nom"].notna()
        & df["ville"].notna()
        & df["date_integration"].notna()
    ].copy()
    return finaliser(df, "chauffeurs")


def transformer_vehicules(df):
    df = nettoyer_texte(df)
    df = convertir_entiers(
        df,
        [
            "vehicule_id",
            "chauffeur_id",
            "annee",
            "capacite_kg",
        ],
    )
    df = convertir_numeriques(df, ["capacite_m3"])
    df = convertir_dates(df, ["ingested_at"])
    df = df[df["pays"].isin(PAYS)].copy()
    df = df[
        (df["capacite_kg"] > 0)
        & (df["capacite_m3"] > 0)
    ].copy()
    return finaliser(df, "vehicules")


def transformer_entrepots(df):
    df = nettoyer_texte(df)
    df = convertir_entiers(df, ["entrepot_id"])
    df = convertir_numeriques(
        df,
        [
            "capacite_m3",
            "volume_stocke_m3",
            "taux_occupation_pct",
        ],
    )
    df = convertir_dates(df, ["ingested_at"])
    df = df[df["pays"].isin(PAYS)].copy()
    df = df[
        (df["capacite_m3"] > 0)
        & (df["volume_stocke_m3"] >= 0)
        & (df["volume_stocke_m3"] <= df["capacite_m3"])
    ].copy()
    df["taux_occupation_pct"] = (
        df["volume_stocke_m3"]
        / df["capacite_m3"]
        * 100
    ).round(2)
    return finaliser(df, "entrepots")


def transformer_expeditions(df):
    df = nettoyer_texte(df)
    df = convertir_entiers(
        df,
        [
            "expedition_id",
            "chauffeur_id",
            "vehicule_id",
            "entrepot_origine_id",
            "entrepot_destination_id",
        ],
    )
    df = convertir_numeriques(
        df,
        [
            "poids_kg",
            "volume_m3",
            "distance_km",
            "cout_transport_xof",
        ],
    )
    df = convertir_dates(
        df,
        [
            "date_expedition",
            "date_livraison_prevue",
            "ingested_at",
        ],
    )
    df = df[
        df["pays_origine"].isin(PAYS)
        & df["pays_destination"].isin(PAYS)
    ].copy()
    df = df[
        (df["poids_kg"] > 0)
        & (df["volume_m3"] > 0)
        & (df["distance_km"] > 0)
        & (df["cout_transport_xof"] > 0)
    ].copy()
    df = df[
        df["date_livraison_prevue"]
        > df["date_expedition"]
    ].copy()
    df["annee"] = (
        df["date_expedition"].dt.year.astype("Int64")
    )
    df["mois"] = (
        df["date_expedition"].dt.month.astype("Int64")
    )
    return finaliser(df, "expeditions")


def transformer_livraisons(df):
    df = nettoyer_texte(df)
    df = convertir_entiers(
        df,
        [
            "livraison_id",
            "expedition_id",
            "chauffeur_id",
            "vehicule_id",
        ],
    )
    df = convertir_dates(
        df,
        [
            "date_livraison_prevue",
            "date_livraison_reelle",
            "ingested_at",
        ],
    )
    df = df[df["pays_destination"].isin(PAYS)].copy()
    df["delai_heures"] = (
        (
            df["date_livraison_reelle"]
            - df["date_livraison_prevue"]
        ).dt.total_seconds()
        / 3600
    ).round(2)
    df["est_livree"] = df["statut_livraison"].isin(
        ["Livrée à temps", "Livrée en retard"]
    )
    df["est_a_temps"] = (
        df["statut_livraison"] == "Livrée à temps"
    )
    return finaliser(df, "livraisons")


TRANSFORMERS = {
    "chauffeurs": transformer_chauffeurs,
    "vehicules": transformer_vehicules,
    "entrepots": transformer_entrepots,
    "expeditions": transformer_expeditions,
    "livraisons": transformer_livraisons,
}


# ÉCRITURE SILVER

def transformer_fichier(nom):
    source = BRONZE_DIR / FILES[nom]
    destination = SILVER_DIR / f"{nom}_clean.csv.gz"

    if not source.exists():
        raise FileNotFoundError(
            f"Fichier Bronze introuvable : {source}"
        )

    if destination.exists():
        destination.unlink()

    total_lu = 0
    total_ecrit = 0
    premiere_ecriture = True

    lecteur = pd.read_json(
        source,
        lines=True,
        chunksize=CHUNK_SIZE,
    )

    for numero_chunk, chunk in enumerate(lecteur, start=1):
        total_lu += len(chunk)

        silver = TRANSFORMERS[nom](chunk)
        total_ecrit += len(silver)

        if silver.empty:
            logger.warning(
                "%s | lot %d vide après nettoyage",
                nom,
                numero_chunk,
            )
            continue

        silver.to_csv(
            destination,
            mode="wt" if premiere_ecriture else "at",
            header=premiere_ecriture,
            index=False,
            encoding="utf-8",
            compression="gzip",
            date_format="%Y-%m-%dT%H:%M:%S.%f",
        )

        premiere_ecriture = False

        logger.info(
            "%s | lot %d | lu=%,d | écrit=%,d",
            nom,
            numero_chunk,
            total_lu,
            total_ecrit,
        )

    if premiere_ecriture:
        raise ValueError(
            f"Aucune donnée Silver produite pour {nom}"
        )

    logger.info(
        "%s terminé | Bronze=%,d | Silver=%,d",
        nom,
        total_lu,
        total_ecrit,
    )

    return total_lu, total_ecrit


# VALIDATION

def valider_silver(resultats):
    erreurs = []

    for nom, (nombre_bronze, nombre_silver) in resultats.items():
        fichier = SILVER_DIR / f"{nom}_clean.csv.gz"

        if not fichier.exists():
            erreurs.append(
                f"Fichier Silver absent : {fichier.name}"
            )
            continue

        nombre_fichier = compter_lignes_csv_gzip(fichier)

        if nombre_fichier != nombre_silver:
            erreurs.append(
                f"{nom}: fichier={nombre_fichier:,}, "
                f"attendu={nombre_silver:,}"
            )

        if nombre_silver > nombre_bronze:
            erreurs.append(
                f"{nom}: Silver supérieur à Bronze"
            )

        logger.info(
            "%s | Bronze=%,d | Silver=%,d | fichier=%,d",
            nom,
            nombre_bronze,
            nombre_silver,
            nombre_fichier,
        )

    if erreurs:
        raise ValueError(
            "Validation Silver échouée : "
            + " | ".join(erreurs)
        )

    logger.info("VALIDATION SILVER : OK")


# MAIN

def main():
    logger.info("TRANSFORMATION BRONZE VERS SILVER")

    resultats = {}

    for nom in FILES:
        resultats[nom] = transformer_fichier(nom)

    valider_silver(resultats)
    logger.info(
        "TRANSFORMATION SILVER TERMINÉE AVEC SUCCÈS"
    )


if __name__ == "__main__":
    main()
