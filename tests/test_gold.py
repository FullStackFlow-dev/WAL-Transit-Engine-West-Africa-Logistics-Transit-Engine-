from pathlib import Path

import pandas as pd
import pytest


# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent
SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"
CHUNK_SIZE = 100_000

EXPECTED_GOLD = {
    "dim_date": "dim_date.csv.gz",
    "dim_pays": "dim_pays.csv.gz",
    "dim_chauffeur": "dim_chauffeur.csv.gz",
    "dim_vehicule": "dim_vehicule.csv.gz",
    "dim_entrepot": "dim_entrepot.csv.gz",
    "fact_expedition": "fact_expedition.csv.gz",
    "fact_livraison": "fact_livraison.csv.gz",
    "kpi_global": "kpi_global.csv.gz",
    "kpi_pays": "kpi_pays.csv.gz",
    "kpi_chauffeurs": "kpi_chauffeurs.csv.gz",
    "kpi_entrepots": "kpi_entrepots.csv.gz",
    "kpi_mensuel": "kpi_mensuel.csv.gz",
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


# OUTILS

def gold_path(nom):
    return GOLD_DIR / EXPECTED_GOLD[nom]


def silver_path(nom):
    return SILVER_DIR / f"{nom}_clean.csv.gz"


def lire_gold(nom, **kwargs):
    return pd.read_csv(
        gold_path(nom),
        compression="gzip",
        **kwargs,
    )


def lire_silver(nom, **kwargs):
    return pd.read_csv(
        silver_path(nom),
        compression="gzip",
        **kwargs,
    )


def compter_csv(chemin):
    total = 0
    for chunk in pd.read_csv(
        chemin,
        compression="gzip",
        usecols=[0],
        chunksize=CHUNK_SIZE,
    ):
        total += len(chunk)
    return total


def lire_ids_gold(nom, colonne):
    valeurs = set()
    for chunk in pd.read_csv(
        gold_path(nom),
        compression="gzip",
        usecols=[colonne],
        chunksize=CHUNK_SIZE,
    ):
        valeurs.update(chunk[colonne].dropna().astype("int64").tolist())
    return valeurs


# PRÉSENCE DES FICHIERS

@pytest.mark.parametrize("nom,fichier", EXPECTED_GOLD.items())
def test_fichiers_gold_existent(nom, fichier):
    chemin = GOLD_DIR / fichier
    assert chemin.is_file(), f"Fichier Gold absent : {fichier}"
    assert chemin.stat().st_size > 0


# DIMENSIONS

def test_dim_pays():
    df = lire_gold("dim_pays")

    assert len(df) == 10
    assert df["pays_id"].is_unique
    assert df["pays"].is_unique
    assert set(df["pays"]) == PAYS
    assert (df["region"] == "Afrique de l'Ouest").all()


def test_dimensions_metier():
    dim_chauffeur = lire_gold("dim_chauffeur")
    dim_vehicule = lire_gold("dim_vehicule")
    dim_entrepot = lire_gold("dim_entrepot")

    silver_chauffeurs = compter_csv(silver_path("chauffeurs"))
    silver_vehicules = compter_csv(silver_path("vehicules"))
    silver_entrepots = compter_csv(silver_path("entrepots"))

    assert len(dim_chauffeur) == silver_chauffeurs
    assert len(dim_vehicule) == silver_vehicules
    assert len(dim_entrepot) == silver_entrepots

    assert dim_chauffeur["chauffeur_id"].is_unique
    assert dim_vehicule["vehicule_id"].is_unique
    assert dim_entrepot["entrepot_id"].is_unique

    assert dim_chauffeur["pays"].isin(PAYS).all()
    assert dim_vehicule["pays"].isin(PAYS).all()
    assert dim_entrepot["pays"].isin(PAYS).all()

    assert (dim_vehicule["capacite_kg"] > 0).all()
    assert (dim_vehicule["capacite_m3"] > 0).all()
    assert dim_entrepot["taux_occupation_pct"].between(0, 100).all()


def test_dim_date():
    df = lire_gold("dim_date", parse_dates=["date"])

    assert len(df) > 0
    assert df["date_id"].is_unique
    assert df["date"].is_unique
    assert (df["date_id"] == df["date"].dt.strftime("%Y%m%d").astype("int64")).all()
    assert (df["jour"] == df["date"].dt.day).all()
    assert (df["mois"] == df["date"].dt.month).all()
    assert (df["trimestre"] == df["date"].dt.quarter).all()
    assert (df["annee"] == df["date"].dt.year).all()
    assert df["jour_semaine"].between(1, 7).all()


# TABLES DE FAITS

def test_fact_expedition_volume_et_references():
    assert compter_csv(gold_path("fact_expedition")) == compter_csv(
        silver_path("expeditions")
    )

    chauffeur_ids = lire_ids_gold("dim_chauffeur", "chauffeur_id")
    vehicule_ids = lire_ids_gold("dim_vehicule", "vehicule_id")
    entrepot_ids = lire_ids_gold("dim_entrepot", "entrepot_id")
    date_ids = lire_ids_gold("dim_date", "date_id")

    colonnes = [
        "expedition_id",
        "chauffeur_id",
        "vehicule_id",
        "entrepot_origine_id",
        "entrepot_destination_id",
        "date_expedition_id",
        "date_livraison_prevue_id",
        "poids_kg",
        "volume_m3",
        "distance_km",
        "cout_transport_xof",
    ]

    for chunk in pd.read_csv(
        gold_path("fact_expedition"),
        compression="gzip",
        usecols=colonnes,
        chunksize=CHUNK_SIZE,
    ):
        assert chunk["chauffeur_id"].isin(chauffeur_ids).all()
        assert chunk["vehicule_id"].isin(vehicule_ids).all()
        assert chunk["entrepot_origine_id"].isin(entrepot_ids).all()
        assert chunk["entrepot_destination_id"].isin(entrepot_ids).all()
        assert chunk["date_expedition_id"].isin(date_ids).all()
        assert chunk["date_livraison_prevue_id"].isin(date_ids).all()
        assert (chunk["poids_kg"] > 0).all()
        assert (chunk["volume_m3"] > 0).all()
        assert (chunk["distance_km"] > 0).all()
        assert (chunk["cout_transport_xof"] > 0).all()


def test_fact_livraison_volume_et_references():
    assert compter_csv(gold_path("fact_livraison")) == compter_csv(
        silver_path("livraisons")
    )

    expedition_ids = lire_ids_gold("fact_expedition", "expedition_id")
    chauffeur_ids = lire_ids_gold("dim_chauffeur", "chauffeur_id")
    vehicule_ids = lire_ids_gold("dim_vehicule", "vehicule_id")
    date_ids = lire_ids_gold("dim_date", "date_id")

    colonnes = [
        "livraison_id",
        "expedition_id",
        "chauffeur_id",
        "vehicule_id",
        "date_livraison_prevue_id",
        "date_livraison_reelle_id",
        "statut_livraison",
        "est_livree",
        "est_a_temps",
    ]

    for chunk in pd.read_csv(
        gold_path("fact_livraison"),
        compression="gzip",
        usecols=colonnes,
        chunksize=CHUNK_SIZE,
    ):
        assert chunk["expedition_id"].isin(expedition_ids).all()
        assert chunk["chauffeur_id"].isin(chauffeur_ids).all()
        assert chunk["vehicule_id"].isin(vehicule_ids).all()
        assert chunk["date_livraison_prevue_id"].isin(date_ids).all()

        reelles = pd.to_numeric(
            chunk["date_livraison_reelle_id"],
            errors="coerce",
        )
        assert reelles.dropna().astype("int64").isin(date_ids).all()

        a_temps = chunk["statut_livraison"] == "Livrée à temps"
        echouees = chunk["statut_livraison"] == "Échouée"

        assert (chunk.loc[a_temps, "est_a_temps"].astype(str).str.lower() == "true").all()
        assert (chunk.loc[echouees, "est_livree"].astype(str).str.lower() == "false").all()


# KPI GLOBAUX

def test_kpi_global_coherent_avec_silver():
    kpi = lire_gold("kpi_global").iloc[0]

    total_expeditions = 0
    poids_total = 0.0
    volume_total = 0.0
    distance_totale = 0.0
    cout_total = 0.0

    for chunk in pd.read_csv(
        silver_path("expeditions"),
        compression="gzip",
        usecols=[
            "expedition_id",
            "poids_kg",
            "volume_m3",
            "distance_km",
            "cout_transport_xof",
        ],
        chunksize=CHUNK_SIZE,
    ):
        total_expeditions += len(chunk)
        poids_total += chunk["poids_kg"].sum()
        volume_total += chunk["volume_m3"].sum()
        distance_totale += chunk["distance_km"].sum()
        cout_total += chunk["cout_transport_xof"].sum()

    total_livraisons = 0
    a_temps = 0
    echouees = 0

    for chunk in pd.read_csv(
        silver_path("livraisons"),
        compression="gzip",
        usecols=["livraison_id", "statut_livraison", "est_a_temps"],
        chunksize=CHUNK_SIZE,
    ):
        total_livraisons += len(chunk)
        a_temps += (chunk["statut_livraison"] == "Livrée à temps").sum()
        echouees += (chunk["statut_livraison"] == "Échouée").sum()

    assert kpi["nombre_expeditions"] == total_expeditions
    assert kpi["nombre_livraisons"] == total_livraisons
    assert kpi["poids_total_expedie_kg"] == pytest.approx(poids_total, abs=0.1)
    assert kpi["volume_total_expedie_m3"] == pytest.approx(volume_total, abs=0.1)
    assert kpi["distance_totale_km"] == pytest.approx(distance_totale, abs=0.1)
    assert kpi["cout_transport_total_xof"] == pytest.approx(cout_total, abs=1.0)
    assert kpi["taux_livraison_temps_pct"] == pytest.approx(
        a_temps / total_livraisons * 100,
        abs=0.01,
    )
    assert kpi["taux_echec_livraison_pct"] == pytest.approx(
        echouees / total_livraisons * 100,
        abs=0.01,
    )
    assert 0 <= kpi["taux_utilisation_vehicules_pct"] <= 100
    assert 0 <= kpi["taux_occupation_entrepots_moyen_pct"] <= 100


# KPI PAYS

def test_kpi_pays():
    df = lire_gold("kpi_pays")

    assert set(df["pays_destination"]) == PAYS
    assert df["pays_destination"].is_unique
    assert (df["nombre_expeditions"] > 0).all()
    assert (df["nombre_livraisons"] > 0).all()
    assert df["taux_livraison_temps_pct"].between(0, 100).all()
    assert df["taux_echec_pct"].between(0, 100).all()
    assert df["nombre_expeditions"].sum() == compter_csv(silver_path("expeditions"))
    assert df["nombre_livraisons"].sum() == compter_csv(silver_path("livraisons"))


# KPI CHAUFFEURS

def test_kpi_chauffeurs():
    df = lire_gold("kpi_chauffeurs")
    chauffeur_ids = lire_ids_gold("dim_chauffeur", "chauffeur_id")

    assert df["chauffeur_id"].is_unique
    assert df["chauffeur_id"].isin(chauffeur_ids).all()
    assert (df["nombre_livraisons"] > 0).all()
    assert (df["livraisons_a_temps"] >= 0).all()
    assert (df["livraisons_echouees"] >= 0).all()
    assert df["taux_a_temps_pct"].between(0, 100).all()
    assert df["nombre_livraisons"].sum() == compter_csv(silver_path("livraisons"))


# KPI ENTREPÔTS

def test_kpi_entrepots():
    df = lire_gold("kpi_entrepots")

    assert len(df) == compter_csv(silver_path("entrepots"))
    assert df["entrepot_id"].is_unique
    assert df["pays"].isin(PAYS).all()
    assert (df["capacite_m3"] > 0).all()
    assert (df["volume_stocke_m3"] >= 0).all()
    assert df["taux_occupation_pct"].between(0, 100).all()


# KPI MENSUELS

def test_kpi_mensuel():
    df = lire_gold("kpi_mensuel")

    assert len(df) > 0
    assert df[["annee", "mois"]].duplicated().sum() == 0
    assert df["mois"].between(1, 12).all()
    assert (df["nombre_expeditions"] > 0).all()
    assert (df["poids_total_kg"] > 0).all()
    assert (df["volume_total_m3"] > 0).all()
    assert (df["cout_transport_total_xof"] > 0).all()
    assert df["nombre_expeditions"].sum() == compter_csv(silver_path("expeditions"))
