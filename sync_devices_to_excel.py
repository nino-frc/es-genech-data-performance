"""
Script de Synchronisation Automatique : MongoDB Atlas -> registre_appareils_connectes.xlsx
- Interroge la base cloud MongoDB Atlas
- Récupère chaque session réelle enregistrée
- Ajoute dynamiquement chaque nouvel appareil dans l'Excel officiel
"""

import os
import pandas as pd
from datetime import datetime
from pymongo import MongoClient

BASE_DIR = os.path.dirname(__file__)
ENV_PATH = os.path.join(BASE_DIR, ".env")
EXCEL_PATH = os.path.join(BASE_DIR, "registre_appareils_connectes.xlsx")
CSV_PATH = os.path.join(BASE_DIR, "registre_appareils_anonymes.csv")

def sync_devices():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#") and "=" in line:
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

    mongo_uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB_NAME", "matchday_db")

    if not mongo_uri:
        print("Erreur: MONGODB_URI non trouvée.")
        return

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        coll = db["club_licenses"]

        rows = []
        for club in coll.find().sort("club_code", 1):
            club_nom = club.get("nom", "Club Inconnu")
            devices = club.get("devices", [])
            for d in devices:
                rows.append({
                    "Club Adhérent": club_nom,
                    "Code Support": d.get("support_code", "--"),
                    "Rôle Titulaire & Appareil": d.get("role_titulaire", d.get("alias", "Membre Staff")),
                    "Statut Accès": d.get("statut", "Actif"),
                    "Première Connexion": d.get("premiere_connexion", "--"),
                    "Dernière Activité": d.get("derniere_activite", "--"),
                    "Type Session": "Session Réelle Utilisateur"
                })

        if not rows:
            print("Aucun appareil connecté dans MongoDB.")
            df = pd.DataFrame(columns=[
                "Club Adhérent", "Code Support", "Rôle Titulaire & Appareil",
                "Statut Accès", "Première Connexion", "Dernière Activité", "Type Session"
            ])
        else:
            df = pd.DataFrame(rows)

        df.to_excel(EXCEL_PATH, index=False)
        print(f"[OK] Excel mis a jour : {len(rows)} appareil(s) reel(s) consigne(s) dans {EXCEL_PATH}")

        # Export CSV
        df.to_csv(CSV_PATH, sep=";", index=False, encoding="utf-8")
        print(f"[OK] CSV mis a jour : {CSV_PATH}")

    except Exception as e:
        print(f"Erreur de synchronisation : {e}")

if __name__ == "__main__":
    sync_devices()
