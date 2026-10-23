import re

# 1. Update discipline_monitor.py
disc_path = 'C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/discipline_monitor.py'
with open(disc_path, 'r', encoding='utf-8') as f:
    disc_code = f.read()

disc_code = disc_code.replace('"REMI D.": "REMI DELOBEL",', '"REMI D.": "REMI DEFENIN",\n    "REMI DELOBEL": "REMI DEFENIN",')
with open(disc_path, 'w', encoding='utf-8') as f:
    f.write(disc_code)
print("Updated discipline_monitor.py")

# 2. Update scraper.py
scraper_path = 'C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/scraper.py'
with open(scraper_path, 'r', encoding='utf-8') as f:
    scraper_code = f.read()

# Fix current_team in scraper.py
old_comp = """        elif current_section == "COMPOSITION":
            if line.isdigit() and i + 1 < len(lines):
                num = int(line)
                name = lines[i + 1]
                if not name.isdigit() and name not in ["TITULAIRES", "REMPLAÇANTS", "REMPLACANTS", "DIRIGEANTS", "OFFICIELS", "ARBITRES"]:
                    team = "GENECH ES"
                    lineups.append({
                        "equipe": team,
                        "numero": num,
                        "joueur_nom": name,
                        "role": current_role
                    })
                    i += 1"""

new_comp = """        elif current_section == "COMPOSITION":
            if line in ["LIEU DE LA RENCONTRE", "DÉTAIL DE L'INSTALLATION", "DETAIL DE L'INSTALLATION", "OFFICIELS", "ARBITRES", "LA FÉDÉRATION", "LA FEDERATION"]:
                current_section = "FIN"
            elif line not in ["TITULAIRES", "TITULAIRE", "REMPLAÇANTS", "REMPLACANTS", "COMPOSITION"] and not line.isdigit() and len(line) > 3:
                if i + 1 < len(lines) and lines[i + 1] in ["TITULAIRES", "TITULAIRE", "REMPLAÇANTS", "REMPLACANTS"]:
                    current_team = line.strip().upper()
            
            if line.isdigit() and i + 1 < len(lines):
                num = int(line)
                name = lines[i + 1]
                if not name.isdigit() and name not in ["TITULAIRES", "REMPLAÇANTS", "REMPLACANTS", "DIRIGEANTS", "OFFICIELS", "ARBITRES"]:
                    team = current_team if 'current_team' in locals() and current_team else "GENECH ES"
                    from discipline_monitor import normalize_player_name
                    lineups.append({
                        "equipe": team,
                        "numero": num,
                        "joueur_nom": normalize_player_name(name),
                        "role": current_role
                    })
                    i += 1"""

if old_comp in scraper_code:
    scraper_code = scraper_code.replace(old_comp, new_comp)
    with open(scraper_path, 'w', encoding='utf-8') as f:
        f.write(scraper_code)
    print("Updated scraper.py")
else:
    print("old_comp not found in scraper.py, skipping replacement")

# 3. Update analytics.py
analytics_path = 'C:/Users/ninof/.gemini/antigravity/scratch/genech_data_performance/analytics.py'
with open(analytics_path, 'r', encoding='utf-8') as f:
    an_code = f.read()

# Replace export of dim_lineups.csv to be Genech only
an_code = an_code.replace(
    'df_lineups.to_csv(os.path.join(OUTPUT_DIR, "dim_lineups.csv"), index=False, encoding="utf-8-sig")',
    'df_lineups.to_csv(os.path.join(OUTPUT_DIR, "dim_lineups_tous_clubs.csv"), index=False, encoding="utf-8-sig")\n    df_lineups[df_lineups["equipe"].str.contains("GENECH", case=False, na=False)].to_csv(os.path.join(OUTPUT_DIR, "dim_lineups.csv"), index=False, encoding="utf-8-sig")'
)

with open(analytics_path, 'w', encoding='utf-8') as f:
    f.write(an_code)
print("Updated analytics.py")
