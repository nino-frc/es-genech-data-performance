"""
Simulateur Monte-Carlo Prédictif de Fin de Saison - Régional 3 Poule D
Méthodologie Scientifique & Régularisation Bayesienne (Empirical Bayes)
Projet ES Genech Data Performance - Portfolio SportTech
"""

import os
import random
import numpy as np
import pandas as pd

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "exports_powerbi")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Classement officiel R3 Poule D après J4
TEAMS_DATA = [
    {"equipe": "BEUVRY LA FORET AS", "pts": 10, "j": 4, "bp": 7, "bc": 3},
    {"equipe": "ANICHE SC",          "pts": 8,  "j": 4, "bp": 6, "bc": 3},
    {"equipe": "GENECH ES",          "pts": 8,  "j": 4, "bp": 6, "bc": 3},
    {"equipe": "HENIN BEAUMONT O.",  "pts": 7,  "j": 4, "bp": 5, "bc": 4},
    {"equipe": "ANSTAING CHERENG EC","pts": 6,  "j": 4, "bp": 5, "bc": 4},
    {"equipe": "BONDUES FC 2",       "pts": 6,  "j": 4, "bp": 5, "bc": 5},
    {"equipe": "VALENCIENNES SUMMER","pts": 6,  "j": 4, "bp": 4, "bc": 5},
    {"equipe": "MAUBEUGE US 2",      "pts": 5,  "j": 4, "bp": 4, "bc": 4},
    {"equipe": "BAVAY US",           "pts": 3,  "j": 4, "bp": 3, "bc": 5},
    {"equipe": "GUESNAIN SC",        "pts": 2,  "j": 4, "bp": 2, "bc": 6},
    {"equipe": "CYSOING WB EAC",     "pts": 1,  "j": 4, "bp": 2, "bc": 7},
    {"equipe": "AUBY US",            "pts": 0,  "j": 4, "bp": 1, "bc": 8},
]

# Matchs connus déjà joués (J1 à J4)
KNOWN_PLAYED = [
    ("BONDUES FC 2", "GENECH ES"),       # J1 : Bondues 1 - 2 Genech
    ("GENECH ES", "MAUBEUGE US 2"),      # J2 : Genech 2 - 0 Maubeuge
    ("GUESNAIN SC", "GENECH ES"),        # J3 : Guesnain 1 - 1 Genech
    ("GENECH ES", "ANSTAING CHERENG EC"),# J4 : Genech 1 - 1 Anstaing
    ("BEUVRY LA FORET AS", "GUESNAIN SC"),# J4
    ("BAVAY US", "ANICHE SC"),           # J4
]

def generate_balanced_remaining_fixtures(teams, seed=42):
    """
    Génère un calendrier cohérent où chaque équipe a exactement 18 matchs restants (108 matchs au total),
    en retirant les 24 matchs déjà joués (4 par équipe) du championnat aller-retour (132 matchs).
    """
    random.seed(seed)
    all_matches = [(h, a) for h in teams for a in teams if h != a]
    
    for _ in range(2000):
        counts = {t: 0 for t in teams}
        played = list(KNOWN_PLAYED)
        for h, a in played:
            counts[h] += 1
            counts[a] += 1
            
        candidates = [m for m in all_matches if m not in played and "GENECH ES" not in m]
        random.shuffle(candidates)
        
        for h, a in candidates:
            if counts[h] < 4 and counts[a] < 4:
                played.append((h, a))
                counts[h] += 1
                counts[a] += 1
                if len(played) == 24:
                    break
        if len(played) == 24 and all(c == 4 for c in counts.values()):
            remaining = [m for m in all_matches if m not in played]
            return remaining, played
            
    raise RuntimeError("Impossible de générer un calendrier équilibré.")

