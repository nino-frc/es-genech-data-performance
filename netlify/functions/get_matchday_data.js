/**
 * Netlify Function (Serverless Node.js) : get_matchday_data.js
 * Passerelle sécurisée vers MongoDB Atlas (Zero Secret côté Client)
 */

const { MongoClient } = require("mongodb");

const uri = process.env.MONGODB_URI;
const dbName = process.env.MONGODB_DB_NAME || "matchday_db";

// Réutilisation du pool de connexion entre les invocations chaudes (Serverless optimization)
let cachedClient = null;

async function connectToMongo() {
  if (cachedClient) {
    return cachedClient;
  }
  const client = new MongoClient(uri, {
    maxPoolSize: 10,
    serverSelectionTimeoutMS: 5000,
  });
  await client.connect();
  cachedClient = client;
  return client;
}

exports.handler = async (event, context) => {
  // Indique à Node.js de fermer la réponse sans attendre que l'event loop soit vide
  context.callbackWaitsForEmptyEventLoop = false;

  // Headers de sécurité et CORS
  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Cache-Control": "public, s-maxage=60, stale-while-revalidate=180"
  };

  // Gestion des requêtes OPTIONS (pre-flight CORS)
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers, body: "" };
  }

  if (!uri) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        status: "error",
        message: "Variable d'environnement MONGODB_URI non configurée sur Netlify."
      }),
    };
  }

  // 1. Extraction et validation du token d'URL
  const queryTeam = (event.queryStringParameters && event.queryStringParameters.team) || "genech";
  
  let teamId = "525674_SENIOR_M1";
  let clubId = "525674";

  const q = queryTeam.toLowerCase();
  if (q.includes("u18") || q.includes("u19")) {
    teamId = "525674_U18_M1";
  } else if (q.includes("fem") || q.includes("f2")) {
    teamId = "525674_SENIOR_F2";
  } else if (q.includes("m2") || q.includes("m3") || q.includes("reserve") || q.includes("senior_b")) {
    teamId = "525674_SENIOR_M2";
  } else if (q.includes("seclin")) {
    teamId = "500934_SENIOR_M1";
    clubId = "500934";
  }

  try {
    const client = await connectToMongo();
    const db = client.db(dbName);

    // 2. Interrogation des 3 collections
    // Collection A : 'equipes'
    const equipe = await db.collection("equipes").findOne({ _id: teamId });

    // Collection B : 'licencies' (RGPD : seuls les noms anonymisés et rôles sont servis)
    const licencies = await db.collection("licencies")
      .find({ club_id: clubId })
      .project({
        "_id": 1,
        "identite.nom_affiche": 1,
        "role_principal": 1,
        "categorie_age": 1,
        "equipes_autorisees": 1
      })
      .limit(50)
      .toArray();

    // Collection C : 'sanctions' (Strictement qualifiées pour l'équipe)
    const sanctions = await db.collection("sanctions")
      .find({
        equipe_id: teamId,
        "qualification_reglementaire.est_applicable_equipe_fanion": true
      })
      .sort({ date_match: -1 })
      .limit(40)
      .toArray();

    // 3. Réponse JSON propre et sécurisée
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        status: "success",
        token_consulte: queryTeam,
        equipe: equipe || { nom_affiche: "ES Genech", code_equipe: "SENIOR_M1" },
        nb_licencies: licencies.length,
        licencies: licencies,
        nb_sanctions: sanctions.length,
        sanctions: sanctions,
        derniere_interrogation: new Date().toISOString()
      }),
    };

  } catch (error) {
    console.error("[Netlify Function Error] :", error);
    return {
      statusCode: 502,
      headers,
      body: JSON.stringify({
        status: "error",
        message: "Base de données MongoDB Atlas temporairement injoignable.",
        details: error.message
      }),
    };
  }
};
