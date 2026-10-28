/**
 * Netlify Serverless Function : Pont sécurisé vers MongoDB Atlas
 * Permet au front-end PWA d'interroger la base sans exposer MONGODB_URI.
 */

const { MongoClient } = require("mongodb");

const uri = process.env.MONGODB_URI;
const dbName = process.env.MONGODB_DB_NAME || "matchday_db";

let cachedClient = null;

async function connectToDatabase() {
  if (cachedClient) {
    return cachedClient;
  }
  const client = new MongoClient(uri, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
  });
  await client.connect();
  cachedClient = client;
  return client;
}

exports.handler = async (event, context) => {
  context.callbackWaitsForEmptyEventLoop = false;

  const teamId = event.queryStringParameters.team || "525674_SENIOR_M1";

  if (!uri) {
    return {
      statusCode: 500,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ error: "MONGODB_URI non configurée sur Netlify" }),
    };
  }

  try {
    const client = await connectToDatabase();
    const db = client.db(dbName);

    // 1. Récupération de l'équipe
    const equipe = await db.collection("equipes").findOne({ _id: teamId });

    // 2. Récupération des licenciés (Anonymisés)
    const licencies = await db.collection("licencies")
      .find({ equipes_autorisees: "SENIOR_M1" })
      .project({ "identite.nom_affiche": 1, poste: 1, role_principal: 1 })
      .limit(30)
      .toArray();

    // 3. Récupération des sanctions actives
    const sanctions = await db.collection("sanctions")
      .find({
        equipe_id: teamId,
        "qualification_reglementaire.est_applicable_equipe_fanion": true,
        "cycle_discipline.statut": "ACTIF"
      })
      .sort({ date_match: -1 })
      .toArray();

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "public, s-maxage=120, stale-while-revalidate=300"
      },
      body: JSON.stringify({
        status: "success",
        equipe,
        licencies,
        sanctions,
        derniere_mise_a_jour: new Date().toISOString()
      }),
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ error: error.message }),
    };
  }
};
