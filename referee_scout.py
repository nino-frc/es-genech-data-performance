"""
Module de Scouting Arbitre (Referee Profile & Severity Index)
Analyse statistique des arbitres officiels désignés par la FFF
Aide à la causerie pour adapter le niveau d'agressivité et éviter les cartons bêtes
"""

import os
import sys
import sqlite3
import pandas as pd

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DB_PATH = os.path.join(os.path.dirname(__file__), "genech_performance.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "exports_powerbi")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Base de connaissances & historique des arbitres régionaux observés
REFEREES_DATABASE = {
    "LOUIS LAURENT": {
        "nom": "LOUIS LAURENT",
        "district": "Flandres / Côte d'Opale",
        "niveau": "Arbitre Régional R3 / CDF",
        "moyenne_jaunes_match": 4.5,
        "moyenne_rouges_match": 0.35,
        "style": "Sévère • Zéro tolérance sur contestations",
        "consigne": "Arbitre qui cartonne très vite sur les gestes d'humeur. Seul le capitaine doit lui adresser la parole."
    },
    "BENJAMIN D.": {
        "nom": "BENJAMIN D.",
        "district": "Flandres",
        "niveau": "Arbitre Régional R3",
        "moyenne_jaunes_match": 2.8,
        "moyenne_rouges_match": 0.10,
        "style": "Pédagogue • Laisse jouer les duels physiques",
        "consigne": "Met de l'impact dans les duels sans craindre la faute rapide, privilégie le dialogue."
    }
}

def scout_referee(referee_name: str = "LOUIS LAURENT"):
    ref_key = referee_name.strip().upper()
    
    # Recherche dans la base
    ref_info = REFEREES_DATABASE.get(ref_key)

    if not ref_info:
        # Valeurs régionales moyennes par défaut
        ref_info = {
            "nom": referee_name,
            "district": "Ligue Hauts-de-France",
            "niveau": "Arbitre Régional Officiel",
            "moyenne_jaunes_match": 3.4,
            "moyenne_rouges_match": 0.20,
            "style": "Profil Neutre / Standard R3",
            "consigne": "Rester rigoureux sur les replis défensifs et ne contester aucune décision arbitrale."
        }

    # Index de sévérité
    if ref_info["moyenne_jaunes_match"] >= 4.0:
        severite_label = "TRÈS ÉLEVÉE (Zéro Tolérance)"
        badge_color = "#b91c1c"
    elif ref_info["moyenne_jaunes_match"] >= 3.0:
        severite_label = "MODÉRÉE (Standard)"
        badge_color = "#ebb837"
    else:
        severite_label = "FAIBLE (Pédagogue)"
        badge_color = "#15803d"

    report = {
        "nom_arbitre": ref_info["nom"],
        "niveau": ref_info["niveau"],
        "severite": severite_label,
        "badge_color": badge_color,
        "moyenne_jaunes": ref_info["moyenne_jaunes_match"],
        "style": ref_info["style"],
        "consigne_coach": ref_info["consigne"]
    }

    print("\n" + "="*70)
    print("👨‍⚖️ PROFIL DE L'ARBITRE OFFICIEL DÉSIGNÉ")
    print("="*70)
    print(f"  • Nom               : {report['nom_arbitre']} ({report['niveau']})")
    print(f"  • Sévérité          : {report['severite']}")
    print(f"  • Moyenne Cartons   : {report['moyenne_jaunes']} cartons jaunes / match")
    print(f"  • Style Arbitrage   : {report['style']}")
    print(f"  • Consigne Joueurs  : {report['consigne_coach']}")
    print("="*70 + "\n")

    return report

if __name__ == "__main__":
    scout_referee("LOUIS LAURENT")
