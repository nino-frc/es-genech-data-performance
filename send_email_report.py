"""
Module d'Expédition Automatique d'E-mails avec Pièces Jointes PDF/PNG
ES Genech Data Performance Pipeline
Envoi sécurisé via Gmail SMTP (SSL/TLS)
"""

import os
import sys
import smtplib
import sqlite3
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "genech_performance.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "briefings_coach")

GMAIL_USER = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "").strip() or GMAIL_USER

def send_report_email(mode: str = None):
    # Mode auto-détecté si non renseigné (lundi = debrief, autres = briefing)
    weekday = datetime.now().weekday() # 0 = Lundi, 4 = Vendredi
    if mode is None:
        mode = "monday" if weekday == 0 else "friday"

    print(f"--- PRÉPARATION DE L'ENVOI E-MAIL (MODE : {mode.upper()}) ---")
    print(f"  Configuration : GMAIL_USER={'Configuré (' + GMAIL_USER + ')' if GMAIL_USER else 'NON DÉFINI'}")
    print(f"  Configuration : GMAIL_APP_PASSWORD={'Configuré (longueur: ' + str(len(GMAIL_APP_PASSWORD)) + ' chars)' if GMAIL_APP_PASSWORD else 'NON DÉFINI'}")
    print(f"  Configuration : RECIPIENT_EMAIL={RECIPIENT_EMAIL if RECIPIENT_EMAIL else 'NON DÉFINI'}")

    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise ValueError(
            "⚠️ Les secrets GMAIL_USER ou GMAIL_APP_PASSWORD ne sont pas configurés dans GitHub Secrets !\n"
            "Vérifiez dans GitHub Settings > Secrets and variables > Actions que GMAIL_USER et GMAIL_APP_PASSWORD existent exactement avec ces noms."
        )

    # Connexion DB pour enrichir le sujet et le corps du mail
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    SELECT tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur, score_domicile, score_exterieur 
    FROM matchs WHERE statut = 'TERMINE' AND (equipe_domicile LIKE '%GENECH%' OR equipe_exterieur LIKE '%GENECH%')
    ORDER BY date_heure DESC LIMIT 1;
    """)
    last_match = cur.fetchone()

    cur.execute("""
    SELECT tour_ou_journee, date_heure, equipe_domicile, equipe_exterieur 
    FROM matchs WHERE statut = 'A_VENIR' AND (equipe_domicile LIKE '%GENECH%' OR equipe_exterieur LIKE '%GENECH%')
    ORDER BY date_heure ASC LIMIT 1;
    """)
    next_match = cur.fetchone()
    conn.close()

    msg = MIMEMultipart()
    msg['From'] = f"ES Genech Data Performance <{GMAIL_USER}>"
    msg['To'] = RECIPIENT_EMAIL

    attachments = []

    if mode == "monday":
        last_score = f"{last_match[2]} {int(last_match[4])} - {int(last_match[5])} {last_match[3]}" if last_match else "Score en cours"
        msg['Subject'] = f"📊 [ES Genech] Débrief du Matchday ({last_score}) + Cartes Joueurs & Rapport Comité"

        body_html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; color: #0a1728; padding: 20px;">
            <div style="max-width: 650px; background: white; margin: 0 auto; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <div style="background: #0a1728; padding: 20px 24px; border-bottom: 4px solid #ebb837; color: white;">
                    <h1 style="margin: 0; font-size: 22px; text-transform: uppercase;">ES <span style="color: #ebb837;">GENECH</span> • DÉBRIEF DU LUNDI</h1>
                    <p style="margin: 5px 0 0 0; font-size: 13px; color: #cbd5e1;">Rapport de performance hebdomadaire & Livrables staff</p>
                </div>
                
                <div style="padding: 24px;">
                    <div style="background: #f1f5f9; border-radius: 8px; padding: 14px 18px; border-left: 5px solid #15803d; margin-bottom: 20px;">
                        <div style="font-size: 11px; font-weight: 800; color: #64748b; text-transform: uppercase;">Dernier Match Disputé</div>
                        <div style="font-size: 18px; font-weight: bold; color: #0a1728; margin-top: 3px;">{last_score}</div>
                    </div>

                    <p style="font-size: 14px; line-height: 1.5; color: #334155;">
                        Bonjour Nino,<br><br>
                        Voici tes livrables automatisés pour le débriefing du match du week-end et la gouvernance du club.
                    </p>

                    <h3 style="font-size: 15px; color: #0a1728; border-bottom: 2px solid #ebb837; padding-bottom: 5px; margin-top: 20px;">📎 3 Documents PDF joints à ce mail :</h3>
                    <ul style="font-size: 13.5px; line-height: 1.6; color: #334155;">
                        <li><strong>1. Débrief Post-Match (Timeline 90') :</strong> Déroulé officiel minute par minute, faits marquants et notes du match.</li>
                        <li><strong>2. Cartes de Profil Joueurs :</strong> Notes <em>ESG Impact Score</em> (0-100), volume de jeu et suivi disciplinaire FFF.</li>
                        <li><strong>3. Rapport Exécutif Mensuel :</strong> Synthèse stratégique et budgétaire pour le Président et le Comité Directeur.</li>
                    </ul>

                    <div style="background: #eff6ff; border-radius: 8px; padding: 12px 16px; border-left: 4px solid #004687; margin-top: 25px; font-size: 12.5px; color: #1e3a8a;">
                        💡 <strong>Astuce Mobile :</strong> Les fichiers PDF et images joints sont directement au format smartphone (1080x1920) et peuvent être transférés tels quels au coach ou au président sur WhatsApp.
                    </div>
                </div>

                <div style="background: #0a1728; padding: 12px 24px; text-align: center; color: #ebb837; font-size: 12px; font-weight: bold; letter-spacing: 1px;">
                    TOUJOURS ENSEMBLE • ALLEZ L'ESG
                </div>
            </div>
        </body>
        </html>
        """

        # Fichiers à joindre
        files_to_attach = [
            "debrief_match_latest.pdf",
            "cartes_profil_joueurs.pdf",
            "rapport_executif_mensuel.pdf",
            "debrief_match_latest.png"
        ]
        for f in files_to_attach:
            path = os.path.join(OUTPUT_DIR, f)
            if os.path.exists(path):
                attachments.append(path)

    else: # Friday (Pre-match briefing)
        next_affiche = f"{next_match[2]} vs {next_match[3]} ({next_match[0]})" if next_match else "Prochain match"
        msg['Subject'] = f"⚽ [ES Genech] Briefing d'Avant-Match — {next_affiche}"

        body_html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; color: #0a1728; padding: 20px;">
            <div style="max-width: 650px; background: white; margin: 0 auto; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <div style="background: #0a1728; padding: 20px 24px; border-bottom: 4px solid #ebb837; color: white;">
                    <h1 style="margin: 0; font-size: 22px; text-transform: uppercase;">ES <span style="color: #ebb837;">GENECH</span> • BRIEFING DU VENDREDI</h1>
                    <p style="margin: 5px 0 0 0; font-size: 13px; color: #cbd5e1;">Espionnage Tactique, Météo & Consignes du Week-End</p>
                </div>
                
                <div style="padding: 24px;">
                    <div style="background: #fff7ed; border-radius: 8px; padding: 14px 18px; border-left: 5px solid #e8590c; margin-bottom: 20px;">
                        <div style="font-size: 11px; font-weight: 800; color: #9a3412; text-transform: uppercase;">Affiche du Match</div>
                        <div style="font-size: 18px; font-weight: bold; color: #0a1728; margin-top: 3px;">{next_affiche}</div>
                    </div>

                    <p style="font-size: 14px; line-height: 1.5; color: #334155;">
                        Bonjour Nino,<br><br>
                        Voici la fiche tactique d'avant-match prête pour la séance d'entraînement de ce vendredi soir et la causerie de dimanche.
                    </p>

                    <h3 style="font-size: 15px; color: #0a1728; border-bottom: 2px solid #ebb837; padding-bottom: 5px; margin-top: 20px;">🔍 Points Clés intégrés dans le document :</h3>
                    <ul style="font-size: 13.5px; line-height: 1.6; color: #334155;">
                        <li><strong>Espionnage de l'adversaire :</strong> Profil d'attaque, vulnérabilité après la 70e minute et alertes de suspension.</li>
                        <li><strong>Conditions de jeu :</strong> Météo exacte au coup d'envoi, force du vent et type de surface (pelouse/synthétique).</li>
                        <li><strong>Arbitre officiel :</strong> Indice de sévérité et consignes de discipline.</li>
                        <li><strong>Veille interne Genech :</strong> Joueurs sous sursis (Maxime Petit à 1 carton jaune de la suspension).</li>
                    </ul>
                </div>

                <div style="background: #0a1728; padding: 12px 24px; text-align: center; color: #ebb837; font-size: 12px; font-weight: bold; letter-spacing: 1px;">
                    TOUJOURS ENSEMBLE • ALLEZ L'ESG
                </div>
            </div>
        </body>
        </html>
        """

        files_to_attach = [
            "briefing_match_latest.pdf",
            "briefing_match_latest.png"
        ]
        for f in files_to_attach:
            path = os.path.join(OUTPUT_DIR, f)
            if os.path.exists(path):
                attachments.append(path)

    msg.attach(MIMEText(body_html, 'html'))

    # Ajout des pièces jointes
    for file_path in attachments:
        try:
            with open(file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
            msg.attach(part)
            print(f"  + Pièce jointe ajoutée : {os.path.basename(file_path)}")
        except Exception as e:
            print(f"  Erreur attachement {file_path}: {e}")

    # Envoi sécurisé via Gmail SMTP (port 465 SSL ou 587 TLS)
    try:
        print(f"Connexion au serveur SMTP Gmail (smtp.gmail.com) pour envoyer à {RECIPIENT_EMAIL}...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ E-mail envoyé avec succès à {RECIPIENT_EMAIL} avec {len(attachments)} pièce(s) jointe(s) !")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'e-mail : {e}")
        raise e

if __name__ == "__main__":
    mode_arg = sys.argv[1].lower() if len(sys.argv) > 1 else None
    send_report_email(mode_arg)
