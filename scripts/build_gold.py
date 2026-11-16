import logging
from pathlib import Path

import pandas as pd


# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"
LOG_DIR = BASE_DIR / "logs"

GOLD_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 100_000


# LOGGING

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "build_gold.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# OUTILS

def lire_silver(nom, usecols=None, parse_dates=None):
    return pd.read_csv(
        SILVER_DIR / f"{nom}_clean.csv.gz",
        compression="gzip",
        usecols=usecols,
        parse_dates=parse_dates,
    )


def ecrire_gold(df, nom):
    chemin = GOLD_DIR / f"{nom}.csv.gz"
    df.to_csv(
        chemin,
        index=False,
        encoding="utf-8",
        compression="gzip",
        date_format="%Y-%m-%dT%H:%M:%S",
    )
    logger.info("%s créé | %,d lignes", chemin.name, len(df))


# DIMENSIONS

def construire_dimensions():
    chauffeurs = lire_silver("chauffeurs")
    vehicules = lire_silver("vehicules")
    entrepots = lire_silver("entrepots")

    dim_chauffeur = chauffeurs[[
        "chauffeur_id", "nom", "pays", "ville", "date_integration", "statut"
    ]].copy()
    ecrire_gold(dim_chauffeur, "dim_chauffeur")

    dim_vehicule = vehicules[[
        "vehicule_id", "chauffeur_id", "pays", "ville", "type_vehicule",
        "marque", "annee", "capacite_kg", "capacite_m3", "statut"
    ]].copy()
    ecrire_gold(dim_vehicule, "dim_vehicule")

    dim_entrepot = entrepots[[
        "entrepot_id", "nom_entrepot", "pays", "ville", "capacite_m3",
        "volume_stocke_m3", "taux_occupation_pct", "statut"
    ]].copy()
    ecrire_gold(dim_entrepot, "dim_entrepot")

    expeditions_dates = lire_silver(
        "expeditions",
        usecols=["date_expedition", "date_livraison_prevue"],
        parse_dates=["date_expedition", "date_livraison_prevue"],
    )
    livraisons_dates = lire_silver(
        "livraisons",
        usecols=["date_livraison_reelle"],
        parse_dates=["date_livraison_reelle"],
    )

    dates = pd.concat([
        expeditions_dates["date_expedition"],
        expeditions_dates["date_livraison_prevue"],
        livraisons_dates["date_livraison_reelle"],
    ]).dropna().dt.normalize().drop_duplicates().sort_values()

    dim_date = pd.DataFrame({"date": dates})
    dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d").astype("int64")
    dim_date["jour"] = dim_date["date"].dt.day
    dim_date["mois"] = dim_date["date"].dt.month
    dim_date["trimestre"] = dim_date["date"].dt.quarter
    dim_date["annee"] = dim_date["date"].dt.year
    dim_date["jour_semaine"] = dim_date["date"].dt.dayofweek + 1
    dim_date = dim_date[[
        "date_id", "date", "jour", "mois", "trimestre", "annee", "jour_semaine"
    ]]
    ecrire_gold(dim_date, "dim_date")

    pays = sorted(set(chauffeurs["pays"]) | set(entrepots["pays"]))
    dim_pays = pd.DataFrame({
        "pays_id": range(1, len(pays) + 1),
        "pays": pays,
        "region": "Afrique de l'Ouest",
    })
    ecrire_gold(dim_pays, "dim_pays")


# FAITS

def construire_faits():
    expeditions = lire_silver(
        "expeditions",
        parse_dates=["date_expedition", "date_livraison_prevue"],
    )
    livraisons = lire_silver(
        "livraisons",
        parse_dates=["date_livraison_prevue", "date_livraison_reelle"],
    )

    fact_expedition = expeditions.copy()
    fact_expedition["date_expedition_id"] = (
        fact_expedition["date_expedition"].dt.strftime("%Y%m%d").astype("int64")
    )
    fact_expedition["date_livraison_prevue_id"] = (
        fact_expedition["date_livraison_prevue"].dt.strftime("%Y%m%d").astype("int64")
    )
    ecrire_gold(fact_expedition, "fact_expedition")

    fact_livraison = livraisons.copy()
    fact_livraison["date_livraison_prevue_id"] = (
        fact_livraison["date_livraison_prevue"].dt.strftime("%Y%m%d").astype("int64")
    )
    fact_livraison["date_livraison_reelle_id"] = (
        fact_livraison["date_livraison_reelle"].dt.strftime("%Y%m%d")
    )
    ecrire_gold(fact_livraison, "fact_livraison")


# KPI

