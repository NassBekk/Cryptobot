#!/bin/bash

# Script pour exporter un dump de la base de données PostgreSQL
# Usage: ./export_dump.sh [host] [port]

set -e

# Configuration par défaut
DB_HOST="${1:-localhost}"
DB_PORT="${2:-5432}"
DB_USER="nassim"
DB_NAME="crypto"
OUTPUT_DIR="database/init"
OUTPUT_FILE="${OUTPUT_DIR}/init.sql"

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Export du dump de la base de données ===${NC}"
echo "Host: $DB_HOST"
echo "Port: $DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""

# Créer le dossier de sortie s'il n'existe pas
mkdir -p "$OUTPUT_DIR"

# Vérifier si pg_dump est installé
if ! command -v pg_dump &> /dev/null; then
    echo -e "${RED}Erreur: pg_dump n'est pas installé.${NC}"
    echo "Installation: sudo apt-get install postgresql-client"
    exit 1
fi

# Demander le mot de passe
echo -e "${YELLOW}Mot de passe PostgreSQL pour l'utilisateur '$DB_USER':${NC}"
export PGPASSWORD

# Exporter le dump
echo -e "${GREEN}Export en cours...${NC}"
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$OUTPUT_FILE" --verbose; then
    echo ""
    echo -e "${GREEN}✓ Dump exporté avec succès vers: $OUTPUT_FILE${NC}"
    
    # Afficher la taille du fichier
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo -e "${GREEN}Taille du fichier: $FILE_SIZE${NC}"
    
    echo ""
    echo -e "${YELLOW}Pour charger ce dump dans le conteneur Docker:${NC}"
    echo "  1. Arrêtez les conteneurs: docker-compose down"
    echo "  2. Supprimez le volume: docker-compose down -v"
    echo "  3. Redémarrez: docker-compose up -d db"
    echo ""
else
    echo -e "${RED}✗ Erreur lors de l'export${NC}"
    exit 1
fi
