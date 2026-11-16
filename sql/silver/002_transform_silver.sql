TRUNCATE TABLE CHAUFFEURS;
INSERT INTO CHAUFFEURS
SELECT
    chauffeur_id,
    TRIM(nom),
    TRIM(pays),
    TRIM(ville),
    date_integration,
    TRIM(statut),
    source_system,
    batch_id,
    ingested_at,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
FROM {{BRONZE_SCHEMA}}.CHAUFFEURS
WHERE chauffeur_id IS NOT NULL
  AND nom IS NOT NULL
  AND ville IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY chauffeur_id ORDER BY ingested_at DESC) = 1;

TRUNCATE TABLE VEHICULES;
INSERT INTO VEHICULES
SELECT
    vehicule_id,
    chauffeur_id,
    TRIM(pays),
    TRIM(ville),
    TRIM(type_vehicule),
    TRIM(marque),
    annee,
    capacite_kg,
    capacite_m3,
    TRIM(statut),
    source_system,
    batch_id,
    ingested_at,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
FROM {{BRONZE_SCHEMA}}.VEHICULES
WHERE vehicule_id IS NOT NULL
  AND capacite_kg > 0
  AND capacite_m3 > 0
QUALIFY ROW_NUMBER() OVER (PARTITION BY vehicule_id ORDER BY ingested_at DESC) = 1;

TRUNCATE TABLE ENTREPOTS;
INSERT INTO ENTREPOTS
SELECT
    entrepot_id,
    TRIM(nom_entrepot),
    TRIM(pays),
    TRIM(ville),
    capacite_m3,
    volume_stocke_m3,
    ROUND(volume_stocke_m3 / NULLIF(capacite_m3, 0) * 100, 2),
    TRIM(statut),
    source_system,
    batch_id,
    ingested_at,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
FROM {{BRONZE_SCHEMA}}.ENTREPOTS
WHERE entrepot_id IS NOT NULL
  AND capacite_m3 > 0
  AND volume_stocke_m3 BETWEEN 0 AND capacite_m3
QUALIFY ROW_NUMBER() OVER (PARTITION BY entrepot_id ORDER BY ingested_at DESC) = 1;

TRUNCATE TABLE EXPEDITIONS;
INSERT INTO EXPEDITIONS
SELECT
    expedition_id,
    chauffeur_id,
    vehicule_id,
    entrepot_origine_id,
    entrepot_destination_id,
    TRIM(pays_origine),
    TRIM(ville_origine),
    TRIM(pays_destination),
    TRIM(ville_destination),
    date_expedition,
    date_livraison_prevue,
    TRIM(type_marchandise),
    poids_kg,
    volume_m3,
    distance_km,
    cout_transport_xof,
    TRIM(statut_expedition),
    source_system,
    batch_id,
    ingested_at,
    YEAR(date_expedition),
    MONTH(date_expedition),
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
FROM {{BRONZE_SCHEMA}}.EXPEDITIONS
WHERE expedition_id IS NOT NULL
  AND poids_kg > 0
  AND volume_m3 > 0
  AND distance_km > 0
  AND cout_transport_xof > 0
  AND date_livraison_prevue > date_expedition
QUALIFY ROW_NUMBER() OVER (PARTITION BY expedition_id ORDER BY ingested_at DESC) = 1;

TRUNCATE TABLE LIVRAISONS;
INSERT INTO LIVRAISONS
SELECT
    livraison_id,
    expedition_id,
    chauffeur_id,
    vehicule_id,
    date_livraison_prevue,
    date_livraison_reelle,
    TRIM(statut_livraison),
    TRIM(incident),
    TRIM(pays_destination),
    TRIM(ville_destination),
    source_system,
    batch_id,
    ingested_at,
    ROUND(DATEDIFF('second', date_livraison_prevue, date_livraison_reelle) / 3600.0, 2),
    statut_livraison IN ('Livrée à temps', 'Livrée en retard'),
    statut_livraison = 'Livrée à temps',
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ
FROM {{BRONZE_SCHEMA}}.LIVRAISONS
WHERE livraison_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY livraison_id ORDER BY ingested_at DESC) = 1;
