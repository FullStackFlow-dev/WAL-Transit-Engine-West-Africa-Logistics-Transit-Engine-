import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# CONFIGURATION

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "data" / "bronze"
LOG_DIR = BASE_DIR / "logs"

BRONZE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

NB_CHAUFFEURS = 10_000
NB_VEHICULES = 8_000
NB_ENTREPOTS = 200
NB_EXPEDITIONS = 1_000_000
NB_LIVRAISONS = 1_000_000

DATE_DEBUT = datetime(2023, 1, 1)
DATE_FIN = datetime(2026, 10, 19, 23, 59, 59)
BATCH_LOG_SIZE = 50_000


# LOGGING

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "generate_data.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# RÉFÉRENTIELS MÉTIER

PAYS = {
    "Sénégal": {
        "code": "SN",
        "villes": ["Dakar", "Thiès", "Mbour", "Saint-Louis", "Kaolack", "Ziguinchor"],
        "poids": 0.24,
        "langue": "fr",
    },
    "Côte d'Ivoire": {
        "code": "CI",
        "villes": ["Abidjan", "Bouaké", "Yamoussoukro", "San-Pédro", "Korhogo"],
        "poids": 0.18,
        "langue": "fr",
    },
    "Mali": {
        "code": "ML",
        "villes": ["Bamako", "Sikasso", "Ségou", "Kayes", "Mopti"],
        "poids": 0.10,
        "langue": "fr",
    },
    "Guinée": {
        "code": "GN",
        "villes": ["Conakry", "Kankan", "Kindia", "Labé", "Nzérékoré"],
        "poids": 0.09,
        "langue": "fr",
    },
    "Burkina Faso": {
        "code": "BF",
        "villes": ["Ouagadougou", "Bobo-Dioulasso", "Koudougou", "Ouahigouya"],
        "poids": 0.09,
        "langue": "fr",
    },
    "Bénin": {
        "code": "BJ",
        "villes": ["Cotonou", "Porto-Novo", "Parakou", "Abomey-Calavi"],
        "poids": 0.07,
        "langue": "fr",
    },
    "Togo": {
        "code": "TG",
        "villes": ["Lomé", "Sokodé", "Kara", "Atakpamé"],
        "poids": 0.06,
        "langue": "fr",
    },
    "Mauritanie": {
        "code": "MR",
        "villes": ["Nouakchott", "Nouadhibou", "Rosso", "Kaédi"],
        "poids": 0.05,
        "langue": "fr",
    },
    "Ghana": {
        "code": "GH",
        "villes": ["Accra", "Kumasi", "Tema", "Tamale", "Takoradi"],
        "poids": 0.08,
        "langue": "en",
    },
    "Gambie": {
        "code": "GM",
        "villes": ["Banjul", "Serekunda", "Brikama", "Bakau"],
        "poids": 0.04,
        "langue": "en",
    },
}

TYPES_VEHICULE = {
    "Fourgon": {"capacite_kg": (600, 1500), "capacite_m3": (4, 12)},
    "Camion léger": {"capacite_kg": (1500, 5000), "capacite_m3": (12, 30)},
    "Camion porteur": {"capacite_kg": (5000, 15000), "capacite_m3": (30, 60)},
    "Semi-remorque": {"capacite_kg": (15000, 30000), "capacite_m3": (60, 100)},
}

MARQUES = ["Mercedes-Benz", "Renault Trucks", "MAN", "Iveco", "Isuzu", "Toyota", "Mitsubishi", "DAF", "Volvo"]
STATUTS_CHAUFFEUR = ["Actif", "Repos", "Suspendu", "Inactif"]
STATUTS_VEHICULE = ["Disponible", "En mission", "Maintenance", "Inactif"]
STATUTS_EXPEDITION = ["Préparée", "En transit", "Livrée", "Annulée"]
STATUTS_LIVRAISON = ["Livrée à temps", "Livrée en retard", "Échouée", "En cours"]
MOTIFS_ECHEC = ["Destinataire absent", "Adresse incorrecte", "Incident véhicule", "Marchandise refusée", "Accès impossible"]
TYPES_MARCHANDISE = ["Agroalimentaire", "Textile", "Électronique", "Pharmaceutique", "Pièces détachées", "Documents", "Produits ménagers"]


# IDENTITÉS SYNTHÉTIQUES

