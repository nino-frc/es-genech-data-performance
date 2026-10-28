"""
Module de fiabilisation, anonymisation et filtrage - MatchDay Analytics
Format d'anonymisation : 'Prénom N.' (ex: Julien D., Maxime P.)
Filtrage strict : Exclusion U18/Gambardella et Rôles Dirigeant/Banc
"""

import re
import os
import sqlite3
import pandas as pd
from typing import Optional, Dict, Any, Tuple

# -----------------------------------------------------------------------------
# 1. ANONYMISATION STRICTE : "Prénom N."
# -----------------------------------------------------------------------------

def anonymize_player_name(raw_name: Optional[str]) -> str:
    """
    Transforme n'importe quelle forme de nom brut en 'Prénom N.'
    Exemples :
    - 'JULIEN DEVERNAY' -> 'Julien D.'
    - 'ELIO DELCROIX'   -> 'Elio D.'
    - 'DANY DE FREITAS' -> 'Dany D.'
    - 'MAXIME PETIT'    -> 'Maxime P.'
    - 'JEAN PAUL BANGALA TOFIFI' -> 'Jean-Paul B.'
    """
    if not raw_name or not isinstance(raw_name, str):
        return "Inconnu X."

    clean = re.sub(r'[\(\)\[\]0-9]', '', raw_name).strip()
    clean = re.sub(r'\s+', ' ', clean)

    if not clean or clean.upper() in ["CSC", "INCONNU", "JOUEUR NON IDENTIFIE", "NON RENSEIGNE"]:
        return "Inconnu X."

    parts = clean.split(' ')

    # Si déjà au format "Prénom N." ou "PRENOM N."
    if len(parts) == 2 and (len(parts[1]) == 1 or (len(parts[1]) == 2 and parts[1].endswith('.'))):
        prenom = parts[0].capitalize()
        initiale = parts[1][0].upper()
        return f"{prenom} {initiale}."

    if len(parts) == 1:
        return f"{parts[0].capitalize()} X."

    # Gestion des prénoms composés courants
    compound_prefixes = ["JEAN", "MARC", "PIERRE", "PAUL", "ANNE", "MARIE"]
    if parts[0].upper() in compound_prefixes and len(parts) >= 3:
        prenom = f"{parts[0].capitalize()}-{parts[1].capitalize()}"
        nom_parts = parts[2:]
    else:
        prenom = parts[0].capitalize()
        nom_parts = parts[1:]

    # Première lettre du premier mot du nom de famille
    initiale = nom_parts[0][0].upper() if nom_parts and len(nom_parts[0]) > 0 else "X"
    return f"{prenom} {initiale}."


# -----------------------------------------------------------------------------
# 2. RÈGLES DE FILTRAGE STRICT CATEGORIES & RÔLES
# -----------------------------------------------------------------------------

STAFF_ROLES = [
    "DIRIGEANT", "ENTRAINEUR", "COACH", "STAFF", "MEDECIN", 
    "KINE", "BANC", "RESPONSABLE", "OFFICIEL", "ADJOINT"
]

NON_SENIOR_CATEGORIES = [
    "U18", "U17", "U16", "U15", "U14", "U13", "VETERANS", "GAMBARDELLA"
]

def is_first_team_eligible(
    event_dict: Dict[str, Any], 
    target_team_code: str = "SENIOR_M1"
) -> Tuple[bool, str]:
    """
    Contrôle d'éligibilité pour les statistiques et le tableau disciplinaire fanion.
    Rejette toute sanction concernant les jeunes ou le banc/staff.
    """
    competition = str(event_dict.get("competition_nom", "")).upper()
    equipe_nom = str(event_dict.get("equipe", "")).upper()
    role_acteur = str(event_dict.get("role_acteur", "JOUEUR")).upper()
    acteur_nom = str(event_dict.get("acteur_principal", "")).upper()
    detail = str(event_dict.get("detail", "")).upper()
    equipe_code = str(event_dict.get("equipe_code", target_team_code)).upper()

    # 1. Vérification Catégorie
    for cat in NON_SENIOR_CATEGORIES:
        if cat in competition or cat in detail:
            return False, f"Catégorie hors fanion ({cat})"

    # 2. Vérification Staff / Banc
    for staff in STAFF_ROLES:
        if staff in role_acteur or staff in detail or staff in acteur_nom:
            return False, f"Sanction non joueur ({staff})"

    return True, "OK"
