USE SCHEMA SILVER;

CREATE TABLE IF NOT EXISTS chauffeurs (
    chauffeur_id NUMBER(38,0),
    nom VARCHAR,
    pays VARCHAR,
    ville VARCHAR,
    date_integration DATE,
    statut VARCHAR,
    source_system VARCHAR,
    batch_id VARCHAR,
    ingested_at TIMESTAMP_NTZ,
    silver_processed_at TIMESTAMP_NTZ
);

CREATE TABLE IF NOT EXISTS vehicules (
    vehicule_id NUMBER(38,0),
    chauffeur_id NUMBER(38,0),
    pays VARCHAR,
    ville VARCHAR,
    type_vehicule VARCHAR,
    marque VARCHAR,
    annee NUMBER(4,0),
    capacite_kg NUMBER(12,0),
    capacite_m3 NUMBER(12,2),
    statut VARCHAR,
    source_system VARCHAR,
    batch_id VARCHAR,
    ingested_at TIMESTAMP_NTZ,
    silver_processed_at TIMESTAMP_NTZ
);

CREATE TABLE IF NOT EXISTS entrepots (
    entrepot_id NUMBER(38,0),
    nom_entrepot VARCHAR,
    pays VARCHAR,
    ville VARCHAR,
    capacite_m3 NUMBER(14,2),
    volume_stocke_m3 NUMBER(14,2),
    taux_occupation_pct NUMBER(7,2),
    statut VARCHAR,
    source_system VARCHAR,
    batch_id VARCHAR,
    ingested_at TIMESTAMP_NTZ,
    silver_processed_at TIMESTAMP_NTZ
);

CREATE TABLE IF NOT EXISTS expeditions (
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
    silver_processed_at TIMESTAMP_NTZ
);

CREATE TABLE IF NOT EXISTS livraisons (
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
    silver_processed_at TIMESTAMP_NTZ
);