NOMS_PAR_PAYS = {
    "Sénégal": {
        "prenoms": ["Mamadou", "Ibrahima", "Cheikh", "Abdoulaye", "Amadou", "Moussa", "Ousmane", "Babacar", "Malick", "Fatou", "Ndeye", "Awa", "Khady", "Aminata", "Aïssatou", "Mariama", "Coumba", "Seynabou"],
        "noms": ["Ndiaye", "Diop", "Ba", "Diallo", "Sow", "Diouf", "Gueye", "Fall", "Faye", "Sarr", "Cissé", "Seck", "Niang", "Thiam", "Mbaye", "Dieng"],
    },
    "Côte d'Ivoire": {
        "prenoms": ["Kouassi", "Koffi", "Yao", "Adama", "Moussa", "Ibrahim", "Mamadou", "Awa", "Aminata", "Aya", "Akissi", "Fatou", "Mariam", "Aïcha"],
        "noms": ["Koné", "Kouassi", "Yao", "Ouattara", "Coulibaly", "Traoré", "Fofana", "Bamba", "Koffi", "N'Guessan", "Kouamé", "Touré"],
    },
    "Mali": {
        "prenoms": ["Moussa", "Adama", "Mamadou", "Ibrahim", "Oumar", "Bakary", "Seydou", "Amadou", "Aminata", "Fatoumata", "Aïssata", "Kadiatou", "Mariam", "Oumou"],
        "noms": ["Traoré", "Coulibaly", "Keïta", "Konaté", "Diarra", "Sidibé", "Touré", "Camara", "Dembélé", "Sissoko", "Cissé", "Maïga"],
    },
    "Guinée": {
        "prenoms": ["Mamadou", "Alpha", "Ibrahima", "Moussa", "Ousmane", "Sékou", "Aboubacar", "Fodé", "Aïssatou", "Kadiatou", "Fatoumata", "Mariama", "Hawa", "Aminata"],
        "noms": ["Diallo", "Bah", "Barry", "Camara", "Condé", "Sylla", "Keïta", "Touré", "Soumah", "Cissé", "Kourouma", "Traoré"],
    },
    "Burkina Faso": {
        "prenoms": ["Issa", "Adama", "Moussa", "Ousmane", "Abdoulaye", "Ibrahim", "Souleymane", "Aminata", "Aïssata", "Mariam", "Fatimata", "Safiatou", "Rasmata"],
        "noms": ["Ouédraogo", "Sawadogo", "Traoré", "Kaboré", "Compaoré", "Sanou", "Barry", "Ilboudo", "Zongo", "Yaméogo", "Somé", "Bazié"],
    },
    "Bénin": {
        "prenoms": ["Dossou", "Arnaud", "Boris", "Romuald", "Ibrahim", "Moussa", "Olivier", "Aïcha", "Clarisse", "Nadine", "Grâce", "Mariam", "Aminata"],
        "noms": ["Dossou", "Houénou", "Hountondji", "Adjovi", "Soglo", "Agossou", "Ahouansou", "Kiki", "Adéoti", "Gbaguidi", "Aïssi"],
    },
    "Togo": {
        "prenoms": ["Kodjo", "Kossi", "Komlan", "Koffi", "Yao", "Messan", "Sena", "Afi", "Ama", "Akouvi", "Dédé", "Mawuli", "Elikem"],
        "noms": ["Mensah", "Agbodjan", "Amouzou", "Kpodo", "Tchalla", "Amegavi", "Koffi", "Adjakpa", "Dossou", "Lawson", "Gnofam"],
    },
    "Mauritanie": {
        "prenoms": ["Mohamed", "Ahmed", "Sidi", "Moustapha", "Abdallahi", "Cheikh", "Brahim", "Mariam", "Fatimetou", "Aïcha", "Khadijetou", "Mintou"],
        "noms": ["Ould Ahmed", "Ould Mohamed", "Ould Cheikh", "Ould Sid'Ahmed", "Ould Abdallahi", "Mint Ahmed", "Mint Mohamed", "Ba", "Diallo", "Kane"],
    },
    "Ghana": {
        "prenoms": ["Kwame", "Kofi", "Kwabena", "Yaw", "Kojo", "Kwaku", "Ama", "Akosua", "Abena", "Yaa", "Adwoa", "Afia", "Esi"],
        "noms": ["Mensah", "Owusu", "Boateng", "Asante", "Osei", "Agyeman", "Addo", "Appiah", "Acheampong", "Nkrumah", "Ankrah", "Adjei"],
    },
    "Gambie": {
        "prenoms": ["Lamin", "Ousman", "Modou", "Ebrima", "Mamadou", "Bakary", "Alieu", "Fatou", "Mariama", "Awa", "Isatou", "Binta", "Haddy"],
        "noms": ["Jallow", "Ceesay", "Touray", "Camara", "Darboe", "Sanyang", "Njie", "Bojang", "Sonko", "Bah", "Sanneh", "Jawara"],
    },
}


