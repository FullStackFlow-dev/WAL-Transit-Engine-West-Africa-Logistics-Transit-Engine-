import gzip
from pathlib import Path

import pandas as pd
import pytest


# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent
SILVER_DIR = BASE_DIR / "data" / "silver"

EXPECTED = {
    "chauffeurs": ("chauffeurs_clean.csv.gz", 10_000, "chauffeur_id"),
    "vehicules": ("vehicules_clean.csv.gz", 8_000, "vehicule_id"),
    "entrepots": ("entrepots_clean.csv.gz", 200, "entrepot_id"),
    "expeditions": ("expeditions_clean.csv.gz", 1_000_000, "expedition_id"),
    "livraisons": ("livraisons_clean.csv.gz", 1_000_000, "livraison_id"),
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

CHUNK_SIZE = 100_000


# OUTILS

def chemin_silver(nom):
    return SILVER_DIR / EXPECTED[nom][0]


def compter_lignes(chemin):
    with gzip.open(chemin, "rt", encoding="utf-8") as fichier:
        total = sum(1 for ligne in fichier if ligne.strip())
    return max(total - 1, 0)


def lire_ids(nom, colonne):
    ids = set()
    for chunk in pd.read_csv(
        chemin_silver(nom),
        compression="gzip",
        usecols=[colonne],
        chunksize=CHUNK_SIZE,
    ):
        ids.update(chunk[colonne].dropna().astype("int64").tolist())
    return ids


# FICHIERS

@pytest.mark.parametrize("nom,config", EXPECTED.items())
def test_fichiers_volumes_et_cles(nom, config):
    fichier, attendu, cle = config
    chemin = SILVER_DIR / fichier

    assert chemin.is_file(), f"Fichier Silver absent : {fichier}"
    assert compter_lignes(chemin) == attendu

    ids = set()
    total = 0

    for chunk in pd.read_csv(
        chemin,
        compression="gzip",
        usecols=[cle],
        chunksize=CHUNK_SIZE,
    ):
        assert chunk[cle].notna().all()
        assert not chunk[cle].duplicated().any()

        valeurs = set(chunk[cle].astype("int64").tolist())
        assert ids.isdisjoint(valeurs)
        ids.update(valeurs)
        total += len(chunk)

    assert total == attendu


# CHAUFFEURS

def test_chauffeurs_silver():
    colonnes = [
        "chauffeur_id",
        "nom",
        "pays",
        "ville",
        "date_integration",
        "silver_processed_at",
    ]

    for chunk in pd.read_csv(
        chemin_silver("chauffeurs"),
        compression="gzip",
        usecols=colonnes,
        chunksize=CHUNK_SIZE,
        parse_dates=["date_integration", "silver_processed_at"],
    ):
        assert chunk["nom"].notna().all()
        assert chunk["ville"].notna().all()
        assert chunk["pays"].isin(PAYS).all()
        assert chunk["date_integration"].notna().all()
        assert chunk["silver_processed_at"].notna().all()


# VÉHICULES

def test_vehicules_silver():
    chauffeur_ids = lire_ids("chauffeurs", "chauffeur_id")

    colonnes = [
        "vehicule_id",
        "chauffeur_id",
        "pays",
        "capacite_kg",
        "capacite_m3",
    ]

    for chunk in pd.read_csv(
        chemin_silver("vehicules"),
        compression="gzip",
        usecols=colonnes,
        chunksize=CHUNK_SIZE,
    ):
        assert chunk["chauffeur_id"].isin(chauffeur_ids).all()
        assert chunk["pays"].isin(PAYS).all()
        assert (chunk["capacite_kg"] > 0).all()
        assert (chunk["capacite_m3"] > 0).all()


# ENTREPÔTS

def test_entrepots_silver():
    colonnes = [
        "entrepot_id",
        "pays",
        "capacite_m3",
        "volume_stocke_m3",
        "taux_occupation_pct",
    ]

    df = pd.read_csv(
        chemin_silver("entrepots"),
        compression="gzip",
        usecols=colonnes,
    )

    assert df["pays"].isin(PAYS).all()
    assert (df["capacite_m3"] > 0).all()
    assert (df["volume_stocke_m3"] >= 0).all()
    assert (df["volume_stocke_m3"] <= df["capacite_m3"]).all()
    assert df["taux_occupation_pct"].between(0, 100).all()

    taux_attendu = (
        df["volume_stocke_m3"] / df["capacite_m3"] * 100
    ).round(2)

    assert (df["taux_occupation_pct"].round(2) == taux_attendu).all()


# EXPÉDITIONS

def test_expeditions_silver():
    chauffeur_ids = lire_ids("chauffeurs", "chauffeur_id")
    vehicule_ids = lire_ids("vehicules", "vehicule_id")
    entrepot_ids = lire_ids("entrepots", "entrepot_id")

    colonnes = [
        "expedition_id",
        "chauffeur_id",
        "vehicule_id",
        "entrepot_origine_id",
        "entrepot_destination_id",
        "pays_origine",
        "pays_destination",
        "date_expedition",
        "date_livraison_prevue",
        "poids_kg",
        "volume_m3",
        "distance_km",
        "cout_transport_xof",
        "annee",
        "mois",
    ]

    for chunk in pd.read_csv(
        chemin_silver("expeditions"),
        compression="gzip",
        usecols=colonnes,
        chunksize=CHUNK_SIZE,
        parse_dates=["date_expedition", "date_livraison_prevue"],
    ):
        assert chunk["chauffeur_id"].isin(chauffeur_ids).all()
        assert chunk["vehicule_id"].isin(vehicule_ids).all()
        assert chunk["entrepot_origine_id"].isin(entrepot_ids).all()
        assert chunk["entrepot_destination_id"].isin(entrepot_ids).all()
        assert chunk["pays_origine"].isin(PAYS).all()
        assert chunk["pays_destination"].isin(PAYS).all()
        assert (chunk["poids_kg"] > 0).all()
        assert (chunk["volume_m3"] > 0).all()
        assert (chunk["distance_km"] > 0).all()
        assert (chunk["cout_transport_xof"] > 0).all()
        assert (chunk["date_livraison_prevue"] > chunk["date_expedition"]).all()
        assert (chunk["annee"] == chunk["date_expedition"].dt.year).all()
        assert (chunk["mois"] == chunk["date_expedition"].dt.month).all()


# LIVRAISONS

def test_livraisons_silver():
    expedition_ids = lire_ids("expeditions", "expedition_id")
    chauffeur_ids = lire_ids("chauffeurs", "chauffeur_id")
    vehicule_ids = lire_ids("vehicules", "vehicule_id")

    colonnes = [
        "livraison_id",
        "expedition_id",
        "chauffeur_id",
        "vehicule_id",
        "pays_destination",
        "date_livraison_prevue",
        "date_livraison_reelle",
        "statut_livraison",
        "delai_heures",
        "est_livree",
        "est_a_temps",
    ]

    for chunk in pd.read_csv(
        chemin_silver("livraisons"),
        compression="gzip",
        usecols=colonnes,
        chunksize=CHUNK_SIZE,
        parse_dates=["date_livraison_prevue", "date_livraison_reelle"],
    ):
        assert chunk["expedition_id"].isin(expedition_ids).all()
        assert chunk["chauffeur_id"].isin(chauffeur_ids).all()
        assert chunk["vehicule_id"].isin(vehicule_ids).all()
        assert chunk["pays_destination"].isin(PAYS).all()

        livrees = chunk["statut_livraison"].isin(
            ["Livrée à temps", "Livrée en retard"]
        )
        a_temps = chunk["statut_livraison"] == "Livrée à temps"
        en_retard = chunk["statut_livraison"] == "Livrée en retard"
        non_livrees = chunk["statut_livraison"].isin(
            ["Échouée", "En cours"]
        )

        assert chunk.loc[livrees, "date_livraison_reelle"].notna().all()
        assert chunk.loc[non_livrees, "date_livraison_reelle"].isna().all()
        assert chunk.loc[a_temps, "delai_heures"].le(0).all()
        assert chunk.loc[en_retard, "delai_heures"].gt(0).all()

        est_livree_calcule = livrees
        est_a_temps_calcule = a_temps

        assert (
            chunk["est_livree"].astype(str).str.lower()
            == est_livree_calcule.astype(str).str.lower()
        ).all()
        assert (
            chunk["est_a_temps"].astype(str).str.lower()
            == est_a_temps_calcule.astype(str).str.lower()
        ).all()
