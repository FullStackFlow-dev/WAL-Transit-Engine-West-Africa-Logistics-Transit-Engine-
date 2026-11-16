# Snowflake

## Configuration

`APP_ENV` sélectionne `config/dev.yaml` ou `config/prod.yaml`. Les scripts utilisent la base, le warehouse et les schémas de cet environnement. Les variables `SNOWFLAKE_DATABASE`, `SNOWFLAKE_WAREHOUSE` et `SNOWFLAKE_ROLE`, si renseignées dans `.env`, remplacent les valeurs de configuration.

L'authentification par navigateur est activée par défaut dans `.env.example` (`SNOWFLAKE_AUTHENTICATOR=externalbrowser`). Pour utiliser un mot de passe, choisissez `SNOWFLAKE_AUTHENTICATOR=snowflake` et définissez `SNOWFLAKE_PASSWORD`.

## Schémas

- `BRONZE`
- `SILVER`
- `GOLD`

## Exécution

```powershell
Copy-Item .env.example .env
# Renseigner le compte et l'utilisateur Snowflake dans .env.
python -u -m scripts.load_bronze_snowflake
python -u -m scripts.run_snowflake_sql silver
python -u -m scripts.run_snowflake_sql gold
python -u -m scripts.validate_snowflake
```

Les scripts SQL `001_create_*_tables.sql` créent les tables dans la base active de la session Snowflake. Sélectionnez la base correspondant à `APP_ENV` avant de les exécuter.

## Validation

La validation vérifie les volumes attendus et l'absence de références orphelines sur les relations principales.

Résultat attendu :

```text
VALIDATION SNOWFLAKE : OK
```

## Sécurité

Les identifiants sont chargés depuis `.env`. Le fichier `.env` ne doit jamais être versionné.
