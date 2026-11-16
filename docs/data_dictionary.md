# Dictionnaire de données

## Bronze / Silver

### Chauffeurs
- `chauffeur_id` : identifiant du chauffeur
- `nom` : identité synthétique adaptée au pays
- `pays`, `ville` : zone d'opération
- `date_integration` : date d'intégration
- `statut` : statut opérationnel

### Véhicules
- `vehicule_id`, `chauffeur_id` : identifiants
- `type_vehicule`, `marque`, `annee` : caractéristiques
- `capacite_kg`, `capacite_m3` : capacités
- `statut` : état opérationnel

### Entrepôts
- `entrepot_id`, `nom_entrepot`
- `pays`, `ville`
- `capacite_m3`, `volume_stocke_m3`
- `taux_occupation_pct`

### Expéditions
- `expedition_id`
- `chauffeur_id`, `vehicule_id`
- `entrepot_origine_id`, `entrepot_destination_id`
- `pays_origine`, `pays_destination`
- `date_expedition`, `date_livraison_prevue`
- `poids_kg`, `volume_m3`, `distance_km`
- `cout_transport_xof`
- `statut_expedition`

### Livraisons
- `livraison_id`, `expedition_id`
- `chauffeur_id`, `vehicule_id`
- `date_livraison_prevue`, `date_livraison_reelle`
- `statut_livraison`, `incident`
- Silver ajoute `delai_heures`, `est_livree`, `est_a_temps`.

## Gold

Dimensions : `DIM_DATE`, `DIM_PAYS`, `DIM_CHAUFFEUR`, `DIM_VEHICULE`, `DIM_ENTREPOT`.

Faits : `FACT_EXPEDITION`, `FACT_LIVRAISON`.

Agrégats : `KPI_GLOBAL`, `KPI_PAYS`, `KPI_CHAUFFEURS`, `KPI_ENTREPOTS`, `KPI_MENSUEL`.
