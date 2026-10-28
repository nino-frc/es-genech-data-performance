"""
license_manager.py
Gestionnaire officiel des Licences B2B SaaS MatchDay & Sessions Staff
- Clé Super-Admin Master (Nino - Accès Global Tous Clubs)
- Clés clubs haute entropie
- Identification nominative/par rôle sans données intrusives (Codes Support #GN-01, #GN-02...)
- Registre Excel B2B multi-onglets & exports CSV
- QR Codes d'activation
- Synchronisation MongoDB Atlas
"""

import os
import json
import secrets
import qrcode
from PIL import Image
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

APP_PROD_URL = "https://match-day-app.netlify.app"
QR_DIR = os.path.join(BASE_DIR, "public", "qr_codes")
LOGOS_DIR = os.path.join(BASE_DIR, "public", "logos")
os.makedirs(QR_DIR, exist_ok=True)
os.makedirs(LOGOS_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# Définition des Clubs et de la Clé Super-Admin Master
# --------------------------------------------------------------------------
CLUBS_DATA = [
    {
        "club_id": "MASTER_NINO",
        "club_code": "ROOT",
        "nom": "Master Direction (Nino)",
        "license_key": "MD-MASTER-NINO-2026",
        "statut": "Super-Admin (Accès Global)",
        "plan": "SUPER_ADMIN",
        "is_master": True,
        "date_emission": "2026-10-28",
        "contact_referent": "Nino François (Créateur SaaS & Analyste)",
        "logo_rel_path": "logo.png",
        "equipes_autorisees": [
            {"id": "SENIOR_M1", "nom": "ES Genech - Séniors A (R3)", "club_code": "GNCH"},
            {"id": "SENIOR_M3", "nom": "ES Genech - Séniors B (D2)", "club_code": "GNCH"},
            {"id": "SENIOR_F2", "nom": "ES Genech - Féminines", "club_code": "GNCH"},
            {"id": "U18_M1", "nom": "ES Genech - U19 / U18 (D1)", "club_code": "GNCH"},
            {"id": "500934_SENIOR_M1", "nom": "FC Seclin - Séniors A (R2)", "club_code": "SCLN"}
        ],
        "default_team": "SENIOR_M1",
        "appareils_actifs": [
            {
                "device_id": "dev_master_nino",
                "support_code": "#ROOT-01",
                "role_titulaire": "Nino F. (Super-Admin / Direction SaaS)",
                "statut": "Actif",
                "premiere_connexion": "2026-10-28 09:00",
                "derniere_activite": "2026-10-28 13:30"
            }
        ]
    },
    {
        "club_id": "525674",
        "club_code": "GNCH",
        "nom": "ES Genech",
        "license_key": "MD-GNCH-88F4-A92B",
        "statut": "Partenaire Officiel VIP (Illimité)",
        "plan": "FULL_PRO",
        "is_master": False,
        "date_emission": "2026-10-28",
        "contact_referent": "Direction Technique ES Genech",
        "logo_rel_path": "logos/logo_genech.png",
        "equipes_autorisees": [
            {"id": "SENIOR_M1", "nom": "Séniors A (R3)"},
            {"id": "SENIOR_M3", "nom": "Séniors B (D2)"},
            {"id": "SENIOR_F2", "nom": "Féminines (Interdistrict)"},
            {"id": "U18_M1", "nom": "U19 / U18 (D1 & Gambardella)"}
        ],
        "default_team": "SENIOR_M1",
        "appareils_actifs": [
            {
                "device_id": "dev_gnch_c1",
                "support_code": "#GN-01",
                "role_titulaire": "Entraîneur Principal - Séniors A",
                "statut": "Actif",
                "premiere_connexion": "2026-10-28 10:15",
                "derniere_activite": "2026-10-28 13:10"
            },
            {
                "device_id": "dev_gnch_c2",
                "support_code": "#GN-02",
                "role_titulaire": "Entraîneur Adjoint & Préparateur",
                "statut": "Actif",
                "premiere_connexion": "2026-10-28 10:30",
                "derniere_activite": "2026-10-28 12:45"
            },
            {
                "device_id": "dev_gnch_c3",
                "support_code": "#GN-03",
                "role_titulaire": "Président & Comité Directeur",
                "statut": "Actif",
                "premiere_connexion": "2026-10-28 11:00",
                "derniere_activite": "2026-10-28 12:30"
            }
        ]
    },
    {
        "club_id": "500934",
        "club_code": "SCLN",
        "nom": "FC Seclin",
        "license_key": "MD-SCLN-74C2-91E3",
        "statut": "Version d'Évaluation (Bridée)",
        "plan": "TRIAL_BRIDEE",
        "is_master": False,
        "date_emission": "2026-10-28",
        "contact_referent": "Commission Sportive FC Seclin",
        "logo_rel_path": "logos/logo_seclin.jpg",
        "equipes_autorisees": [
            {"id": "500934_SENIOR_M1", "nom": "Séniors A (R2)"}
        ],
        "default_team": "500934_SENIOR_M1",
        "appareils_actifs": [
            {
                "device_id": "dev_scln_c1",
                "support_code": "#SC-01",
                "role_titulaire": "Coach Séniors A (Staff R2)",
                "statut": "Actif",
                "premiere_connexion": "2026-10-28 11:10",
                "derniere_activite": "2026-10-28 12:55"
            }
        ]
    },
    {
        "club_id": "500123",
        "club_code": "BNDS",
        "nom": "FC Bondues",
        "license_key": "MD-BNDS-55D1-82A4",
        "statut": "En attente (Devis Club)",
        "is_master": False,
        "date_emission": "2026-10-28",
        "contact_referent": "Pôle Performance Bondues",
        "logo_rel_path": "logo.png",
        "equipes_autorisees": [
            {"id": "SENIOR_M1", "nom": "Séniors A (R1)"}
        ],
        "default_team": "SENIOR_M1",
        "appareils_actifs": []
    }
]

def generate_qr_codes():
    """Génère les QR Codes d'activation"""
    print("\n--- 1. Génération des QR Codes Clubs ---")
    for club in CLUBS_DATA:
        activation_url = f"{APP_PROD_URL}/?key={club['license_key']}"
        club['activation_url'] = activation_url
        qr_filename = f"qr_{club['club_code'].lower()}.png"
        qr_path = os.path.join(QR_DIR, qr_filename)
        club['qr_file'] = qr_filename

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )
        qr.add_data(activation_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0a1728", back_color="#ffffff").convert('RGB')
        img.save(qr_path)
        print(f"[OK] QR Code genere pour {club['nom']}: {qr_filename} -> {activation_url}")

def export_excel_registry():
    """Génère le Registre Excel Officiel sans données intrusives, orienté Rôle et Support"""
    print("\n--- 2. Génération du Registre Excel B2B & Support ---")
    wb = openpyxl.Workbook()
    
    navy_fill = PatternFill(start_color="0A1728", end_color="0A1728", fill_type="solid")
    gold_fill = PatternFill(start_color="B45309", end_color="B45309", fill_type="solid")
    white_font_bold = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    master_row_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    green_font_bold = Font(name="Segoe UI", size=10, bold=True, color="15803D")
    standard_font = Font(name="Segoe UI", size=10)
    border_thin = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    # ----------------------------------------------------
    # FEUILLE 1 : Licences Clubs & Clé Master
    # ----------------------------------------------------
    ws1 = wb.active
    ws1.title = "Licences Clubs"
    ws1.views.sheetView[0].showGridLines = True

    headers1 = [
        "Nom de l'Espace / Club", "N° FFF / Réf", "Clé de Licence Cryptographique",
        "Type de Licence", "Comptes Staff Actifs", "Date Émission",
        "Lien Direct d'Activation PWA", "Fichier QR Code"
    ]
    ws1.append(headers1)
    for col_num in range(1, len(headers1) + 1):
        cell = ws1.cell(row=1, column=col_num)
        cell.fill = navy_fill
        cell.font = white_font_bold
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for row_idx, club in enumerate(CLUBS_DATA, start=2):
        is_master = club.get("is_master", False)
        row_data = [
            club["nom"],
            club["club_id"],
            club["license_key"],
            club["statut"],
            len(club["appareils_actifs"]),
            club["date_emission"],
            club["activation_url"],
            club["qr_file"]
        ]
        ws1.append(row_data)
        for col_num in range(1, len(headers1) + 1):
            c = ws1.cell(row=row_idx, column=col_num)
            c.font = standard_font
            c.border = border_thin
            if is_master:
                c.fill = master_row_fill
            elif row_idx % 2 == 1:
                c.fill = zebra_fill
            if col_num in (2, 3, 4, 5, 6, 8):
                c.alignment = Alignment(horizontal="center", vertical="center")
            if col_num == 3:
                c.font = Font(name="Consolas", size=11, bold=True, color="B45309" if is_master else "0A1728")
            if col_num == 4 and "Actif" in club["statut"]:
                c.font = green_font_bold

    for col in ws1.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws1.column_dimensions[col_letter].width = max(max_len + 4, 14)

    # ----------------------------------------------------
    # FEUILLE 2 : Accès Staff & Codes Support (Zéro Donnée Intrusive)
    # ----------------------------------------------------
    ws2 = wb.create_sheet(title="Accès Staff & Support")
    ws2.views.sheetView[0].showGridLines = True

    headers2 = [
        "Club Partenaire", "Code Support Staff", "Rôle / Titulaire Déclaré",
        "Statut Accès", "Première Connexion", "Dernière Activité",
        "Comment Nino Identifie en Support"
    ]
    ws2.append(headers2)
    for col_num in range(1, len(headers2) + 1):
        cell = ws2.cell(row=1, column=col_num)
        cell.fill = navy_fill
        cell.font = white_font_bold
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    row_idx2 = 2
    for club in CLUBS_DATA:
        for dev in club["appareils_actifs"]:
            is_master = club.get("is_master", False)
            row_data2 = [
                club["nom"],
                dev["support_code"],
                dev["role_titulaire"],
                dev["statut"],
                dev["premiere_connexion"],
                dev["derniere_activite"],
                f"Si problème, le coach donne {dev['support_code']} à Nino"
            ]
            ws2.append(row_data2)
            for col_num in range(1, len(headers2) + 1):
                c = ws2.cell(row=row_idx2, column=col_num)
                c.font = standard_font
                c.border = border_thin
                if is_master:
                    c.fill = master_row_fill
                elif row_idx2 % 2 == 1:
                    c.fill = zebra_fill
                if col_num in (2, 4, 5, 6):
                    c.alignment = Alignment(horizontal="center", vertical="center")
                if col_num == 2:
                    c.font = Font(name="Consolas", size=11, bold=True, color="15803D" if not is_master else "B45309")
                if col_num == 3:
                    c.font = Font(name="Segoe UI", size=10, bold=True)
                if col_num == 4:
                    c.font = green_font_bold
            row_idx2 += 1

    for col in ws2.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws2.column_dimensions[col_letter].width = max(max_len + 4, 15)

    excel_path = os.path.join(BASE_DIR, "registre_licences_clubs.xlsx")
    wb.save(excel_path)
    print(f"[OK] Registre Excel B2B mis a jour : {excel_path}")

    # Export CSV Licences
    csv_licences = os.path.join(BASE_DIR, "registre_licences_clubs.csv")
    df1 = pd.DataFrame([
        {
            "Club": c["nom"],
            "Code_FFF": c["club_id"],
            "Cle_Licence": c["license_key"],
            "Statut": c["statut"],
            "Nb_Comptes_Staff": len(c["appareils_actifs"]),
            "Lien_Activation": c["activation_url"],
            "Fichier_QR": c["qr_file"]
        } for c in CLUBS_DATA
    ])
    df1.to_csv(csv_licences, index=False, encoding="utf-8-sig", sep=";")
    print(f"[OK] Registre CSV Licences mis a jour : {csv_licences}")

    # Export CSV Staff & Support
    csv_devices = os.path.join(BASE_DIR, "registre_appareils_anonymes.csv")
    devices_list = []
    for c in CLUBS_DATA:
        for d in c["appareils_actifs"]:
            devices_list.append({
                "Club": c["nom"],
                "Code_Support": d["support_code"],
                "Role_Titulaire": d["role_titulaire"],
                "Statut": d["statut"],
                "Premiere_Connexion": d["premiere_connexion"],
                "Derniere_Activite": d["derniere_activite"]
            })
    df2 = pd.DataFrame(devices_list)
    df2.to_csv(csv_devices, index=False, encoding="utf-8-sig", sep=";")
    print(f"[OK] Registre CSV Staff mis a jour : {csv_devices}")

def sync_mongodb_licenses():
    """Synchronise les licences et accès staff dans MongoDB Atlas"""
    print("\n--- 3. Synchronisation MongoDB Atlas ---")
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME", "matchday_db")
    if not mongo_uri:
        print("[AVERTISSEMENT] MONGODB_URI non renseigne, passage.")
        return

    try:
        import pymongo
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        coll = db["club_licenses"]

        coll.create_index("license_key", unique=True)
        coll.create_index("club_id")

        for club in CLUBS_DATA:
            doc = {
                "_id": club["club_id"],
                "club_id": club["club_id"],
                "club_code": club["club_code"],
                "nom": club["nom"],
                "license_key": club["license_key"],
                "statut": club["statut"],
                "plan": club.get("plan", "FULL_PRO"),
                "is_master": club.get("is_master", False),
                "date_emission": club["date_emission"],
                "logo_url": f"./{club['logo_rel_path']}",
                "equipes_autorisees": club["equipes_autorisees"],
                "default_team": club["default_team"],
                "activation_url": club.get("activation_url"),
                "devices": club["appareils_actifs"],
                "derniere_synchronisation": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            coll.replace_one({"_id": club["club_id"]}, doc, upsert=True)
            print(f"[OK] Licence {club['nom']} ({club['license_key']}) synchronisee sur MongoDB Atlas !")

        client.close()
    except Exception as e:
        print(f"[ERREUR] Sync MongoDB: {e}")

def export_client_licenses_js():
    """Génère public/licenses_registry.js pour fonctionnement hors-ligne / PWA garanti"""
    print("\n--- 4. Generation public/licenses_registry.js (Garantie Offline PWA) ---")
    output_path = os.path.join(BASE_DIR, "public", "licenses_registry.js")
    
    registry = {}
    for club in CLUBS_DATA:
        registry[club["license_key"]] = {
            "club_id": club["club_id"],
            "club_code": club["club_code"],
            "nom": club["nom"],
            "logo_url": f"./{club['logo_rel_path']}",
            "statut": club["statut"],
            "plan": club.get("plan", "FULL_PRO"),
            "is_master": club.get("is_master", False),
            "equipes_autorisees": club["equipes_autorisees"],
            "default_team": club["default_team"],
            "devices": club["appareils_actifs"]
        }

    js_content = f"// Registre PWA autonome MatchDay\nwindow.MATCHDAY_LICENSES = {json.dumps(registry, ensure_ascii=False, indent=2)};\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"[OK] Registre PWA client cree : {output_path}")

if __name__ == "__main__":
    generate_qr_codes()
    export_excel_registry()
    sync_mongodb_licenses()
    export_client_licenses_js()
    print("\n[OK] Gestionnaire de licences execute avec succes !")
