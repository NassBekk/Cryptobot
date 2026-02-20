# Utiliser une image Python officielle
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer setuptools et wheel pour la compilation des packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/models /app/data/processed /app/data/predictions

# Rendre le script d'entrypoint exécutable
RUN chmod +x /app/entrypoint.sh

# Exposer le port de l'application
EXPOSE 8000

# Utiliser le script d'entrypoint pour l'initialisation et le démarrage
ENTRYPOINT ["/app/entrypoint.sh"]
