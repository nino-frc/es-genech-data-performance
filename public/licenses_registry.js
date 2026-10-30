// Registre PWA autonome MatchDay
window.MATCHDAY_LICENSES = {
  "MD-MASTER-NINO-2026": {
    "club_id": "MASTER_NINO",
    "club_code": "ROOT",
    "nom": "Master Direction (Nino)",
    "logo_url": "./logo.png",
    "statut": "Super-Admin (Accès Global)",
    "plan": "SUPER_ADMIN",
    "is_master": true,
    "equipes_autorisees": [
      {
        "id": "SENIOR_M1",
        "nom": "ES Genech - Séniors A (R3)",
        "club_code": "GNCH"
      },
      {
        "id": "SENIOR_M3",
        "nom": "ES Genech - Séniors B (D2)",
        "club_code": "GNCH"
      },
      {
        "id": "SENIOR_F2",
        "nom": "ES Genech - Féminines",
        "club_code": "GNCH"
      },
      {
        "id": "U18_M1",
        "nom": "ES Genech - U19 / U18 (D1)",
        "club_code": "GNCH"
      },
      {
        "id": "500934_SENIOR_M1",
        "nom": "FC Seclin - Séniors A (R2)",
        "club_code": "SCLN"
      },
      {
        "id": "500426_SENIOR_M1",
        "nom": "US Lesquin - Séniors A (R2)",
        "club_code": "LSQN"
      }
    ],
    "default_team": "SENIOR_M1",
    "devices": [
      {
        "device_id": "session-pc-windows-nino-01",
        "support_code": "#ROOT-01",
        "role_titulaire": "PC Windows (Session Principale)",
        "statut": "Actif",
        "premiere_connexion": "28/10/2026 à 09:00",
        "derniere_activite": "28/10/2026 à 18:10"
      }
    ]
  },
  "MD-GNCH-88F4-A92B": {
    "club_id": "525674",
    "club_code": "GNCH",
    "nom": "ES Genech",
    "logo_url": "./logos/logo_genech.png",
    "statut": "Partenaire Officiel VIP (Illimité)",
    "plan": "FULL_PRO",
    "is_master": false,
    "equipes_autorisees": [
      {
        "id": "SENIOR_M1",
        "nom": "Séniors A (R3)"
      },
      {
        "id": "SENIOR_M3",
        "nom": "Séniors B (D2)"
      },
      {
        "id": "SENIOR_F2",
        "nom": "Féminines (Interdistrict)"
      },
      {
        "id": "U18_M1",
        "nom": "U19 / U18 (D1 & Gambardella)"
      }
    ],
    "default_team": "SENIOR_M1",
    "devices": []
  },
  "MD-SCLN-74C2-91E3": {
    "club_id": "500934",
    "club_code": "SCLN",
    "nom": "FC Seclin",
    "logo_url": "./logos/logo_seclin.jpg",
    "statut": "Version d'Évaluation (Bridée)",
    "plan": "TRIAL_BRIDEE",
    "is_master": false,
    "equipes_autorisees": [
      {
        "id": "500934_SENIOR_M1",
        "nom": "Séniors A (R2)"
      }
    ],
    "default_team": "500934_SENIOR_M1",
    "devices": []
  },
  "MD-LSQN-92D3-71B8": {
    "club_id": "500426",
    "club_code": "LSQN",
    "nom": "US Lesquin",
    "logo_url": "./logos/logo_lesquin.jpg",
    "statut": "Version d'Évaluation (Bridée)",
    "plan": "TRIAL_BRIDEE",
    "is_master": false,
    "equipes_autorisees": [
      {
        "id": "500426_SENIOR_M1",
        "nom": "Séniors A (R2)"
      }
    ],
    "default_team": "500426_SENIOR_M1",
    "devices": []
  },
  "MD-BNDS-55D1-82A4": {
    "club_id": "500123",
    "club_code": "BNDS",
    "nom": "FC Bondues",
    "logo_url": "./logo.png",
    "statut": "En attente (Devis Club)",
    "plan": "FULL_PRO",
    "is_master": false,
    "equipes_autorisees": [
      {
        "id": "SENIOR_M1",
        "nom": "Séniors A (R1)"
      }
    ],
    "default_team": "SENIOR_M1",
    "devices": []
  }
};

// Aliases pratiques pour les accès directs et la rétrocompatibilité
window.MATCHDAY_LICENSES["MD-GNCH-2026-STAFF"] = window.MATCHDAY_LICENSES["MD-GNCH-88F4-A92B"];
window.MATCHDAY_LICENSES["MD-GENECH-2026"] = window.MATCHDAY_LICENSES["MD-GNCH-88F4-A92B"];
window.MATCHDAY_LICENSES["GENECH"] = window.MATCHDAY_LICENSES["MD-GNCH-88F4-A92B"];
window.MATCHDAY_LICENSES["MD-SCLN-2026-STAFF"] = window.MATCHDAY_LICENSES["MD-SCLN-74C2-91E3"];
window.MATCHDAY_LICENSES["SECLIN"] = window.MATCHDAY_LICENSES["MD-SCLN-74C2-91E3"];
window.MATCHDAY_LICENSES["MD-LSQN-2026-STAFF"] = window.MATCHDAY_LICENSES["MD-LSQN-92D3-71B8"];
window.MATCHDAY_LICENSES["LESQUIN"] = window.MATCHDAY_LICENSES["MD-LSQN-92D3-71B8"];
window.MATCHDAY_LICENSES["MASTER"] = window.MATCHDAY_LICENSES["MD-MASTER-NINO-2026"];
window.MATCHDAY_LICENSES["ROOT"] = window.MATCHDAY_LICENSES["MD-MASTER-NINO-2026"];

