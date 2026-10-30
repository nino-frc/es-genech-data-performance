// Vercel Serverless Function : api/send-push.js
// Diffuse automatiquement la notification Web Push vers Apple (iOS PWA) & Google (Android)

const webpush = require('web-push');
const fs = require('fs');
const path = require('path');

const VAPID_PUBLIC_KEY = process.env.VAPID_PUBLIC_KEY || 'BLgY9vcONVMN2C9JX7UVfI6tL_hxeTGMVEm5NdNPHNBWsMlf7xlA23ROwEsxN-qpuOtS6y0bAS_Rx2GX_xk5VHQ';
const VAPID_PRIVATE_KEY = process.env.VAPID_PRIVATE_KEY || 'OWLtDNDAKVy4B08VzCLCkmtmLaVOaQbfe1bic9jeBwM';
const VAPID_SUBJECT = 'mailto:nino.francois.contact@gmail.com';

webpush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

const TMP_FILE = path.join('/tmp', 'matchday_push_subscriptions.json');

function getSubscriptions() {
  try {
    if (fs.existsSync(TMP_FILE)) {
      return JSON.parse(fs.readFileSync(TMP_FILE, 'utf8'));
    }
  } catch (e) {}
  return [];
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { title, body, url, targetClub } = req.body || {};

  const payload = JSON.stringify({
    title: title || 'MatchDay - Données actualisées ⚽',
    body: body || 'Nouvelle mise à jour FFF prête sur votre appareil.',
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

  const pushPromises = filteredSubs.map(sub => {
    return webpush.sendNotification({
      endpoint: sub.endpoint,
      keys: sub.keys
    }, payload)
    .then(() => {
      successCount++;
    })
    .catch(err => {
      failCount++;
      // Si l'endpoint a expiré (code 410 Gone ou 404), on peut l'ignorer
    });
  });

  await Promise.all(pushPromises);

  return res.status(200).json({
    success: true,
    sent: successCount,
    failed: failCount,
    total: filteredSubs.length
  });
};
