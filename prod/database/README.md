# Initialisation de la Base de Données

Ce dossier contient les scripts et dumps pour initialiser la base de données PostgreSQL dans le conteneur Docker.

## Structure

```
database/
├── init/              # Dumps SQL à charger au démarrage du conteneur
│   └── init.sql      # Dump de la base de données (optionnel)
└── README.md         # Ce fichier
```

## Comment ça fonctionne

PostgreSQL exécute automatiquement tous les fichiers `.sql`, `.sql.gz`, ou scripts `.sh` présents dans `/docker-entrypoint-initdb.d/` lors du **premier démarrage** du conteneur (quand la base est vide).

Le dossier `database/init/` est monté dans `/docker-entrypoint-initdb.d/` du conteneur PostgreSQL.

## Exporter un dump depuis votre base locale

### Option 1 : Utiliser pg_dump (recommandé)

Si vous avez une base PostgreSQL locale avec les mêmes credentials :

```bash
# Depuis le répertoire prod/
pg_dump -h localhost -U nassim -d crypto -F c -f database/init/init.dump

# Ou en format SQL plain (plus facile à lire/modifier)
pg_dump -h localhost -U nassim -d crypto -f database/init/init.sql
```

### Option 2 : Si la base est sur un serveur distant

```bash
# Format custom (compressé, plus rapide)
pg_dump -h VOTRE_SERVEUR -U nassim -d crypto -F c -f database/init/init.dump

# Format SQL (texte, lisible)
pg_dump -h VOTRE_SERVEUR -U nassim -d crypto -f database/init/init.sql
```

### Option 3 : Si vous avez déjà un dump

1. Placez votre fichier dump dans `database/init/`
2. Nommez-le `init.sql` ou `init.dump` (ou tout autre nom avec extension `.sql`, `.sql.gz`, `.dump`)
3. PostgreSQL l'exécutera automatiquement au démarrage

## Format du fichier dump

Le fichier peut être :
- **`.sql`** : Format SQL plain text (recommandé pour la lisibilité)
- **`.sql.gz`** : SQL compressé avec gzip
- **`.dump`** : Format custom PostgreSQL (binaire compressé, plus rapide)

## Important

⚠️ **Les scripts dans `/docker-entrypoint-initdb.d/` ne sont exécutés QUE lors du PREMIER démarrage** du conteneur (quand la base est vide).

Si vous voulez réinitialiser la base avec un nouveau dump :

```bash
# Arrêter les conteneurs
docker-compose down

# Supprimer le volume de données (ATTENTION : perte de données)
docker volume rm prod_postgres_data

# Redémarrer (le dump sera chargé)
docker-compose up -d db
```

Ou plus simple, supprimez le volume dans docker-compose.yml et recréez :

```bash
docker-compose down -v  # Supprime les volumes
docker-compose up -d    # Recrée et charge le dump
```

## Vérification

Pour vérifier que le dump a été chargé :

```bash
# Se connecter à la base dans le conteneur
docker-compose exec db psql -U nassim -d crypto

# Dans psql, lister les tables
\dt

# Voir le contenu d'une table
SELECT COUNT(*) FROM binance_historical_data_with_metrics;
```

## Script d'aide

Un script `export_dump.sh` est disponible pour faciliter l'export (voir ci-dessous).
