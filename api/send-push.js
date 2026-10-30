// Vercel Serverless Function : api/send-push.js
// Redirige vers le contrôleur unifié api/subscribe.js avec action: 'send'

const subscribeHandler = require('./subscribe');

module.exports = async (req, res) => {
  if (req.method === 'POST') {
    req.body = req.body || {};
    req.body.action = 'send';
  }
  return subscribeHandler(req, res);
};
