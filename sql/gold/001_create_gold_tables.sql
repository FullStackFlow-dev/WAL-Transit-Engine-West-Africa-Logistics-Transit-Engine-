USE SCHEMA GOLD;

CREATE TABLE IF NOT EXISTS dim_pays (
    pays_id NUMBER(38,0),
    pays VARCHAR,
    region VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id NUMBER(8,0),
    date DATE,
    jour NUMBER(2,0),
    mois NUMBER(2,0),
    trimestre NUMBER(1,0),
    annee NUMBER(4,0),
    jour_semaine NUMBER(1,0)
);

CREATE TABLE IF NOT EXISTS dim_chauffeur (
    chauffeur_id NUMBER(38,0),
    nom VARCHAR,
    pays VARCHAR,
    ville VARCHAR,
    date_integration DATE,
    statut VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_vehicule (
    vehicule_id NUMBER(38,0),
    chauffeur_id NUMBER(38,0),
    pays VARCHAR,
    ville VARCHAR,
    type_vehicule VARCHAR,
    marque VARCHAR,
    annee NUMBER(4,0),
    capacite_kg NUMBER(12,0),
    capacite_m3 NUMBER(12,2),
    statut VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_entrepot (
    entrepot_id NUMBER(38,0),
    nom_entrepot VARCHAR,
    pays VARCHAR,
    ville VARCHAR,
    capacite_m3 NUMBER(14,2),
    volume_stocke_m3 NUMBER(14,2),
    taux_occupation_pct NUMBER(7,2),
    statut VARCHAR
);

CREATE TABLE IF NOT EXISTS fact_expedition (
    expedition_id NUMBER(38,0),
    chauffeur_id NUMBER(38,0),
    vehicule_id NUMBER(38,0),
    entrepot_origine_id NUMBER(38,0),
    entrepot_destination_id NUMBER(38,0),
    pays_origine VARCHAR,
    ville_origine VARCHAR,
    pays_destination VARCHAR,
    ville_destination VARCHAR,
    date_expedition TIMESTAMP_NTZ,
    date_livraison_prevue TIMESTAMP_NTZ,
    type_marchandise VARCHAR,
    poids_kg NUMBER(14,2),
    volume_m3 NUMBER(14,2),
    distance_km NUMBER(14,2),
    cout_transport_xof NUMBER(18,2),
    statut_expedition VARCHAR,
    source_system VARCHAR,
    batch_id VARCHAR,
    ingested_at TIMESTAMP_NTZ,
    annee NUMBER(4,0),
    mois NUMBER(2,0),
    silver_processed_at TIMESTAMP_NTZ,
    date_expedition_id NUMBER(8,0),
    date_livraison_prevue_id NUMBER(8,0)
);

CREATE TABLE IF NOT EXISTS fact_livraison (
    livraison_id NUMBER(38,0),
    expedition_id NUMBER(38,0),
    chauffeur_id NUMBER(38,0),
    vehicule_id NUMBER(38,0),
    date_livraison_prevue TIMESTAMP_NTZ,
    date_livraison_reelle TIMESTAMP_NTZ,
    statut_livraison VARCHAR,
    incident VARCHAR,
    pays_destination VARCHAR,
    ville_destination VARCHAR,
    source_system VARCHAR,
    batch_id VARCHAR,
    ingested_at TIMESTAMP_NTZ,
    delai_heures NUMBER(14,2),
    est_livree BOOLEAN,
    est_a_temps BOOLEAN,
    silver_processed_at TIMESTAMP_NTZ,
    date_livraison_prevue_id NUMBER(8,0),
    date_livraison_reelle_id NUMBER(8,0)
);

CREATE TABLE IF NOT EXISTS kpi_global (
    nombre_expeditions NUMBER(38,0),
    nombre_livraisons NUMBER(38,0),
    poids_total_expedie_kg NUMBER(20,2),
    volume_total_expedie_m3 NUMBER(20,2),
    distance_totale_km NUMBER(20,2),
    cout_transport_total_xof NUMBER(24,2),
    taux_livraison_temps_pct NUMBER(7,2),
    taux_echec_livraison_pct NUMBER(7,2),
    vehicules_actifs NUMBER(38,0),
    vehicules_total NUMBER(38,0),
    taux_utilisation_vehicules_pct NUMBER(7,2),
    taux_occupation_entrepots_moyen_pct NUMBER(7,2)
);

CREATE TABLE IF NOT EXISTS kpi_pays (
    pays_destination VARCHAR,
    nombre_expeditions NUMBER(38,0),
    poids_total_kg NUMBER(20,2),
    volume_total_m3 NUMBER(20,2),
    distance_totale_km NUMBER(20,2),
    cout_transport_total_xof NUMBER(24,2),
    nombre_livraisons NUMBER(38,0),
    livraisons_a_temps NUMBER(38,0),
    livraisons_echouees NUMBER(38,0),
    taux_livraison_temps_pct NUMBER(7,2),
    taux_echec_pct NUMBER(7,2)
);

CREATE TABLE IF NOT EXISTS kpi_chauffeurs (
    chauffeur_id NUMBER(38,0),
    nombre_livraisons NUMBER(38,0),
    livraisons_a_temps NUMBER(38,0),
    livraisons_echouees NUMBER(38,0),
    taux_a_temps_pct NUMBER(7,2)
);

CREATE TABLE IF NOT EXISTS kpi_entrepots (
    entrepot_id NUMBER(38,0),
    nom_entrepot VARCHAR,
    pays VARCHAR,
    ville VARCHAR,
    capacite_m3 NUMBER(14,2),
    volume_stocke_m3 NUMBER(14,2),
    taux_occupation_pct NUMBER(7,2)
);

CREATE TABLE IF NOT EXISTS kpi_mensuel (
    annee NUMBER(4,0),
    mois NUMBER(2,0),
    nombre_expeditions NUMBER(38,0),
    poids_total_kg NUMBER(20,2),
    volume_total_m3 NUMBER(20,2),
    cout_transport_total_xof NUMBER(24,2)
);
