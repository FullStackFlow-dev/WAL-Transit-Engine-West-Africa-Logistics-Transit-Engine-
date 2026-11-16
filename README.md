# MIRAH-BI West Africa Logistics Analytics

![Statut](https://img.shields.io/badge/statut-en%20d%C3%A9veloppement-orange)
![Plateforme](https://img.shields.io/badge/data%20warehouse-Snowflake-29B5E8)
![Architecture](https://img.shields.io/badge/architecture-Bronze%20%2F%20Silver%20%2F%20Gold-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)

> Plateforme analytique logistique de bout en bout connecter à la plateforme **Snowflake**, couvrant 10 pays d'Afrique de l'Ouest et alimentant la plateforme **MIRAH-BI**.


``` Projet MIRAH-BI développé dans le cadre de la plateforme MIRAH-BI.

Ce projet a été proposé afin de permettre à l'équipe Data/BI de concevoir, tester et industrialiser des pipelines analytiques logistiques couvrant le Sénégal et plusieurs pays d'Afrique de l'Ouest.

L'objectif est de fournir un environnement réaliste permettant :

- la génération de données logistiques
- l'expérimentation de pipelines Bronze / Silver / Gold
- le chargement dans plusieurs SGBD et Data Warehouses
- la mise en œuvre de Snowflake
- les tests de qualité de données
- la conception de tableaux de bord BI
- la validation des architectures MIRAH-BI
```

| | |
|---|---|
| **Projet parent** | MIRAH-BI |
| **Rôle de ce dépôt** | Source de données logistiques (ingestion, transformation, modélisation, KPI) |
| **Responsable technique** | Database & Data Engineer, équipe MIRAH-BI |
| **Version du document** | 1.0 |

---

## Table des matières

1. [Contexte métier](#1-contexte-métier)
2. [Objectifs et périmètre](#2-objectifs-et-périmètre)
3. [Architecture](#3-architecture)
4. [Modèle de données](#4-modèle-de-données)
5. [Indicateurs (KPI)](#5-indicateurs-kpi)
6. [Structure du dépôt](#6-structure-du-dépôt)
7. [Stack technique](#7-stack-technique)
8. [Démarrage rapide](#8-démarrage-rapide)
9. [Configuration et environnements](#9-configuration-et-environnements)
10. [Exécution du pipeline](#10-exécution-du-pipeline)
11. [Qualité des données et tests](#11-qualité-des-données-et-tests)
12. [Sécurité et gouvernance](#12-sécurité-et-gouvernance)
13. [Intégration avec MIRAH-BI](#13-intégration-avec-mirah-bi)
14. [Observabilité](#14-observabilité)
15. [Conventions](#15-conventions)
16. [Feuille de route](#16-feuille-de-route)
17. [Contribution](#17-contribution)

---

## 1. Contexte métier

L'entreprise opère des activités logistiques dans dix pays d'Afrique de l'Ouest :

| Zone | Pays |
|---|---|
| Afrique de l'Ouest francophone | Sénégal, Côte d'Ivoire, Mali, Guinée, Burkina Faso, Bénin, Togo, Mauritanie |
| Afrique de l'Ouest anglophone | Ghana, Gambie |

Les opérations génèrent des données sur cinq domaines :

- **Chauffeurs** : identité, affiliation, statut, pays d'opération
- **Véhicules** : parc, type, capacité, état
- **Entrepôts** : localisation, capacité, pays
- **Expéditions** : origine, destination, poids, volume, statut
- **Livraisons** : délais, réussite ou échec, incidents

Aujourd'hui, ces données sont dispersées et difficiles à consolider à l'échelle régionale. Ce projet fournit une base analytique unique, fiable et historisée, pour le pilotage des opérations.

## 2. Objectifs et périmètre

### Objectifs

1. Générer et ingérer les données métier de façon reproductible.
2. Structurer les données en trois couches **Bronze, Silver, Gold**.
3. Charger et modéliser les données dans **Snowflake**.
4. Produire des **KPI logistiques** standardisés.
5. Alimenter les **tableaux de bord MIRAH-BI** via une couche Gold documentée.

### Dans le périmètre

- Génération de données synthétiques réalistes pour les 10 pays
- Pipeline d'ingestion et de transformation
- Modèle dimensionnel (étoile) en couche Gold
- Contrôles de qualité et tests automatisés
- Documentation technique et dictionnaire de données

### Hors périmètre

- Conception des tableaux de bord (portée par MIRAH-BI)
- Systèmes opérationnels sources (TMS, WMS)
- Applications métier temps réel

## 3. Architecture

### Vue d'ensemble

```mermaid
flowchart LR
    A[Génération / sources<br/>chauffeurs, véhicules,<br/>entrepôts, expéditions,<br/>livraisons] --> B[(BRONZE<br/>données brutes)]
    B --> C[(SILVER<br/>nettoyées, typées,<br/>dédupliquées)]
    C --> D[(GOLD<br/>modèle dimensionnel<br/>et KPI)]
    D --> E[MIRAH-BI<br/>tableaux de bord]
```

### Rôle de chaque couche

| Couche | Rôle | Principes |
|---|---|---|
| **Bronze** | Données brutes, telles que reçues | Aucune transformation métier, conservation de l'historique, métadonnées d'ingestion (date, source, lot) |
| **Silver** | Données nettoyées et conformées | Typage, normalisation (pays, dates, unités), dédoublonnage, règles de qualité appliquées |
| **Gold** | Données prêtes pour l'analyse | Modèle en étoile, agrégats, KPI, optimisées pour la lecture par MIRAH-BI |

### Organisation Snowflake (proposée)

```text
Base de données : LOGISTICS_<ENV>          (ex. LOGISTICS_DEV, LOGISTICS_PROD)
 ├── Schéma BRONZE
 ├── Schéma SILVER
 └── Schéma GOLD
Warehouse       : WH_LOGISTICS_<ENV>_ETL   (chargement et transformation)
                  WH_LOGISTICS_<ENV>_BI    (lecture par MIRAH-BI)
Rôles           : ROLE_LOGISTICS_ENGINEER, ROLE_LOGISTICS_ANALYST, ROLE_MIRAH_BI_READER
```

> Les noms ci-dessus sont une convention de départ. À aligner avec les standards Snowflake de MIRAH-BI avant mise en production.

## 4. Modèle de données

Modèle dimensionnel en étoile (couche Gold).

**Dimensions**

| Table | Description |
|---|---|
| `DIM_DATE` | Calendrier (jour, semaine, mois, trimestre, année) |
| `DIM_PAYS` | Pays et zone régionale |
| `DIM_CHAUFFEUR` | Chauffeurs et attributs descriptifs |
| `DIM_VEHICULE` | Parc de véhicules |
| `DIM_ENTREPOT` | Entrepôts et capacités |

**Faits**

| Table | Grain | Mesures principales |
|---|---|---|
| `FACT_EXPEDITION` | une ligne par expédition | poids, volume, distance, coût |
| `FACT_LIVRAISON` | une ligne par livraison | délai réel, délai prévu, statut, incident |

Le dictionnaire de données complet est maintenu dans `docs/`.

## 5. Indicateurs (KPI)

| KPI | Définition | Axes d'analyse |
|---|---|---|
| Taux de livraison à temps (OTD) | Livraisons dans les délais / total livraisons | pays, période, chauffeur |
| Délai moyen de livraison | Moyenne (date livraison − date expédition) | pays, axe, véhicule |
| Taux d'échec de livraison | Livraisons échouées / total livraisons | pays, motif |
| Taux d'utilisation des véhicules | Véhicules actifs / parc total | pays, type de véhicule |
| Taux d'occupation des entrepôts | Volume stocké / capacité | entrepôt, pays |
| Volume expédié | Somme des poids et volumes | pays, période |
| Productivité des chauffeurs | Livraisons par chauffeur et par période | chauffeur, pays |

Les définitions exactes (formules SQL, règles d'exclusion) sont documentées dans `docs/kpi.md` et implémentées dans `sql/gold/`.

## 6. Structure du dépôt

```text
west-africa-logistics-analytics/
│
├── data/                  # Données locales (non versionnées)
│   ├── bronze/            # Données brutes
│   ├── silver/            # Données nettoyées
│   └── gold/              # Données analytiques
│
├── scripts/               # Génération, ingestion, orchestration Python
│
├── sql/                   # Transformations et DDL Snowflake
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── tests/                 # Tests unitaires et contrôles de qualité
│
├── logs/                  # Journaux d'exécution (non versionnés)
│
├── config/                # Configuration par environnement
│   ├── dev.yaml
│   ├── local.yaml
│   └── prod.yaml
│
├── docs/                  # Documentation, dictionnaire de données, KPI
│
├── requirements.txt       # Dépendances Python
├── .env.example           # Modèle de variables d'environnement
├── .gitignore
└── README.md
```

## 7. Stack technique

| Domaine | Technologie |
|---|---|
| Data warehouse | Snowflake |
| Langages | Python 3.11+, SQL |
| Connecteur | `snowflake-connector-python` |
| Manipulation de données | pandas |
| Configuration | YAML + variables d'environnement |
| Tests | pytest |
| Consommation | MIRAH-BI |

## 8. Démarrage rapide

### Prérequis

- Python 3.11 ou supérieur
- Un compte Snowflake avec un rôle autorisé à créer des objets
- Git

### Installation

```bash
git clone <url-du-depot>
cd west-africa-logistics-analytics

python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Configuration des accès

```bash
cp .env.example .env     # Windows : copy .env.example .env
```

Renseigner ensuite les valeurs dans `.env` (voir section suivante).

## 9. Configuration et environnements

Trois environnements sont définis dans `config/` :

| Fichier | Usage |
|---|---|
| `local.yaml` | Développement sur poste, données locales |
| `dev.yaml` | Intégration sur Snowflake (base de développement) |
| `prod.yaml` | Production (consommée par MIRAH-BI) |

L'environnement actif se sélectionne via la variable `APP_ENV`.

### Variables d'environnement (`.env`)

| Variable | Description |
|---|---|
| `APP_ENV` | `local`, `dev` ou `prod` |
| `SNOWFLAKE_ACCOUNT` | Identifiant du compte Snowflake |
| `SNOWFLAKE_USER` | Utilisateur technique |
| `SNOWFLAKE_AUTHENTICATOR` | `externalbrowser` (défaut) ou `snowflake` pour une connexion par mot de passe |
| `SNOWFLAKE_PASSWORD` | Mot de passe, uniquement si `SNOWFLAKE_AUTHENTICATOR=snowflake` |
| `SNOWFLAKE_ROLE` | Rôle utilisé |
| `SNOWFLAKE_WAREHOUSE` | Warehouse de traitement (remplace la valeur de l'environnement choisi) |
| `SNOWFLAKE_DATABASE` | Base cible (remplace la valeur de l'environnement choisi) |

> **Important :** le fichier `.env` contient des secrets. Il ne doit **jamais** être versionné. Seul `.env.example`, sans valeurs réelles, est commité.

## 10. Exécution du pipeline

Ordre d'exécution :

| Étape | Action | Résultat |
|---|---|---|
| 1 | Génération des données métier | Fichiers dans `data/bronze/` |
| 2 | Création des objets Snowflake (DDL) | Schémas et tables Bronze, Silver, Gold |
| 3 | Chargement Bronze | Données brutes dans Snowflake |
| 4 | Transformation Silver | Données nettoyées et conformées |
| 5 | Construction Gold | Dimensions, faits et KPI |
| 6 | Contrôles de qualité | Rapport de validation |

Les commandes exactes seront documentées dans `scripts/README.md` au fil de l'implémentation.

**Principes d'exécution :** chaque étape est **idempotente** (relançable sans doublons) et journalisée dans `logs/`.

## 11. Qualité des données et tests

### Contrôles de qualité

- **Complétude** : champs obligatoires non nuls
- **Unicité** : clés primaires sans doublon
- **Intégrité référentielle** : chaque fait pointe vers une dimension existante
- **Validité** : valeurs dans les domaines attendus (pays, statuts, dates cohérentes)
- **Cohérence** : date de livraison postérieure à la date d'expédition
- **Réconciliation** : volumétrie cohérente entre Bronze, Silver et Gold

### Tests automatisés

```bash
pytest tests/ -v
```

Les tests doivent passer avant toute fusion vers la branche principale.

## 12. Sécurité et gouvernance

- **Secrets** : jamais dans le code ni dans Git ; utilisation de `.env` en local et d'un gestionnaire de secrets en production.
- **Moindre privilège** : rôles Snowflake distincts pour l'ingénierie, l'analyse et la lecture BI.
- **Authentification** : privilégier l'authentification par paire de clés pour les comptes de service.
- **Données personnelles** : les données chauffeurs sont traitées comme sensibles ; pseudonymisation ou masquage dans les couches exposées à la BI.
- **Traçabilité** : chaque enregistrement Bronze porte sa date d'ingestion et sa source.
- **Environnements isolés** : la production n'est modifiable que via le processus de revue.

## 13. Intégration avec MIRAH-BI

La couche **Gold** est le contrat d'interface avec MIRAH-BI.

| Élément | Engagement |
|---|---|
| Point d'accès | Schéma `GOLD` de la base `LOGISTICS_<ENV>` |
| Accès BI | Rôle en lecture seule dédié, warehouse séparé |
| Stabilité | Les tables et colonnes Gold ne changent pas sans préavis ni versionnement |
| Documentation | Dictionnaire de données et définitions KPI dans `docs/` |
| Fraîcheur | Fréquence de rafraîchissement à définir avec l'équipe MIRAH-BI |

## 14. Observabilité

- Journaux horodatés par exécution dans `logs/`
- Volumétrie de lignes tracée à chaque étape
- Statut des contrôles de qualité consigné
- Indicateurs de durée et de coût (crédits Snowflake) à suivre en production

## 15. Conventions

| Sujet | Règle |
|---|---|
| Nommage SQL | `snake_case` ; préfixes `dim_`, `fact_` en Gold |
| Colonnes techniques | `ingested_at`, `source_system`, `batch_id` en Bronze |
| Branches Git | `main` (stable), `develop`, `feature/<nom>`, `fix/<nom>` |
| Commits | Format *Conventional Commits* (`feat:`, `fix:`, `docs:`, `test:`) |
| Code Python | PEP 8, typage recommandé |
| Revue | Toute modification vers `main` passe par une revue |

## 16. Feuille de route

- [ ] **Phase 1 : Fondations** : structure du dépôt, configuration, connexion Snowflake
- [ ] **Phase 2 : Bronze** : génération des données et chargement brut
- [ ] **Phase 3 : Silver** : nettoyage, normalisation, règles de qualité
- [ ] **Phase 4 : Gold** : modèle en étoile et KPI
- [ ] **Phase 5 : Intégration** : raccordement et validation avec MIRAH-BI
- [ ] **Phase 6 : Industrialisation** : orchestration, CI/CD, monitoring

## 17. Contribution

1. Créer une branche depuis `develop` : `feature/<description>`
2. Développer en respectant les conventions ci-dessus
3. Ajouter ou mettre à jour les tests
4. Vérifier que `pytest` passe
5. Ouvrir une demande de fusion avec une description claire
6. Obtenir une revue avant fusion

---

*Projet développé dans le cadre de la plateforme MIRAH-BI.*
