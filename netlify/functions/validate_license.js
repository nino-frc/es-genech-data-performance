/**
 * Netlify Function : validate_license.js
 * Passerelle sécurisée d'authentification Club & Suivi des Accès Staff (Zéro Donnée Intrusive)
 * Supporte :
 * 1. Clé Super-Admin Master (Nino - Accès Global Tous Clubs)
 * 2. Attribution de rôle staff & Code Support (#GN-01, #SC-01...) pour identification immédiate
 * 3. Révocation et contrôle d'accès en temps réel
 * 4. Fallback autonome si interruption réseau
 */

const { MongoClient } = require("mongodb");

let cachedClient = null;

const FALLBACK_LICENSES = {
  "MD-MASTER-NINO-2026": {
    club_id: "MASTER_NINO",
    club_code: "ROOT",
    nom: "Master Direction (Nino)",
    logo_url: "./logo.png",
    statut: "Super-Admin (Accès Global)",
    plan: "SUPER_ADMIN",
    is_master: true,
    equipes_autorisees: [
      { id: "SENIOR_M1", nom: "ES Genech - Séniors A (R3)", club_code: "GNCH" },
      { id: "SENIOR_M3", nom: "ES Genech - Séniors B (D2)", club_code: "GNCH" },
      { id: "SENIOR_F2", nom: "ES Genech - Féminines", club_code: "GNCH" },
      { id: "U18_M1", nom: "ES Genech - U19 / U18 (D1)", club_code: "GNCH" },
      { id: "500934_SENIOR_M1", nom: "FC Seclin - Séniors A (R2)", club_code: "SCLN" },
      { id: "500426_SENIOR_M1", nom: "US Lesquin - Séniors A (R2)", club_code: "LSQN" }
    ],
    default_team: "SENIOR_M1",
    devices: [
      {
        device_id: "session-pc-windows-nino-01",
        support_code: "#ROOT-01",
        role_titulaire: "PC Windows (Session Principale)",
        statut: "Actif",
        premiere_connexion: "28/10/2026 à 09:00",
        derniere_activite: "28/10/2026 à 18:10"
      }
    ]
  },
  "MD-GNCH-88F4-A92B": {
    club_id: "525674",
    club_code: "GNCH",
    nom: "ES Genech",
    logo_url: "./logos/logo_genech.png",
    statut: "Partenaire Officiel VIP (Illimité)",
    plan: "FULL_PRO",
    is_master: false,
    equipes_autorisees: [
      { id: "SENIOR_M1", nom: "Séniors A (R3)" },
      { id: "SENIOR_M3", nom: "Séniors B (D2)" },
      { id: "SENIOR_F2", nom: "Féminines (Interdistrict)" },
      { id: "U18_M1", nom: "U19 / U18 (D1 & Gambardella)" }
    ],
    default_team: "SENIOR_M1",
    devices: []
  },
  "MD-SCLN-74C2-91E3": {
    club_id: "500934",
    club_code: "SCLN",
    nom: "FC Seclin",
    logo_url: "./logos/logo_seclin.jpg",
    statut: "Version d'Évaluation (Bridée)",
    plan: "TRIAL_BRIDEE",
    is_master: false,
    equipes_autorisees: [
      { id: "500934_SENIOR_M1", nom: "Séniors A (R2)" }
    ],
    default_team: "500934_SENIOR_M1",
    devices: []
  },
  "MD-LSQN-92D3-71B8": {
    club_id: "500426",
    club_code: "LSQN",
    nom: "US Lesquin",
    logo_url: "./logos/logo_lesquin.jpg",
    statut: "Version d'Évaluation (Bridée)",
    plan: "TRIAL_BRIDEE",
    is_master: false,
    equipes_autorisees: [
      { id: "500426_SENIOR_M1", nom: "Séniors A (R2)" }
    ],
    default_team: "500426_SENIOR_M1",
    devices: []
  },
  "MD-BNDS-55D1-82A4": {
    club_id: "500123",
    club_code: "BNDS",
    nom: "FC Bondues",
    logo_url: "./logo.png",
    statut: "En attente (Devis Club)",
    plan: "FULL_PRO",
    is_master: false,
    equipes_autorisees: [
      { id: "SENIOR_M1", nom: "Séniors A (R1)" }
    ],
    default_team: "SENIOR_M1",
    devices: []
  }
};

async function connectToMongo() {
  if (cachedClient) {
    return cachedClient;
  }
  const uri = process.env.MONGODB_URI;
  if (!uri) {
    throw new Error("Variable d'environnement MONGODB_URI non configurée.");
  }
  const client = new MongoClient(uri, {
    maxPoolSize: 10,
    serverSelectionTimeoutMS: 4000
  });
  await client.connect();
  cachedClient = client;
  return client;
}