def generer_nom(pays):
    referentiel = NOMS_PAR_PAYS[pays]
    return f"{random.choice(referentiel['prenoms'])} {random.choice(referentiel['noms'])}"


# OUTILS

def creer_batch_id():
    return str(uuid.uuid4())


def ecrire_json_line(fichier, enregistrement):
    fichier.write(json.dumps(enregistrement, ensure_ascii=False, default=str) + "\n")


def date_aleatoire(debut, fin):
    secondes = int((fin - debut).total_seconds())
    return debut + timedelta(seconds=random.randint(0, secondes))


def choisir_pays():
    noms = list(PAYS)
    poids = [PAYS[nom]["poids"] for nom in noms]
    return random.choices(noms, weights=poids, k=1)[0]


def afficher_progression(nom, index, total):
    if index % BATCH_LOG_SIZE == 0 or index == total:
        logger.info("%s : %,d / %,d", nom, index, total)


# CHAUFFEURS

def generer_chauffeurs():
    chemin = BRONZE_DIR / "chauffeurs.json"
    batch_id = creer_batch_id()
    ingested_at = datetime.now().isoformat()
    chauffeurs = {}
    chauffeurs_par_pays = {pays: [] for pays in PAYS}

    with chemin.open("w", encoding="utf-8") as fichier:
        for chauffeur_id in range(1, NB_CHAUFFEURS + 1):
            pays = choisir_pays()
            ville = random.choice(PAYS[pays]["villes"])
            date_integration = date_aleatoire(DATE_DEBUT, DATE_FIN)

            row = {
                "chauffeur_id": chauffeur_id,
                "nom": generer_nom(pays),
                "pays": pays,
                "ville": ville,
                "date_integration": date_integration.date().isoformat(),
                "statut": random.choices(STATUTS_CHAUFFEUR, weights=[0.88, 0.07, 0.02, 0.03], k=1)[0],
                "source_system": "synthetic_generator",
                "batch_id": batch_id,
                "ingested_at": ingested_at,
            }
            chauffeurs[chauffeur_id] = row
            chauffeurs_par_pays[pays].append(chauffeur_id)
            ecrire_json_line(fichier, row)
            afficher_progression("Chauffeurs", chauffeur_id, NB_CHAUFFEURS)

    return chauffeurs, chauffeurs_par_pays


# VÉHICULES

def generer_vehicules(chauffeurs, chauffeurs_par_pays):
    chemin = BRONZE_DIR / "vehicules.json"
    batch_id = creer_batch_id()
    ingested_at = datetime.now().isoformat()
    vehicules = {}
    vehicules_par_pays = {pays: [] for pays in PAYS}

    chauffeurs_selectionnes = random.sample(list(chauffeurs), NB_VEHICULES)

    with chemin.open("w", encoding="utf-8") as fichier:
        for vehicule_id, chauffeur_id in enumerate(chauffeurs_selectionnes, start=1):
            chauffeur = chauffeurs[chauffeur_id]
            pays = chauffeur["pays"]
            type_vehicule = random.choice(list(TYPES_VEHICULE))
            config = TYPES_VEHICULE[type_vehicule]

            row = {
                "vehicule_id": vehicule_id,
                "chauffeur_id": chauffeur_id,
                "pays": pays,
                "ville": chauffeur["ville"],
                "type_vehicule": type_vehicule,
                "marque": random.choice(MARQUES),
                "annee": random.randint(2014, 2026),
                "capacite_kg": random.randint(*config["capacite_kg"]),
                "capacite_m3": round(random.uniform(*config["capacite_m3"]), 2),
                "statut": random.choices(STATUTS_VEHICULE, weights=[0.68, 0.22, 0.07, 0.03], k=1)[0],
                "source_system": "synthetic_generator",
                "batch_id": batch_id,
                "ingested_at": ingested_at,
            }
            vehicules[vehicule_id] = row
            vehicules_par_pays[pays].append(vehicule_id)
            ecrire_json_line(fichier, row)
            afficher_progression("Véhicules", vehicule_id, NB_VEHICULES)

    return vehicules, vehicules_par_pays