def run_monte_carlo(n_simulations=20000, seed=42):
    np.random.seed(seed)
    teams = [t["equipe"] for t in TEAMS_DATA]
    n_teams = len(teams)
    team_idx = {name: i for i, name in enumerate(teams)}
    
    init_pts = np.array([t["pts"] for t in TEAMS_DATA], dtype=float)
    
    # -------------------------------------------------------------
    # Régularisation Bayesienne (Empirical Bayes Shrinkage)
    # -------------------------------------------------------------
    # Évite les sur-estimations précoces (aucun faux espoir).
    # Prior w = 6 matchs pondéré sur la moyenne de R3 (1.37 PPM).
    prior_ppm = 1.37
    prior_weight = 6.0
    
    strengths = np.array([
        (t["pts"] + prior_weight * prior_ppm) / (t["j"] + prior_weight)
        for t in TEAMS_DATA
    ])
    strengths_centered = strengths - np.mean(strengths)
    
    # Calendrier équilibré de 108 matchs restants
    remaining_fixtures, _ = generate_balanced_remaining_fixtures(teams, seed=seed)
    n_fixtures = len(remaining_fixtures)
    
    # Probabilités logistiques ordonnées pour chaque confrontation
    home_advantage = 0.28
    temp = 0.70
    c1, c2 = -0.38, 0.42
    
    fixture_probs = []
    for h_name, a_name in remaining_fixtures:
        h = team_idx[h_name]
        a = team_idx[a_name]
        diff_strength = (strengths_centered[h] + home_advantage) - strengths_centered[a]
        z = diff_strength / temp
        
        p_away = 1.0 / (1.0 + np.exp(-(c1 - z)))
        p_home = 1.0 - (1.0 / (1.0 + np.exp(-(c2 - z))))
        p_draw = max(0.0, 1.0 - p_home - p_away)
        
        tot = p_home + p_draw + p_away
        fixture_probs.append((p_home / tot, p_draw / tot, p_away / tot))
        
    fixture_probs = np.array(fixture_probs)
    
    # Tirages aléatoires uniformes
    random_draws = np.random.uniform(0, 1, size=(n_simulations, n_fixtures))
    p_h = fixture_probs[:, 0]
    p_d = fixture_probs[:, 1]
    
    is_home_win = random_draws < p_h
    is_draw = (random_draws >= p_h) & (random_draws < (p_h + p_d))
    is_away_win = random_draws >= (p_h + p_d)
    
    points_sim = np.tile(init_pts, (n_simulations, 1))
    h_indices = np.array([team_idx[f[0]] for f in remaining_fixtures])
    a_indices = np.array([team_idx[f[1]] for f in remaining_fixtures])
    
    for f in range(n_fixtures):
        h, a = h_indices[f], a_indices[f]
        points_sim[:, h] += is_home_win[:, f] * 3 + is_draw[:, f] * 1
        points_sim[:, a] += is_away_win[:, f] * 3 + is_draw[:, f] * 1
        
    # Classements avec tirage au sort infinitesimal pour les ex-aequo
    noise = np.random.uniform(0, 1e-4, size=points_sim.shape)
    final_ranks = np.zeros((n_simulations, n_teams), dtype=int)
    for sim in range(n_simulations):
        order = np.argsort(-(points_sim[sim] + noise[sim]))
        for rank, pos in enumerate(order, start=1):
            final_ranks[sim, pos] = rank
            
    # Synthèse des résultats
    results_summary = []
    for i, t_name in enumerate(teams):
        pts_dist = points_sim[:, i]
        ranks_dist = final_ranks[:, i]
        
        results_summary.append({
            "equipe": t_name,
            "pts_actuels": int(init_pts[i]),
            "pts_mediane": float(np.median(pts_dist)),
            "pts_moyenne": round(float(np.mean(pts_dist)), 1),
            "pts_p10_pessimiste": float(np.percentile(pts_dist, 10)),
            "pts_p90_optimiste": float(np.percentile(pts_dist, 90)),
            "prob_champion_pct": round(np.mean(ranks_dist == 1) * 100, 1),
            "prob_podium_pct": round(np.mean(ranks_dist <= 3) * 100, 1),
            "prob_top5_pct": round(np.mean(ranks_dist <= 5) * 100, 1),
            "prob_relegation_pct": round(np.mean(ranks_dist >= 10) * 100, 1),
            "rang_moyen": round(float(np.mean(ranks_dist)), 1),
            "rang_mediane": int(np.median(ranks_dist))
        })
        
    df_results = pd.DataFrame(results_summary).sort_values(by="prob_champion_pct", ascending=False)
    
    genech_id = team_idx["GENECH ES"]
    genech_pts = points_sim[:, genech_id]
    genech_ranks = final_ranks[:, genech_id]
    champion_points = np.max(points_sim, axis=1)
    
    seuil_pts_titre_mediane = float(np.median(champion_points))
    seuil_pts_titre_p10 = float(np.percentile(champion_points, 10))
    seuil_pts_titre_p90 = float(np.percentile(champion_points, 90))
    
    print("\n" + "="*75)
    print("--- RESULTATS DU SIMULATEUR MONTE-CARLO R3 POULE D (20 000 ITERATIONS) ---")
    print("="*75)
    print(df_results.to_string(index=False))
    print("\n" + "-"*75)
    print("--- ANALYSE SCIENTIFIQUE ES GENECH (AUCUN FAUX ESPOIR) : ---")
    print(f"  * Probabilite de finir 1er (Montee directe en R2) : {np.mean(genech_ranks == 1)*100:.1f} %")
    print(f"  * Probabilite de finir sur le Podium (Top 3)      : {np.mean(genech_ranks <= 3)*100:.1f} %")
    print(f"  * Probabilite Top 5 (Haut de tableau)             : {np.mean(genech_ranks <= 5)*100:.1f} %")
    print(f"  * Risque de Descente / Relegation (Rang >= 10)    : {np.mean(genech_ranks >= 10)*100:.1f} %")
    print(f"  * Points projetes (Mediane)                       : {np.median(genech_pts):.0f} pts")
    print(f"  * Fourchette 80% [P10 Pessimiste - P90 Optimiste] : [{np.percentile(genech_pts, 10):.0f} - {np.percentile(genech_pts, 90):.0f}] pts")
    print(f"  * Seuil de points median requis pour le Titre     : {seuil_pts_titre_mediane:.0f} pts (fourchette : {seuil_pts_titre_p10:.0f} a {seuil_pts_titre_p90:.0f} pts)")
    print("="*75)
    
    # Exports CSV
    df_results.to_csv(os.path.join(OUTPUT_DIR, "dim_monte_carlo_projections.csv"), index=False, encoding="utf-8-sig")
    
    ranks_counts = pd.Series(genech_ranks).value_counts(normalize=True).sort_index().reset_index()
    ranks_counts.columns = ["rang_final", "probabilite_pct"]
    ranks_counts["probabilite_pct"] = (ranks_counts["probabilite_pct"] * 100).round(2)
    ranks_counts.to_csv(os.path.join(OUTPUT_DIR, "dim_genech_ranks_distribution.csv"), index=False, encoding="utf-8-sig")
    
    return df_results, seuil_pts_titre_mediane

if __name__ == "__main__":
    run_monte_carlo()
