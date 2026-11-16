# KPI logistiques

- **Taux de livraison à temps** : livraisons marquées `Livrée à temps` / total des livraisons.
- **Taux d'échec** : livraisons marquées `Échouée` / total des livraisons.
- **Volume expédié** : somme des poids et volumes des expéditions.
- **Coût de transport** : somme de `cout_transport_xof`.
- **Utilisation des véhicules** : véhicules `Disponible` ou `En mission` / parc total, selon la règle implémentée.
- **Occupation des entrepôts** : `volume_stocke_m3 / capacite_m3 * 100`.
- **Productivité chauffeur** : nombre de livraisons par chauffeur.

Les agrégations sont disponibles dans les tables `KPI_*` du schéma Gold.