# ENTREPÔTS

def generer_entrepots():
    chemin = BRONZE_DIR / "entrepots.json"
    batch_id = creer_batch_id()
    ingested_at = datetime.now().isoformat()
    entrepots = {}
    entrepots_par_pays = {pays: [] for pays in PAYS}

    repartition = {pays: max(2, round(NB_ENTREPOTS * PAYS[pays]["poids"])) for pays in PAYS}
    difference = NB_ENTREPOTS - sum(repartition.values())
    repartition["Sénégal"] += difference

    entrepot_id = 1
    with chemin.open("w", encoding="utf-8") as fichier:
        for pays, nombre in repartition.items():
            for _ in range(nombre):
                ville = random.choice(PAYS[pays]["villes"])
                capacite_m3 = random.randint(2_000, 40_000)
                volume_stocke_m3 = round(capacite_m3 * random.uniform(0.20, 0.92), 2)

                row = {
                    "entrepot_id": entrepot_id,
                    "nom_entrepot": f"Hub {PAYS[pays]['code']}-{ville}-{entrepot_id:03d}",
                    "pays": pays,
                    "ville": ville,
                    "capacite_m3": capacite_m3,
                    "volume_stocke_m3": volume_stocke_m3,
                    "taux_occupation_pct": round(volume_stocke_m3 / capacite_m3 * 100, 2),
                    "statut": random.choices(["Actif", "Maintenance"], weights=[0.97, 0.03], k=1)[0],
                    "source_system": "synthetic_generator",
                    "batch_id": batch_id,
                    "ingested_at": ingested_at,
                }
                entrepots[entrepot_id] = row
                entrepots_par_pays[pays].append(entrepot_id)
                ecrire_json_line(fichier, row)
                entrepot_id += 1

    logger.info("Entrepôts : %,d", len(entrepots))
    return entrepots, entrepots_par_pays


# EXPÉDITIONS ET LIVRAISONS

