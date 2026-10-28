import os

send_path = os.path.join(os.path.dirname(__file__), "send_email_report.py")
with open(send_path, "r", encoding="utf-8") as f:
    c = f.read()

target = "FROM matchs WHERE statut = 'A_VENIR' AND equipe_club_id = 'SENIOR_M1' AND (equipe_domicile LIKE '%GENECH%' OR equipe_exterieur LIKE '%GENECH%')"
replacement = "FROM matchs WHERE statut = 'A_VENIR' AND equipe_club_id = 'SENIOR_M1' AND date_heure >= date('now', '-1 day') AND (equipe_domicile LIKE '%GENECH%' OR equipe_exterieur LIKE '%GENECH%')"

if target in c:
    c = c.replace(target, replacement)
    with open(send_path, "w", encoding="utf-8") as f:
        f.write(c)
    print("send_email_report.py mis à jour avec vérification de date >= now !")
else:
    print("Notice: target non trouvée ou déjà modifiée.")
