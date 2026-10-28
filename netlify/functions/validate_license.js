/**
 * Netlify Function : validate_license.js
 * Passerelle sécurisée d'authentification Club & Suivi des Accès Staff (Zéro Donnée Intrusive)
 * Supporte :
 * 1. Clé Super-Admin Master (Nino - Accès Global Tous Clubs)
 * 2. Attribution de rôle staff & Code Support (#GN-01, #SC-01...) pour identification immédiate
 * 3. Révocation et contrôle d'accès en temps réel
 */

const { MongoClient } = require("mongodb");

let cachedClient = null;

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
    serverSelectionTimeoutMS: 5000,
    family: 4
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
      // Nouvel accès staff avec code support personnalisé
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

    // Si Super-Admin Master : récupération de la liste complète des clubs
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
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        valid: false,
        message: "Erreur serveur base de données : " + error.message
      })
    };
  }
};
