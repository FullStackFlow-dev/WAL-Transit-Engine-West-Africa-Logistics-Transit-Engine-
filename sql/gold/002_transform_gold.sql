TRUNCATE TABLE DIM_CHAUFFEUR;
INSERT INTO DIM_CHAUFFEUR
SELECT chauffeur_id, nom, pays, ville, date_integration, statut
FROM {{SILVER_SCHEMA}}.CHAUFFEURS;

TRUNCATE TABLE DIM_VEHICULE;
INSERT INTO DIM_VEHICULE
SELECT vehicule_id, chauffeur_id, pays, ville, type_vehicule, marque,
       annee, capacite_kg, capacite_m3, statut
FROM {{SILVER_SCHEMA}}.VEHICULES;

TRUNCATE TABLE DIM_ENTREPOT;
INSERT INTO DIM_ENTREPOT
SELECT entrepot_id, nom_entrepot, pays, ville, capacite_m3,
       volume_stocke_m3, taux_occupation_pct, statut
FROM {{SILVER_SCHEMA}}.ENTREPOTS;

TRUNCATE TABLE DIM_PAYS;
INSERT INTO DIM_PAYS
SELECT
    ROW_NUMBER() OVER (ORDER BY pays),
    pays,
    'Afrique de l''Ouest'
FROM (
    SELECT pays FROM {{SILVER_SCHEMA}}.CHAUFFEURS
    UNION
    SELECT pays FROM {{SILVER_SCHEMA}}.ENTREPOTS
);

TRUNCATE TABLE DIM_DATE;
INSERT INTO DIM_DATE
SELECT
    TO_NUMBER(TO_CHAR(date_jour, 'YYYYMMDD')),
    date_jour,
    DAY(date_jour),
    MONTH(date_jour),
    QUARTER(date_jour),
    YEAR(date_jour),
    DAYOFWEEKISO(date_jour)
FROM (
    SELECT DISTINCT date_jour
    FROM (
        SELECT date_expedition::DATE AS date_jour FROM {{SILVER_SCHEMA}}.EXPEDITIONS
        UNION
        SELECT date_livraison_prevue::DATE FROM {{SILVER_SCHEMA}}.EXPEDITIONS
        UNION
        SELECT date_livraison_reelle::DATE FROM {{SILVER_SCHEMA}}.LIVRAISONS
        WHERE date_livraison_reelle IS NOT NULL
    )
);

TRUNCATE TABLE FACT_EXPEDITION;
INSERT INTO FACT_EXPEDITION
SELECT
    e.*,
    TO_NUMBER(TO_CHAR(e.date_expedition::DATE, 'YYYYMMDD')),
    TO_NUMBER(TO_CHAR(e.date_livraison_prevue::DATE, 'YYYYMMDD'))
FROM {{SILVER_SCHEMA}}.EXPEDITIONS e;

TRUNCATE TABLE FACT_LIVRAISON;
INSERT INTO FACT_LIVRAISON
SELECT
    l.*,
    TO_NUMBER(TO_CHAR(l.date_livraison_prevue::DATE, 'YYYYMMDD')),
    IFF(
        l.date_livraison_reelle IS NULL,
        NULL,
        TO_NUMBER(TO_CHAR(l.date_livraison_reelle::DATE, 'YYYYMMDD'))
    )
FROM {{SILVER_SCHEMA}}.LIVRAISONS l;

TRUNCATE TABLE KPI_GLOBAL;
INSERT INTO KPI_GLOBAL
SELECT
    (SELECT COUNT(*) FROM {{SILVER_SCHEMA}}.EXPEDITIONS),
    (SELECT COUNT(*) FROM {{SILVER_SCHEMA}}.LIVRAISONS),
    (SELECT ROUND(SUM(poids_kg), 2) FROM {{SILVER_SCHEMA}}.EXPEDITIONS),
    (SELECT ROUND(SUM(volume_m3), 2) FROM {{SILVER_SCHEMA}}.EXPEDITIONS),
    (SELECT ROUND(SUM(distance_km), 2) FROM {{SILVER_SCHEMA}}.EXPEDITIONS),
    (SELECT ROUND(SUM(cout_transport_xof), 2) FROM {{SILVER_SCHEMA}}.EXPEDITIONS),
    (SELECT ROUND(AVG(IFF(est_a_temps, 1, 0)) * 100, 2) FROM {{SILVER_SCHEMA}}.LIVRAISONS),
    (SELECT ROUND(AVG(IFF(statut_livraison = 'Échouée', 1, 0)) * 100, 2) FROM {{SILVER_SCHEMA}}.LIVRAISONS),
    (SELECT COUNT_IF(statut IN ('Disponible', 'En mission')) FROM {{SILVER_SCHEMA}}.VEHICULES),
    (SELECT COUNT(*) FROM {{SILVER_SCHEMA}}.VEHICULES),
    (SELECT ROUND(AVG(IFF(statut IN ('Disponible', 'En mission'), 1, 0)) * 100, 2) FROM {{SILVER_SCHEMA}}.VEHICULES),
    (SELECT ROUND(AVG(taux_occupation_pct), 2) FROM {{SILVER_SCHEMA}}.ENTREPOTS);

TRUNCATE TABLE KPI_PAYS;
INSERT INTO KPI_PAYS
SELECT
    e.pays_destination,
    COUNT(DISTINCT e.expedition_id),
    ROUND(SUM(e.poids_kg), 2),
    ROUND(SUM(e.volume_m3), 2),
    ROUND(SUM(e.distance_km), 2),
    ROUND(SUM(e.cout_transport_xof), 2),
    COUNT(DISTINCT l.livraison_id),
    COUNT_IF(l.est_a_temps),
    COUNT_IF(l.statut_livraison = 'Échouée'),
    ROUND(COUNT_IF(l.est_a_temps) / NULLIF(COUNT(DISTINCT l.livraison_id), 0) * 100, 2),
    ROUND(COUNT_IF(l.statut_livraison = 'Échouée') / NULLIF(COUNT(DISTINCT l.livraison_id), 0) * 100, 2)
FROM {{SILVER_SCHEMA}}.EXPEDITIONS e
LEFT JOIN {{SILVER_SCHEMA}}.LIVRAISONS l
    ON l.expedition_id = e.expedition_id
GROUP BY e.pays_destination;

TRUNCATE TABLE KPI_CHAUFFEURS;
INSERT INTO KPI_CHAUFFEURS
SELECT
    chauffeur_id,
    COUNT(*),
    COUNT_IF(est_a_temps),
    COUNT_IF(statut_livraison = 'Échouée'),
    ROUND(COUNT_IF(est_a_temps) / NULLIF(COUNT(*), 0) * 100, 2)
FROM {{SILVER_SCHEMA}}.LIVRAISONS
GROUP BY chauffeur_id;

TRUNCATE TABLE KPI_ENTREPOTS;
INSERT INTO KPI_ENTREPOTS
SELECT entrepot_id, nom_entrepot, pays, ville, capacite_m3,
       volume_stocke_m3, taux_occupation_pct
FROM {{SILVER_SCHEMA}}.ENTREPOTS;

TRUNCATE TABLE KPI_MENSUEL;
INSERT INTO KPI_MENSUEL
SELECT
    YEAR(date_expedition),
    MONTH(date_expedition),
    COUNT(*),
    ROUND(SUM(poids_kg), 2),
    ROUND(SUM(volume_m3), 2),
    ROUND(SUM(cout_transport_xof), 2)
FROM {{SILVER_SCHEMA}}.EXPEDITIONS
GROUP BY YEAR(date_expedition), MONTH(date_expedition);
