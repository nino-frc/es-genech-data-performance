// Vercel Serverless Function : api/subscribe.js
// Enregistre l'abonnement Web Push d'un appareil (iPhone PWA / Android)

const fs = require('fs');
const path = require('path');

const TMP_FILE = path.join('/tmp', 'matchday_push_subscriptions.json');

function getLocalSubscriptions() {
  try {
    if (fs.existsSync(TMP_FILE)) {
      return JSON.parse(fs.readFileSync(TMP_FILE, 'utf8'));
    }
  } catch (e) {}
  return [];
}

function saveLocalSubscriptions(subs) {
  try {
    fs.writeFileSync(TMP_FILE, JSON.stringify(subs, null, 2), 'utf8');
  } catch (e) {}
}

module.exports = async (req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    const subs = getLocalSubscriptions();
    return res.status(200).json({ count: subs.length, success: true });
  }

  if (req.method === 'POST') {
    const body = req.body || {};
    const subscription = body.subscription;
    const clubCode = body.clubCode || 'GNCH';
    const role = body.role || 'STAFF';

    if (!subscription || !subscription.endpoint) {
      return res.status(400).json({ error: 'Subscription endpoint missing' });
    }

    let subs = getLocalSubscriptions();
    // Évite les doublons basés sur l'endpoint
    subs = subs.filter(s => s.endpoint !== subscription.endpoint);
    subs.push({
      endpoint: subscription.endpoint,
      keys: subscription.keys,
      clubCode,
      role,
      updatedAt: new Date().toISOString()
    });

    saveLocalSubscriptions(subs);

    return res.status(200).json({
      success: true,
      message: 'Abonnement Push enregistré avec succès',
      totalDevices: subs.length
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
};