def construire_kpi():
    expeditions = lire_silver(
        "expeditions",
        usecols=[
            "expedition_id", "chauffeur_id", "vehicule_id", "pays_origine",
            "pays_destination", "poids_kg", "volume_m3", "distance_km",
            "cout_transport_xof", "date_expedition"
        ],
        parse_dates=["date_expedition"],
    )
    livraisons = lire_silver(
        "livraisons",
        usecols=[
            "livraison_id", "expedition_id", "chauffeur_id", "vehicule_id",
            "pays_destination", "statut_livraison", "delai_heures",
            "est_livree", "est_a_temps"
        ],
    )
    vehicules = lire_silver("vehicules")
    entrepots = lire_silver("entrepots")

    kpi_global = pd.DataFrame([{
        "nombre_expeditions": len(expeditions),
        "nombre_livraisons": len(livraisons),
        "poids_total_expedie_kg": round(expeditions["poids_kg"].sum(), 2),
        "volume_total_expedie_m3": round(expeditions["volume_m3"].sum(), 2),
        "distance_totale_km": round(expeditions["distance_km"].sum(), 2),
        "cout_transport_total_xof": round(expeditions["cout_transport_xof"].sum(), 2),
        "taux_livraison_temps_pct": round(livraisons["est_a_temps"].mean() * 100, 2),
        "taux_echec_livraison_pct": round((livraisons["statut_livraison"] == "Échouée").mean() * 100, 2),
        "vehicules_actifs": int(vehicules["statut"].isin(["Disponible", "En mission"]).sum()),
        "vehicules_total": len(vehicules),
        "taux_utilisation_vehicules_pct": round(vehicules["statut"].isin(["Disponible", "En mission"]).mean() * 100, 2),
        "taux_occupation_entrepots_moyen_pct": round(entrepots["taux_occupation_pct"].mean(), 2),
    }])
    ecrire_gold(kpi_global, "kpi_global")

    kpi_pays = (
        expeditions.groupby("pays_destination", as_index=False)
        .agg(
            nombre_expeditions=("expedition_id", "count"),
            poids_total_kg=("poids_kg", "sum"),
            volume_total_m3=("volume_m3", "sum"),
            distance_totale_km=("distance_km", "sum"),
            cout_transport_total_xof=("cout_transport_xof", "sum"),
        )
        .merge(
            livraisons.groupby("pays_destination", as_index=False).agg(
                nombre_livraisons=("livraison_id", "count"),
                livraisons_a_temps=("est_a_temps", "sum"),
                livraisons_echouees=("statut_livraison", lambda s: (s == "Échouée").sum()),
            ),
            on="pays_destination",
            how="left",
        )
    )
    kpi_pays["taux_livraison_temps_pct"] = (
        kpi_pays["livraisons_a_temps"] / kpi_pays["nombre_livraisons"] * 100
    ).round(2)
    kpi_pays["taux_echec_pct"] = (
        kpi_pays["livraisons_echouees"] / kpi_pays["nombre_livraisons"] * 100
    ).round(2)
    ecrire_gold(kpi_pays, "kpi_pays")

    kpi_chauffeurs = (
        livraisons.groupby("chauffeur_id", as_index=False)
        .agg(
            nombre_livraisons=("livraison_id", "count"),
            livraisons_a_temps=("est_a_temps", "sum"),
            livraisons_echouees=("statut_livraison", lambda s: (s == "Échouée").sum()),
        )
    )
    kpi_chauffeurs["taux_a_temps_pct"] = (
        kpi_chauffeurs["livraisons_a_temps"] / kpi_chauffeurs["nombre_livraisons"] * 100
    ).round(2)
    ecrire_gold(kpi_chauffeurs, "kpi_chauffeurs")

    kpi_entrepots = entrepots[[
        "entrepot_id", "nom_entrepot", "pays", "ville", "capacite_m3",
        "volume_stocke_m3", "taux_occupation_pct"
    ]].copy()
    ecrire_gold(kpi_entrepots, "kpi_entrepots")

    expeditions["annee"] = expeditions["date_expedition"].dt.year
    expeditions["mois"] = expeditions["date_expedition"].dt.month
    kpi_mensuel = (
        expeditions.groupby(["annee", "mois"], as_index=False)
        .agg(
            nombre_expeditions=("expedition_id", "count"),
            poids_total_kg=("poids_kg", "sum"),
            volume_total_m3=("volume_m3", "sum"),
            cout_transport_total_xof=("cout_transport_xof", "sum"),
        )
    )
    ecrire_gold(kpi_mensuel, "kpi_mensuel")


# VALIDATION

def valider_gold():
    fichiers = [
        "dim_date", "dim_pays", "dim_chauffeur", "dim_vehicule", "dim_entrepot",
        "fact_expedition", "fact_livraison", "kpi_global", "kpi_pays",
        "kpi_chauffeurs", "kpi_entrepots", "kpi_mensuel",
    ]

    manquants = [
        f"{nom}.csv.gz"
        for nom in fichiers
        if not (GOLD_DIR / f"{nom}.csv.gz").exists()
    ]

    if manquants:
        raise FileNotFoundError("Fichiers Gold manquants : " + ", ".join(manquants))

    logger.info("VALIDATION GOLD : OK")


# MAIN

def main():
    logger.info("CONSTRUCTION GOLD - MIRAH-BI WEST AFRICA LOGISTICS")
    construire_dimensions()
    construire_faits()
    construire_kpi()
    valider_gold()
    logger.info("CONSTRUCTION GOLD TERMINÉE AVEC SUCCÈS")


if __name__ == "__main__":
    main()
