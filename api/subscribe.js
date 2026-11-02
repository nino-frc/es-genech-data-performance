// Vercel Serverless Function : api/subscribe.js
// Gère l'abonnement persistant (MongoDB Atlas) et la diffusion Web Push (Apple APNs & Google FCM)

const webpush = require('web-push');
const { MongoClient } = require('mongodb');
const fs = require('fs');
const path = require('path');

const VAPID_PUBLIC_KEY = process.env.VAPID_PUBLIC_KEY || 'BLgY9vcONVMN2C9JX7UVfI6tL_hxeTGMVEm5NdNPHNBWsMlf7xlA23ROwEsxN-qpuOtS6y0bAS_Rx2GX_xk5VHQ';
const VAPID_PRIVATE_KEY = process.env.VAPID_PRIVATE_KEY || 'OWLtDNDAKVy4B08VzCLCkmtmLaVOaQbfe1bic9jeBwM';
const VAPID_SUBJECT = 'mailto:nino.francois.contact@gmail.com';

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb+srv://ninofrancois02_db_user:nino@cluster0.h5rlbka.mongodb.net/?retryWrites=true&w=majority';
const DB_NAME = process.env.MONGODB_DB_NAME || 'matchday_db';

webpush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

const TMP_FILE = path.join('/tmp', 'matchday_push_subscriptions.json');
let memorySubs = [];
let cachedClient = null;

async function getMongoCollection() {
  try {
    if (!cachedClient) {
      cachedClient = new MongoClient(MONGODB_URI, {
        serverSelectionTimeoutMS: 5000,
        family: 4,
        maxPoolSize: 5
      });
      await cachedClient.connect();
    }
    return cachedClient.db(DB_NAME).collection('push_subscriptions');
  } catch (err) {
    console.warn('[Push] MongoDB indisponible, bascule sur mémoire locale :', err.message);
    return null;
  }
}

async function getAllSubscriptions() {
  const col = await getMongoCollection();
  if (col) {
    try {
      const docs = await col.find({}).toArray();
      if (docs && docs.length > 0) return docs;
    } catch (e) {
      console.warn('[Push] Erreur lecture MongoDB :', e.message);
    }
  }

  // Fallback /tmp et mémoire
  try {
    if (fs.existsSync(TMP_FILE)) {
      const fileData = JSON.parse(fs.readFileSync(TMP_FILE, 'utf8'));
      if (Array.isArray(fileData) && fileData.length > 0) return fileData;
    }
  } catch (e) {}

  return memorySubs;
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // 1. Consultation des abonnés
  if (req.method === 'GET') {
    const subs = await getAllSubscriptions();
    return res.status(200).json({ count: subs.length, success: true });
  }

  // 2. Traitement POST : Envoi (send) ou Abonnement (subscribe)
  if (req.method === 'POST') {
    const body = req.body || {};

    // ACTION : Envoi de notification push
    if (body.action === 'send' || req.query.send === 'true') {
      const { title, body: msgBody, url, targetClub } = body;
      const payload = JSON.stringify({
        title: title || 'MatchDay - Données actualisées ⚽',
        body: msgBody || 'Nouvelle mise à jour FFF prête sur votre appareil.',
        url: url || './',
        icon: './logo.png',
        badge: './logo.png'
      });

      const subs = await getAllSubscriptions();
      if (subs.length === 0) {
        return res.status(200).json({
          success: true,
          message: 'Aucun appareil abonné pour le moment',
          sent: 0
        });
      }

      const filteredSubs = targetClub
        ? subs.filter(s => s.clubCode === targetClub || s.clubCode === 'MASTER')
        : subs;

      let successCount = 0;
      let failCount = 0;
      const expired = [];

      const promises = filteredSubs.map(sub => {
        return webpush.sendNotification({
          endpoint: sub.endpoint,
          keys: sub.keys
        }, payload)
        .then(() => { successCount++; })
        .catch(err => {
          failCount++;
          if (err.statusCode === 410 || err.statusCode === 404) {
            expired.push(sub.endpoint);
          }
        });
      });

      await Promise.all(promises);

      // Nettoyage des abonnements expirés (désinstallations)
      if (expired.length > 0) {
        const col = await getMongoCollection();
        if (col) {
          try {
            await col.deleteMany({ endpoint: { $in: expired } });
          } catch (e) {}
        }
        memorySubs = memorySubs.filter(s => !expired.includes(s.endpoint));
      }

      return res.status(200).json({
        success: true,
        sent: successCount,
        failed: failCount,
        total: filteredSubs.length
      });
    }

    // ACTION : Enregistrement d'un nouvel abonnement (Téléphone ou Navigateur)
    const subscription = body.subscription;
    const clubCode = body.clubCode || 'GNCH';
    const role = body.role || 'STAFF';

    if (!subscription || !subscription.endpoint) {
      return res.status(400).json({ error: 'Subscription endpoint missing' });
    }

    const doc = {
      endpoint: subscription.endpoint,
      keys: subscription.keys,
      clubCode,
      role,
      updatedAt: new Date().toISOString()
    };

    // Sauvegarde persistante MongoDB Atlas
    const col = await getMongoCollection();
    let totalDevices = 1;
    if (col) {
      try {
        await col.updateOne(
          { endpoint: subscription.endpoint },
          { $set: doc },
          { upsert: true }
        );
        totalDevices = await col.countDocuments();
      } catch (err) {
        console.warn('[Push] Erreur écriture MongoDB :', err.message);
      }
    }

    // Mise à jour fallback
    memorySubs = memorySubs.filter(s => s.endpoint !== subscription.endpoint);
    memorySubs.push(doc);
    try {
      fs.writeFileSync(TMP_FILE, JSON.stringify(memorySubs, null, 2), 'utf8');
    } catch (e) {}

    return res.status(200).json({
      success: true,
      message: 'Abonnement Push sauvegardé avec succès dans MongoDB Atlas',
      totalDevices
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
};
