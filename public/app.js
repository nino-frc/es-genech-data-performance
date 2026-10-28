/**
 * MatchDay - Script Client PWA & Gestion Token
 */

// 1. Navigation Onglets Ergonomique
function switchTab(tabId, navElement) {
  // Masquer tous les onglets
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.style.display = 'none';
    tab.classList.remove('active');
  });

  // Afficher l'onglet sélectionné
  const target = document.getElementById(tabId);
  if (target) {
    target.style.display = 'block';
    target.classList.add('active');
  }

  // Mettre à jour l'état actif dans la barre basse
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
  });
  if (navElement) {
    navElement.classList.add('active');
  }
}

// 2. Gestion de l'Accès par Token d'URL
function initAppAuthAndRouting() {
  const urlParams = new URLSearchParams(window.location.search);
  const teamToken = urlParams.get('team') || urlParams.get('token');

  console.log("[MatchDay PWA] Token d'accès détecté :", teamToken || "Mode défaut (Genech VIP)");

  const teamPill = document.getElementById('activeClubName');
  const roleBadge = document.getElementById('appRoleBadge');

  if (teamToken === 'seclin-r2') {
    teamPill.textContent = "FC Seclin (R2)";
    roleBadge.textContent = "PRO";
    loadClubData("500934_SENIOR_M1");
  } else {
    // Par défaut : ES Genech VIP
    teamPill.textContent = "ES Genech (R3)";
    roleBadge.textContent = "VIP";
    loadClubData("525674_SENIOR_M1");
  }
}

// 3. Appel de l'API Serverless (Pont sécurisé MongoDB Atlas)
async function loadClubData(teamId) {
  try {
    const res = await fetch(`/.netlify/functions/get_team_data?team=${teamId}`);
    if (!res.ok) {
      console.warn("[API] Fonction serverless en attente de déploiement Netlify. Utilisation du cache local.");
      return;
    }
    const data = await res.json();
    console.log("[API] Données reçues depuis MongoDB Atlas :", data);
    // Mise à jour de l'UI avec les données fraîches...
  } catch (err) {
    console.log("[PWA] Mode autonome actif. Les données pré-chargées restent affichées.");
  }
}

// 4. Enregistrement du Service Worker (PWA Standalone & Offline)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js')
      .then(reg => console.log('[PWA] Service Worker enregistré avec succès:', reg.scope))
      .catch(err => console.log('[PWA] Échec enregistrement Service Worker:', err));
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initAppAuthAndRouting();
});