exports.handler = async (event, context) => {
  context.callbackWaitsForEmptyEventLoop = false;

  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers, body: "" };
  }

  let body = {};
  if (event.httpMethod === "POST") {
    try {
      body = JSON.parse(event.body || "{}");
    } catch (e) {
      body = {};
    }
  } else {
    body = event.queryStringParameters || {};
  }

  const licenseKey = (body.key || "").trim().toUpperCase();
  const deviceId = (body.device_id || "").trim();
  const roleTitulaire = (body.role_titulaire || body.alias || "").trim();
  const action = body.action || "validate";

  if (!licenseKey) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({
        valid: false,
        message: "Clé de licence obligatoire."
      })
    };
  }

  try {
    const client = await connectToMongo();
    const db = client.db(process.env.MONGODB_DB_NAME || "matchday_db");
    const coll = db.collection("club_licenses");

    const club = await coll.findOne({ license_key: licenseKey });

    if (!club) {
      return {
        statusCode: 401,
        headers,
        body: JSON.stringify({
          valid: false,
          message: "Clé de licence non reconnue ou désactivée."
        })
      };
    }

    const isMaster = club.is_master || licenseKey === "MD-MASTER-NINO-2026";
    const now = new Date();
    const nowStr = now.toLocaleDateString("fr-FR") + " " + now.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });

    let devices = Array.isArray(club.devices) ? club.devices : [];

    // Action : Révocation d'un accès par son device_id (Strictement réservé à la Licence Master Nino)
    if (action === "revoke_device" && body.target_device_id) {
      if (!isMaster) {
        return {
          statusCode: 403,
          headers,
          body: JSON.stringify({
            valid: false,
            message: "Action non autorisée. Seule la clé Super-Admin Master Nino peut révoquer des accès staff."
          })
        };
      }
      devices = devices.map(d => {
        if (d.device_id === body.target_device_id) {
          return { ...d, statut: "Révoqué" };
        }
        return d;
      });
      await coll.updateOne({ _id: club._id }, { $set: { devices: devices } });
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({ success: true, message: "Accès révoqué avec succès.", devices })
      };
    }

    // Action : Modification du rôle / titulaire
    if (action === "rename_device" && body.target_device_id && body.new_alias) {
      devices = devices.map(d => {
        if (d.device_id === body.target_device_id) {
          return { ...d, role_titulaire: body.new_alias.trim(), alias: body.new_alias.trim() };
        }
        return d;
      });
      await coll.updateOne({ _id: club._id }, { $set: { devices: devices } });
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({ success: true, message: "Profil mis à jour.", devices })
      };
    }

    // Action principale : Validation & Enregistrement
    let currentDevice = devices.find(d => d.device_id === deviceId);

    if (currentDevice) {
      if (currentDevice.statut === "Révoqué") {
        return {
          statusCode: 403,
          headers,
          body: JSON.stringify({
            valid: false,
            revoked: true,
            message: "Cet accès a été révoqué par la direction du club."
          })
        };
      }
      currentDevice.derniere_activite = nowStr;
      if (roleTitulaire && roleTitulaire !== currentDevice.role_titulaire) {
        currentDevice.role_titulaire = roleTitulaire;
      }
    } else if (deviceId) {
      const codePrefix = isMaster ? "ROOT" : (club.club_code || "STAFF");
      const nextNum = devices.length + 1;
      const formattedNum = nextNum < 10 ? `0${nextNum}` : `${nextNum}`;
      const supportCode = `#${codePrefix}-${formattedNum}`;

      currentDevice = {
        device_id: deviceId,
        support_code: supportCode,
        role_titulaire: roleTitulaire || `Membre Staff ${supportCode}`,
        statut: "Actif",
        premiere_connexion: nowStr,
        derniere_activite: nowStr
      };
      devices.push(currentDevice);
    }

    await coll.updateOne({ _id: club._id }, { $set: { devices: devices } });

    const activeDevicesCount = devices.filter(d => d.statut === "Actif").length;

    let allClubs = [];
    if (isMaster) {
      const allClubsDocs = await coll.find({ is_master: { $ne: true } }).toArray();
      allClubs = allClubsDocs.map(c => ({
        club_id: c.club_id,
        club_code: c.club_code,
        nom: c.nom,
        statut: c.statut,
        equipes_autorisees: c.equipes_autorisees,
        default_team: c.default_team,
        devices_count: Array.isArray(c.devices) ? c.devices.filter(d => d.statut === 'Actif').length : 0
      }));
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        valid: true,
        is_master: isMaster,
        club: {
          club_id: club.club_id,
          club_code: club.club_code,
          nom: club.nom,
          logo_url: club.logo_url || `./logos/logo_${club.club_code.toLowerCase()}.png`,
          statut: club.statut,
          plan: club.plan || (club.club_code === 'SCLN' ? 'TRIAL_BRIDEE' : 'FULL_PRO'),
          equipes_autorisees: club.equipes_autorisees,
          default_team: club.default_team || "SENIOR_M1"
        },
        all_clubs: allClubs,
        devices: devices,
        device_count: activeDevicesCount,
        current_device: currentDevice
      })
    };

  } catch (error) {
    // Fallback gracieux et résilient
    const fallbackClub = FALLBACK_LICENSES[licenseKey];
    if (fallbackClub) {
      const isMaster = fallbackClub.is_master || licenseKey === "MD-MASTER-NINO-2026";
      let devs = Array.isArray(fallbackClub.devices) ? fallbackClub.devices : [];
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          valid: true,
          is_master: isMaster,
          club: fallbackClub,
          devices: devs,
          device_count: devs.filter(d => d.statut === 'Actif').length,
          current_device: devs[0] || null
        })
      };
    }
    return {
      statusCode: 401,
      headers,
      body: JSON.stringify({
        valid: false,
        message: "Clé de licence non reconnue ou désactivée."
      })
    };
  }
};