def generer_expeditions_livraisons(chauffeurs, vehicules, vehicules_par_pays, entrepots, entrepots_par_pays):
    chemin_exp = BRONZE_DIR / "expeditions.json"
    chemin_liv = BRONZE_DIR / "livraisons.json"
    batch_exp = creer_batch_id()
    batch_liv = creer_batch_id()
    ingested_at = datetime.now().isoformat()

    with (
        chemin_exp.open("w", encoding="utf-8") as fichier_exp,
        chemin_liv.open("w", encoding="utf-8") as fichier_liv,
    ):
        for expedition_id in range(1, NB_EXPEDITIONS + 1):
            pays_origine = choisir_pays()
            pays_destination = random.choices(
                list(PAYS),
                weights=[0.55 if p == pays_origine else PAYS[p]["poids"] for p in PAYS],
                k=1,
            )[0]

            vehicule_id = random.choice(vehicules_par_pays[pays_origine])
            vehicule = vehicules[vehicule_id]
            chauffeur_id = vehicule["chauffeur_id"]
            entrepot_origine_id = random.choice(entrepots_par_pays[pays_origine])
            entrepot_destination_id = random.choice(entrepots_par_pays[pays_destination])
            origine = entrepots[entrepot_origine_id]
            destination = entrepots[entrepot_destination_id]

            date_expedition = date_aleatoire(DATE_DEBUT, DATE_FIN - timedelta(days=10))
            distance_km = round(random.uniform(10, 450) if pays_origine == pays_destination else random.uniform(250, 2200), 2)
            poids_kg = round(random.uniform(5, min(vehicule["capacite_kg"] * 0.85, 20_000)), 2)
            volume_m3 = round(random.uniform(0.1, min(vehicule["capacite_m3"] * 0.85, 80)), 2)
            cout_transport = round(2_500 + distance_km * random.uniform(350, 750) + poids_kg * random.uniform(8, 25), 2)

            delai_prevu_heures = max(2, round(distance_km / random.uniform(35, 55) + random.uniform(2, 18)))
            date_prevue = date_expedition + timedelta(hours=delai_prevu_heures)

            statut_expedition = random.choices(STATUTS_EXPEDITION, weights=[0.02, 0.03, 0.93, 0.02], k=1)[0]

            expedition = {
                "expedition_id": expedition_id,
                "chauffeur_id": chauffeur_id,
                "vehicule_id": vehicule_id,
                "entrepot_origine_id": entrepot_origine_id,
                "entrepot_destination_id": entrepot_destination_id,
                "pays_origine": pays_origine,
                "ville_origine": origine["ville"],
                "pays_destination": pays_destination,
                "ville_destination": destination["ville"],
                "date_expedition": date_expedition.isoformat(),
                "date_livraison_prevue": date_prevue.isoformat(),
                "type_marchandise": random.choice(TYPES_MARCHANDISE),
                "poids_kg": poids_kg,
                "volume_m3": volume_m3,
                "distance_km": distance_km,
                "cout_transport_xof": cout_transport,
                "statut_expedition": statut_expedition,
                "source_system": "synthetic_generator",
                "batch_id": batch_exp,
                "ingested_at": ingested_at,
            }
            ecrire_json_line(fichier_exp, expedition)

            if statut_expedition == "Annulée":
                statut_livraison = "Échouée"
                date_livraison = None
                motif_incident = "Expédition annulée"
            elif statut_expedition in {"Préparée", "En transit"}:
                statut_livraison = "En cours"
                date_livraison = None
                motif_incident = None
            else:
                statut_livraison = random.choices(
                    ["Livrée à temps", "Livrée en retard", "Échouée"],
                    weights=[0.84, 0.12, 0.04],
                    k=1,
                )[0]
                if statut_livraison == "Livrée à temps":
                    date_livraison = date_prevue - timedelta(minutes=random.randint(5, max(6, delai_prevu_heures * 20)))
                    motif_incident = None
                elif statut_livraison == "Livrée en retard":
                    date_livraison = date_prevue + timedelta(minutes=random.randint(15, 1440))
                    motif_incident = random.choice([None, "Trafic", "Retard chargement", "Incident routier"])
                else:
                    date_livraison = None
                    motif_incident = random.choice(MOTIFS_ECHEC)

            livraison = {
                "livraison_id": expedition_id,
                "expedition_id": expedition_id,
                "chauffeur_id": chauffeur_id,
                "vehicule_id": vehicule_id,
                "date_livraison_prevue": date_prevue.isoformat(),
                "date_livraison_reelle": date_livraison.isoformat() if date_livraison else None,
                "statut_livraison": statut_livraison,
                "incident": motif_incident,
                "pays_destination": pays_destination,
                "ville_destination": destination["ville"],
                "source_system": "synthetic_generator",
                "batch_id": batch_liv,
                "ingested_at": ingested_at,
            }
            ecrire_json_line(fichier_liv, livraison)
            afficher_progression("Expéditions / livraisons", expedition_id, NB_EXPEDITIONS)


# VALIDATION

def compter_lignes(chemin):
    with chemin.open("r", encoding="utf-8") as fichier:
        return sum(1 for ligne in fichier if ligne.strip())


def valider_fichiers():
    attentes = {
        "chauffeurs.json": NB_CHAUFFEURS,
        "vehicules.json": NB_VEHICULES,
        "entrepots.json": NB_ENTREPOTS,
        "expeditions.json": NB_EXPEDITIONS,
        "livraisons.json": NB_LIVRAISONS,
    }

    logger.info("VALIDATION DES FICHIERS BRONZE")
    for nom, attendu in attentes.items():
        obtenu = compter_lignes(BRONZE_DIR / nom)
        statut = "OK" if obtenu == attendu else "ERREUR"
        logger.info("%s | attendu=%,d | obtenu=%,d | %s", nom, attendu, obtenu, statut)
        if obtenu != attendu:
            raise ValueError(f"{nom}: {obtenu} lignes au lieu de {attendu}")


# MAIN

def main():
    logger.info("GÉNÉRATION BRONZE - MIRAH-BI WEST AFRICA LOGISTICS ANALYTICS")
    chauffeurs, chauffeurs_par_pays = generer_chauffeurs()
    vehicules, vehicules_par_pays = generer_vehicules(chauffeurs, chauffeurs_par_pays)
    entrepots, entrepots_par_pays = generer_entrepots()
    generer_expeditions_livraisons(
        chauffeurs,
        vehicules,
        vehicules_par_pays,
        entrepots,
        entrepots_par_pays,
    )
    valider_fichiers()
    logger.info("GÉNÉRATION BRONZE TERMINÉE AVEC SUCCÈS")


if __name__ == "__main__":
    main()
