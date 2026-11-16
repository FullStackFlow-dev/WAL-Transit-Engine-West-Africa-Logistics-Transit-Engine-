import json
from datetime import datetime
from pathlib import Path

import pytest


# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"

EXPECTED = {
    "chauffeurs.json": (10_000, "chauffeur_id"),
    "vehicules.json": (8_000, "vehicule_id"),
    "entrepots.json": (200, "entrepot_id"),
    "expeditions.json": (1_000_000, "expedition_id"),
    "livraisons.json": (1_000_000, "livraison_id"),
}

PAYS = {
    "Sénégal", "Côte d'Ivoire", "Mali", "Guinée", "Burkina Faso",
    "Bénin", "Togo", "Mauritanie", "Ghana", "Gambie",
}


# OUTILS

def iter_jsonl(path):
    with path.open("r", encoding="utf-8") as fichier:
        for numero, ligne in enumerate(fichier, 1):
            if ligne.strip():
                yield numero, json.loads(ligne)


def load_map(filename, key, fields):
    return {
        row[key]: {field: row[field] for field in fields}
        for _, row in iter_jsonl(BRONZE_DIR / filename)
    }


# FICHIERS ET VOLUMÉTRIE

@pytest.mark.parametrize("filename,config", EXPECTED.items())
def test_fichiers_volumes_et_cles(filename, config):
    attendu, cle = config
    path = BRONZE_DIR / filename
    assert path.is_file(), f"Fichier absent : {filename}"

    ids = set()
    total = 0
    for numero, row in iter_jsonl(path):
        total += 1
        assert cle in row, f"{filename} ligne {numero}: {cle} absent"
        assert row[cle] is not None
        assert row[cle] not in ids, f"{filename}: doublon {cle}={row[cle]}"
        ids.add(row[cle])

    assert total == attendu, f"{filename}: {total:,} au lieu de {attendu:,}"


# INTÉGRITÉ RÉFÉRENTIELLE

def test_integrite_referentielle():
    chauffeurs = load_map("chauffeurs.json", "chauffeur_id", ["pays", "ville"])
    vehicules = load_map(
        "vehicules.json", "vehicule_id", ["chauffeur_id", "pays", "ville", "capacite_kg", "capacite_m3"]
    )
    entrepots = load_map("entrepots.json", "entrepot_id", ["pays", "ville"])

    for _, vehicule in iter_jsonl(BRONZE_DIR / "vehicules.json"):
        assert vehicule["chauffeur_id"] in chauffeurs
        chauffeur = chauffeurs[vehicule["chauffeur_id"]]
        assert vehicule["pays"] == chauffeur["pays"]
        assert vehicule["ville"] == chauffeur["ville"]

    for _, expedition in iter_jsonl(BRONZE_DIR / "expeditions.json"):
        assert expedition["chauffeur_id"] in chauffeurs
        assert expedition["vehicule_id"] in vehicules
        assert expedition["entrepot_origine_id"] in entrepots
        assert expedition["entrepot_destination_id"] in entrepots

        vehicule = vehicules[expedition["vehicule_id"]]
        assert vehicule["chauffeur_id"] == expedition["chauffeur_id"]
        assert expedition["poids_kg"] <= vehicule["capacite_kg"]
        assert expedition["volume_m3"] <= vehicule["capacite_m3"]

        origine = entrepots[expedition["entrepot_origine_id"]]
        destination = entrepots[expedition["entrepot_destination_id"]]
        assert expedition["pays_origine"] == origine["pays"]
        assert expedition["ville_origine"] == origine["ville"]
        assert expedition["pays_destination"] == destination["pays"]
        assert expedition["ville_destination"] == destination["ville"]


# RÈGLES MÉTIER

def test_regles_metier_expeditions_livraisons():
    expeditions = load_map(
        "expeditions.json",
        "expedition_id",
        [
            "chauffeur_id", "vehicule_id", "pays_destination", "ville_destination",
            "date_expedition", "date_livraison_prevue", "statut_expedition",
        ],
    )

    for _, livraison in iter_jsonl(BRONZE_DIR / "livraisons.json"):
        assert livraison["expedition_id"] in expeditions
        expedition = expeditions[livraison["expedition_id"]]
        assert livraison["chauffeur_id"] == expedition["chauffeur_id"]
        assert livraison["vehicule_id"] == expedition["vehicule_id"]
        assert livraison["pays_destination"] == expedition["pays_destination"]
        assert livraison["ville_destination"] == expedition["ville_destination"]

        date_exp = datetime.fromisoformat(expedition["date_expedition"])
        date_prevue = datetime.fromisoformat(expedition["date_livraison_prevue"])
        assert date_prevue > date_exp

        if livraison["date_livraison_reelle"]:
            date_reelle = datetime.fromisoformat(livraison["date_livraison_reelle"])
            assert date_reelle > date_exp

        if livraison["statut_livraison"] == "Livrée à temps":
            assert livraison["date_livraison_reelle"] is not None
            assert datetime.fromisoformat(livraison["date_livraison_reelle"]) <= date_prevue

        if livraison["statut_livraison"] == "Livrée en retard":
            assert livraison["date_livraison_reelle"] is not None
            assert datetime.fromisoformat(livraison["date_livraison_reelle"]) > date_prevue

        if livraison["statut_livraison"] in {"Échouée", "En cours"}:
            assert livraison["date_livraison_reelle"] is None


# DOMAINES

def test_pays_et_entrepots():
    for _, chauffeur in iter_jsonl(BRONZE_DIR / "chauffeurs.json"):
        assert chauffeur["pays"] in PAYS

    for _, entrepot in iter_jsonl(BRONZE_DIR / "entrepots.json"):
        assert entrepot["pays"] in PAYS
        assert entrepot["capacite_m3"] > 0
        assert 0 <= entrepot["volume_stocke_m3"] <= entrepot["capacite_m3"]
        assert 0 <= entrepot["taux_occupation_pct"] <= 100
