import argparse
import subprocess
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Pipeline de prédiction pour les cryptomonnaies")
    parser.add_argument("--clean", action="store_true", help="Nettoyer les données")
    parser.add_argument("--train", action="store_true", help="Entraîner les modèles")
    parser.add_argument("--predict", action="store_true", help="Générer des prédictions")
    parser.add_argument("--all", action="store_true", help="Exécuter tout le pipeline")
    args = parser.parse_args()

    # Changer le répertoire de travail
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        if args.all or args.clean:
            print("Nettoyage des données...")
            subprocess.run(["python", "scripts/01_data_cleaning.py"], check=True)

        if args.all or args.train:
            print("Entraînement des modèles...")
            subprocess.run(["python", "scripts/02_train_models.py"], check=True)

        if args.all or args.predict:
            print("Génération des prédictions...")
            subprocess.run(["python", "scripts/03_make_predictions.py"], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution du script : {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
