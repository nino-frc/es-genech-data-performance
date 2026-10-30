// Vercel Serverless Function : api/subscribe.js
// Gère à la fois l'abonnement et la diffusion Web Push (Instance unifiée sans base externe)

const webpush = require('web-push');
const fs = require('fs');
const path = require('path');

const VAPID_PUBLIC_KEY = process.env.VAPID_PUBLIC_KEY || 'BLgY9vcONVMN2C9JX7UVfI6tL_hxeTGMVEm5NdNPHNBWsMlf7xlA23ROwEsxN-qpuOtS6y0bAS_Rx2GX_xk5VHQ';
const VAPID_PRIVATE_KEY = process.env.VAPID_PRIVATE_KEY || 'OWLtDNDAKVy4B08VzCLCkmtmLaVOaQbfe1bic9jeBwM';
const VAPID_SUBJECT = 'mailto:nino.francois.contact@gmail.com';

webpush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

const TMP_FILE = path.join('/tmp', 'matchday_push_subscriptions.json');

// Mémoire partagée de l'instance
let memorySubs = [];

function getSubscriptions() {
  try {
    if (fs.existsSync(TMP_FILE)) {
      const fileData = JSON.parse(fs.readFileSync(TMP_FILE, 'utf8'));
      if (Array.isArray(fileData) && fileData.length > 0) {
        memorySubs = fileData;
      }
    }
  } catch (e) {}
  return memorySubs;
}

function saveSubscriptions(subs) {
  memorySubs = subs;
  try {
    fs.writeFileSync(TMP_FILE, JSON.stringify(subs, null, 2), 'utf8');
  } catch (e) {}
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
    const subs = getSubscriptions();
    return res.status(200).json({ count: subs.length, success: true });
  }

  // 2. Traitement POST : soit Envoi (send), soit Abonnement (subscribe)
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

      const subs = getSubscriptions();
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

      if (expired.length > 0) {
        saveSubscriptions(subs.filter(s => !expired.includes(s.endpoint)));
      }

      return res.status(200).json({
        success: true,
        sent: successCount,
        failed: failCount,
        total: filteredSubs.length
      });
    }

    // ACTION : Enregistrement d'un nouvel abonnement
    const subscription = body.subscription;
    const clubCode = body.clubCode || 'GNCH';
    const role = body.role || 'STAFF';

    if (!subscription || !subscription.endpoint) {
      return res.status(400).json({ error: 'Subscription endpoint missing' });
    }

    let subs = getSubscriptions();
    subs = subs.filter(s => s.endpoint !== subscription.endpoint);
    subs.push({
      endpoint: subscription.endpoint,
      keys: subscription.keys,
      clubCode,
      role,
      updatedAt: new Date().toISOString()
    });

    saveSubscriptions(subs);

    return res.status(200).json({
      success: true,
      message: 'Abonnement Push enregistré avec succès',
      totalDevices: subs.length
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
};
