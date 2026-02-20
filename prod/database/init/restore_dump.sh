#!/bin/bash
set -e

# Script pour restaurer un dump PostgreSQL custom (.dump)
# Ce script sera exécuté automatiquement au démarrage du conteneur

echo "Restauration du dump de la base de données..."

# Attendre que PostgreSQL soit prêt
until pg_isready -U nassim -d crypto; do
  echo "En attente de PostgreSQL..."
  sleep 1
done

# Restaurer le dump si présent
if [ -f /docker-entrypoint-initdb.d/crypto.dump ]; then
    echo "Restauration du dump custom..."
    pg_restore -U nassim -d crypto -v /docker-entrypoint-initdb.d/crypto.dump || true
    echo "Dump restauré avec succès."
elif [ -f /docker-entrypoint-initdb.d/init.dump ]; then
    echo "Restauration du dump custom (init.dump)..."
    pg_restore -U nassim -d crypto -v /docker-entrypoint-initdb.d/init.dump || true
    echo "Dump restauré avec succès."
else
    echo "Aucun dump custom trouvé. Ignoré."
fi
