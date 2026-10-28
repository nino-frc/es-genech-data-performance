/**
 * MatchDay PWA - Client Script & Alimentation Dynamique
 * Gestion des 5 Onglets, Modales Joueurs Interactives, Trésorerie & Gouvernance
 * Pont sécurisé vers Netlify Serverless Function (/api/get_matchday_data)
 */

let globalData = null;

// 1. Navigation au Pouce (Bottom Nav 5 Onglets)
function switchTab(tabId, navElement) {
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.style.display = 'none';
    tab.classList.remove('active');
  });

  const target = document.getElementById(tabId);
  if (target) {
    target.style.display = 'block';
    target.classList.add('active');
  }

  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
  });
  if (navElement) {
    navElement.classList.add('active');
  }
}

// 2. Gestion du Splash Screen
function dismissSplashScreen() {
  const splash = document.getElementById('splashScreen');
  if (splash) {
    setTimeout(() => {
      splash.classList.add('hidden');
      setTimeout(() => {
        splash.style.display = 'none';
      }, 400);
    }, 800);
  }
}

// 3. Gestion de la Modale Joueur
function openPlayerModal(playerIndex) {
  if (!globalData || !globalData.effectif_esg) return;
  const p = globalData.effectif_esg[playerIndex];
  if (!p) return;

  const modal = document.getElementById('playerModal');
  const subs = p.sous_scores || {};

  document.getElementById('modalName').textContent = p.nom;
  document.getElementById('modalBadge').textContent = p.badge;
  document.getElementById('modalEsgScore').textContent = p.esg_score;

  const volPct = Math.min(100, Math.round((subs.volume / (subs.volume_max || 35)) * 100));
  const defPct = Math.min(100, Math.round((subs.defense / (subs.defense_max || 30)) * 100));
  const attPct = Math.min(100, Math.round((subs.attaque / (subs.attaque_max || 35)) * 100));
  const malusVal = subs.malus_discipline || 0;

  document.getElementById('subscoreVolumeText').textContent = `${subs.volume} / ${subs.volume_max || 35} pts`;
  document.getElementById('subscoreVolumeBar').style.width = `${volPct}%`;

  document.getElementById('subscoreDefenseText').textContent = `${subs.defense} / ${subs.defense_max || 30} pts`;
  document.getElementById('subscoreDefenseBar').style.width = `${defPct}%`;

  document.getElementById('subscoreAttaqueText').textContent = `${subs.attaque} / ${subs.attaque_max || 35} pts`;
  document.getElementById('subscoreAttaqueBar').style.width = `${attPct}%`;

  document.getElementById('subscoreMalusText').textContent = malusVal > 0 ? `-${malusVal} pts` : `0 pt (Discipline parfaite)`;
  document.getElementById('subscoreMalusBar').style.width = malusVal > 0 ? `${Math.min(100, malusVal * 5)}%` : `0%`;

  document.getElementById('modalMinutes').textContent = `${p.minutes}m`;
  document.getElementById('modalStarts').textContent = `${p.titularisations} / ${p.matchs}`;
  document.getElementById('modalCleanSheets').textContent = `${p.clean_sheets} CS`;

  modal.classList.remove('hidden');
}

function closePlayerModal() {
  const modal = document.getElementById('playerModal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

function handleModalOverlayClick(e) {
  if (e.target.id === 'playerModal') {
    closePlayerModal();
  }
}

// 3. bis Gestion du Centre de Notifications & Alertes PWA
function openNotifModal() {
  const modal = document.getElementById('notifModal');
  if (modal) {
    modal.classList.remove('hidden');
    updateNotifUI();
    const dot = document.getElementById('notifDot');
    if (dot) dot.style.display = 'none';
  }
}

function closeNotifModal() {
  const modal = document.getElementById('notifModal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

function handleNotifModalOverlay(e) {
  if (e.target.id === 'notifModal') {
    closeNotifModal();
  }
}

function updateNotifUI() {
  const statusBadge = document.getElementById('notifStatusBadge');
  const enableBtn = document.getElementById('btnEnableNotif');
  if (!statusBadge || !enableBtn) return;

  if (!('Notification' in window)) {
    statusBadge.textContent = 'Non supporté';
    statusBadge.style.background = '#fef2f2';
    statusBadge.style.color = '#991b1b';
    enableBtn.disabled = true;
    enableBtn.textContent = 'Non disponible';
    return;
  }

  if (Notification.permission === 'granted') {
    statusBadge.textContent = 'Activé ✅';
    statusBadge.style.background = '#dcfce7';
    statusBadge.style.color = '#15803d';
    enableBtn.textContent = 'Notifications actives';
    enableBtn.style.background = '#15803d';
  } else if (Notification.permission === 'denied') {
    statusBadge.textContent = 'Bloqué ❌';
    statusBadge.style.background = '#fee2e2';
    statusBadge.style.color = '#b91c1c';
    enableBtn.textContent = 'Bloqué dans réglages';
    enableBtn.disabled = true;
  } else {
    statusBadge.textContent = 'En attente';
    statusBadge.style.background = '#f1f5f9';
    statusBadge.style.color = 'var(--text-muted)';
    enableBtn.textContent = 'Activer sur cet appareil';
    enableBtn.style.background = 'var(--color-primary)';
  }
}

async function enablePushNotifications() {
  if (!('Notification' in window)) {
    showNotification('Les notifications ne sont pas supportées par votre navigateur.', true);
    return;
  }

  try {
    const permission = await Notification.requestPermission();
    updateNotifUI();

    if (permission === 'granted') {
      showNotification('Notifications MatchDay activées avec succès !');
      testStaffNotification(true);
    } else if (permission === 'denied') {
      showNotification('Autorisation refusée dans le navigateur.', true);
    }
  } catch (err) {
    console.error('Erreur demande permission notifications :', err);
  }
}

function testStaffNotification(isWelcome = false) {
  const isSeclin = (activeClub?.code === 'seclin' || activeClub?.club_code === 'SCLN');
  const clubNom = isSeclin ? 'FC Seclin' : 'ES Genech';
  const title = isWelcome ? 'MatchDay - Notifications Activées 🎉' : `MatchDay - Alerte Staff ${clubNom} 🚨`;
  const body = isWelcome
    ? 'Vous recevrez les alertes de suspension FFF, briefings et debriefings en direct sur cet appareil.'
    : (isSeclin
        ? 'Choc au sommet R2 : Déplacement chez le leader Croix IC 2. Bilan 22 buts marqués cette saison.'
        : 'Commission FFF : 4 joueurs sous sursis avant le déplacement à Aniche SC (Art. 226). 250 € préservés.');

  if (!('Notification' in window) || Notification.permission !== 'granted') {
    if ('Notification' in window && Notification.permission !== 'denied') {
      enablePushNotifications();
      return;
    }
    showNotification(body, false);
    return;
  }

  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.ready.then(reg => {
      reg.showNotification(title, {
        body: body,
        icon: './logo.png',
        badge: './logo.png',
        vibrate: [200, 100, 200],
        data: { url: './' }
      }).catch(err => {
        new Notification(title, { body, icon: './logo.png' });
      });
    }).catch(() => {
      new Notification(title, { body, icon: './logo.png' });
    });
  } else {
    try {
      new Notification(title, { body, icon: './logo.png' });
    } catch (e) {
      showNotification(body, false);
    }
  }

  showNotification('Alerte envoyée sur votre appareil !');
}

// 3. ter Gestion de l'Historique des Matchs & Modale Feuille de Match
function filterMatchHistory(filterType, btnElement) {
  document.querySelectorAll('.history-filter-btn').forEach(b => b.classList.remove('active'));
  if (btnElement) btnElement.classList.add('active');

  const cards = document.querySelectorAll('.match-history-card');
  cards.forEach(card => {
    const comp = card.getAttribute('data-comp-type');
    if (filterType === 'ALL' || comp === filterType) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

function openMatchDetailModal(matchIndex) {
  if (!globalData || !globalData.historique_matchs) return;
  const m = globalData.historique_matchs[matchIndex];
  if (!m) return;

  const modal = document.getElementById('matchDetailModal');
  document.getElementById('detailModalCompBadge').textContent = m.competition;
  document.getElementById('detailModalDate').textContent = `${m.date} (${m.date_heure ? m.date_heure.slice(11) : '15:00'})`;
  document.getElementById('detailModalHomeTeam').textContent = m.domicile;
  document.getElementById('detailModalAwayTeam').textContent = m.exterieur;
  document.getElementById('detailModalScoreDisplay').textContent = m.score_display;

  const badgeEl = document.getElementById('detailModalResultBadge');
  if (m.resultat === 'V') {
    badgeEl.textContent = 'Victoire';
    badgeEl.className = 'match-detail-result-badge score-pill-win';
  } else if (m.resultat === 'N') {
    badgeEl.textContent = 'Match Nul';
    badgeEl.className = 'match-detail-result-badge score-pill-draw';
  } else {
    badgeEl.textContent = 'Défaite';
    badgeEl.className = 'match-detail-result-badge score-pill-loss';
  }

  // Événements
  const evs = m.evenements || [];
  document.getElementById('countEvents').textContent = evs.length;

  const eventsListEl = document.getElementById('detailEventsList');
  if (evs.length > 0) {
    let evHtml = '';
    evs.forEach(ev => {
      let icon = '⚡';
      let title = ev.type;
      if (ev.type === 'BUT') {
        icon = '⚽';
        title = 'But';
      } else if (ev.type === 'AVERTISSEMENT') {
        icon = '🟨';
        title = 'Carton Jaune';
      } else if (ev.type === 'EXPULSION') {
        icon = '🟥';
        title = 'Carton Rouge';
      } else if (ev.type === 'REMPLACEMENT' || ev.type === 'CHANGEMENT') {
        icon = '🔄';
        title = 'Remplacement';
      }

      let desc = ev.acteur;
      if (ev.acteur_secondaire) {
        desc = `<strong>${ev.acteur}</strong> ⬅️ <em>${ev.acteur_secondaire}</em>`;
      } else if (ev.acteur) {
        desc = `<strong>${ev.acteur}</strong>`;
      }

      evHtml += `
        <div class="timeline-event-row">
          <span class="timeline-minute">${ev.minute}'</span>
          <span class="timeline-icon">${icon}</span>
          <div class="timeline-content">
            <div>${desc} <span style="font-size: 10px; color: var(--text-light);">(${ev.equipe})</span></div>
            <div class="timeline-detail">${ev.detail || title}</div>
          </div>
        </div>
      `;
    });
    eventsListEl.innerHTML = evHtml;
  } else {
    eventsListEl.innerHTML = '<div style="text-align: center; color: var(--text-light); font-size: 11px; padding: 14px;">Aucun événement consigné pour ce match.</div>';
  }

  // Compositions
  const lineups = m.compositions || {};
  const isSeclin = (activeClub?.code === 'seclin' || activeClub?.club_code === 'SCLN');
  const clubDisplay = isSeclin ? 'FC SECLIN' : 'ES GENECH';
  const clubBadge = isSeclin ? '🔵⚪' : '🟡🔵';
  const clubLineup = lineups.club || (isSeclin ? (lineups.seclin || lineups.genech) : (lineups.genech || lineups.seclin)) || {};
  const opp = lineups.adversaire || {};
  const lineupContentEl = document.getElementById('detailLineupContent');

  let lineupHtml = `
    <div class="lineup-section-title">
      <span>${clubBadge} ${clubDisplay} (Titulaires)</span>
      <span style="font-family: var(--font-mono);">${clubLineup.titulaires ? clubLineup.titulaires.length : 0} joueurs</span>
    </div>
    <div class="lineup-grid">
  `;

  if (clubLineup.titulaires && clubLineup.titulaires.length > 0) {
    clubLineup.titulaires.forEach(p => {
      lineupHtml += `
        <div class="lineup-item">
          <span class="lineup-number">${p.numero || '-'}</span>
          <span class="lineup-name">${p.nom}</span>
        </div>
      `;
    });
  } else {
    lineupHtml += '<div style="grid-column: 1/-1; font-size: 11px; color: var(--text-light);">Composition non disponible.</div>';
  }

  lineupHtml += `
    </div>
    <div class="lineup-section-title" style="margin-top: 14px;">
      <span>${clubBadge} ${clubDisplay} (Remplaçants)</span>
      <span style="font-family: var(--font-mono);">${clubLineup.remplacants ? clubLineup.remplacants.length : 0} joueurs</span>
    </div>
    <div class="lineup-grid">
  `;

  if (clubLineup.remplacants && clubLineup.remplacants.length > 0) {
    clubLineup.remplacants.forEach(p => {
      lineupHtml += `
        <div class="lineup-item">
          <span class="lineup-number">${p.numero || '-'}</span>
          <span class="lineup-name">${p.nom}</span>
        </div>
      `;
    });
  } else {
    lineupHtml += '<div style="grid-column: 1/-1; font-size: 11px; color: var(--text-light);">Aucun remplaçant renseigné.</div>';
  }

  lineupHtml += `</div>`;

  if (opp.titulaires && opp.titulaires.length > 0) {
    lineupHtml += `
      <div class="lineup-section-title" style="margin-top: 14px;">
        <span>⚪ ${opp.equipe || 'Adversaire'} (Titulaires)</span>
        <span style="font-family: var(--font-mono);">${opp.titulaires.length} joueurs</span>
      </div>
      <div class="lineup-grid">
    `;
    opp.titulaires.forEach(p => {
      lineupHtml += `
        <div class="lineup-item">
          <span class="lineup-number">${p.numero || '-'}</span>
          <span class="lineup-name">${p.nom}</span>
        </div>
      `;
    });
    lineupHtml += `</div>`;
  }

  lineupContentEl.innerHTML = lineupHtml;
  switchMatchDetailSubTab('events');
  modal.classList.remove('hidden');
}

function closeMatchDetailModal() {
  const modal = document.getElementById('matchDetailModal');
  if (modal) {
    modal.classList.add('hidden');
  }
}

function handleMatchDetailModalOverlay(e) {
  if (e.target.id === 'matchDetailModal') {
    closeMatchDetailModal();
  }
}

function switchMatchDetailSubTab(subTab) {
  const btnEvents = document.getElementById('btnTabEvents');
  const btnLineup = document.getElementById('btnTabLineup');
  const viewEvents = document.getElementById('detailViewEvents');
  const viewLineup = document.getElementById('detailViewLineup');

  if (subTab === 'events') {
    if (btnEvents) btnEvents.classList.add('active');
    if (btnLineup) btnLineup.classList.remove('active');
    if (viewEvents) viewEvents.style.display = 'block';
    if (viewLineup) viewLineup.style.display = 'none';
  } else {
    if (btnLineup) btnLineup.classList.add('active');
    if (btnEvents) btnEvents.classList.remove('active');
    if (viewLineup) viewLineup.style.display = 'block';
    if (viewEvents) viewEvents.style.display = 'none';
  }
}

// 3. quater Export Rapport Direction (PDF & Impression)
function exportExecutivePdf() {
  if (activeClub && activeClub.plan === 'TRIAL_BRIDEE') {
    openProModal();
    return;
  }
  const link = document.createElement('a');
  link.href = './rapport_executif_mensuel.pdf';
  link.download = `MatchDay_Rapport_Executif_${activeClub?.nom ? activeClub.nom.replace(/\s+/g, '_') : 'Club'}.pdf`;
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showNotification('Téléchargement du rapport exécutif PDF lancé !');
}

function printExecutiveReport() {
  if (activeClub && activeClub.plan === 'TRIAL_BRIDEE') {
    openProModal();
    return;
  }
  showNotification('Génération de l\'aperçu avant impression...');
  setTimeout(() => {
    window.print();
  }, 250);
}

// 4. Notification d'État (Toast)
function showNotification(message, isError = false) {
  let toast = document.getElementById('appNotificationToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'appNotificationToast';
    toast.style.position = 'fixed';
    toast.style.top = '58px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.zIndex = '999';
    toast.style.padding = '6px 14px';
    toast.style.borderRadius = '20px';
    toast.style.fontSize = '11px';
    toast.style.fontWeight = '600';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    toast.style.transition = 'opacity 0.3s ease';
    document.body.appendChild(toast);
  }

  toast.style.background = isError ? '#fef2f2' : '#f0fdf4';
  toast.style.color = isError ? '#991b1b' : '#166534';
  toast.style.border = isError ? '1px solid #fecaca' : '1px solid #bbf7d0';
  toast.textContent = message;
  toast.style.opacity = '1';

  setTimeout(() => {
    toast.style.opacity = '0';
  }, 3500);
}

// 5. Pont Fetch JavaScript : Appel de la Netlify Function avec gestion du Token et Try/Catch
async function fetchMatchDayFromApi() {
  // Extraction du paramètre d'URL (ex: ?team=genech-token123)
  const urlParams = new URLSearchParams(window.location.search);
  const teamToken = urlParams.get('team') || urlParams.get('token') || 'genech';

  console.log(`[PWA Front-end] Requête Netlify Function pour le token : ${teamToken}`);

  // En local direct (file://), pas d'appel réseau pour respecter la sécurité du navigateur
  if (window.location.protocol === 'file:') {
    return;
  }

  try {
    const response = await fetch(`/api/get_matchday_data?team=${encodeURIComponent(teamToken)}`);

    if (!response.ok) {
      throw new Error(`Erreur réseau HTTP ${response.status} (Fonction Serverless non joignable)`);
    }

    const payload = await response.json();

    if (payload.status === "error") {
      throw new Error(payload.message || "Erreur de base de données retournée par la fonction.");
    }

    console.log("[PWA Front-end] Données MongoDB Atlas reçues avec succès :", payload);

    // Si l'équipe est Seclin ou un autre club, adapter le header
    if (payload.equipe && payload.equipe.nom_affiche) {
      const activeEl = document.getElementById('activeClubName');
      if (activeEl) {
        activeEl.textContent = `${payload.equipe.nom_affiche} (${payload.equipe.categorie || 'R3'})`;
      }
    }

  } catch (error) {
    // Mode discret sans pop-up gênante : conservation des données certifiées
    console.log("[PWA Front-end] Synchronisation distante différée : données locales actives.");
  }
}

// 6. Gestion Multi-Équipes & Initialisation de l'Application
let currentTeamId = 'SENIOR_M1';

// ==========================================================================
// MODULE D'AUTHENTIFICATION B2B & GESTION DES ACCÈS STAFF (ZÉRO DONNÉE INTRUSIVE)
// ==========================================================================

let activeClub = null;
let currentDeviceId = null;
let currentPlatform = null;
let currentSupportCode = null;
let currentStaffRole = null;

function getOrCreateDeviceId() {
  let devId = null;
  try {
    devId = localStorage.getItem('matchday_device_id');
  } catch (e) {}

  if (!devId) {
    const randPart = (typeof crypto !== 'undefined' && crypto.randomUUID) 
      ? crypto.randomUUID().replace(/-/g, '').slice(0, 14)
      : Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
    devId = 'dev_' + randPart;
    try {
      localStorage.setItem('matchday_device_id', devId);
    } catch (e) {}
  }
  currentDeviceId = devId;
  return devId;
}

function getDevicePlatform() {
  if (currentPlatform) return currentPlatform;
  const ua = navigator.userAgent || '';
  let p = "Navigateur Web";

  if (/iPad|Macintosh/i.test(ua) && 'ontouchend' in document) {
    p = "iPad (iPadOS)";
  } else if (/iPhone/i.test(ua)) {
    p = "iPhone (iOS)";
  } else if (/Android/i.test(ua)) {
    p = "Smartphone Android";
  } else if (/Windows/i.test(ua)) {
    p = "PC Windows";
  } else if (/Mac/i.test(ua)) {
    p = "Mac (macOS)";
  } else if (/Linux/i.test(ua)) {
    p = "Poste Linux";
  }

  currentPlatform = p;
  return p;
}

function selectRolePreset(role) {
  const input = document.getElementById('staffRoleInput');
  if (input) input.value = role;
}

function showLicenseModal(errorMsg) {
  const modal = document.getElementById('licenseModal');
  const errEl = document.getElementById('licenseErrorMsg');
  if (errEl) {
    if (errorMsg) {
      errEl.textContent = errorMsg;
      errEl.classList.remove('hidden');
    } else {
      errEl.classList.add('hidden');
    }
  }
  if (modal) {
    modal.classList.remove('hidden');
  }
  const splash = document.getElementById('splashScreen');
  if (splash) {
    splash.classList.add('hidden');
    setTimeout(() => { splash.style.display = 'none'; }, 400);
  }
}

function hideLicenseModal() {
  const modal = document.getElementById('licenseModal');
  if (modal) modal.classList.add('hidden');
}

function handleLicenseSubmit(e) {
  if (e && e.preventDefault) e.preventDefault();
  const input = document.getElementById('licenseKeyInput');
  const roleInput = document.getElementById('staffRoleInput');
  if (!input) return;
  const key = input.value.trim().toUpperCase();
  const role = roleInput ? roleInput.value.trim() : '';
  if (!key) return;
  authenticateClub(key, role, true);
}

function quickFillLicense(key, defaultRole) {
  const input = document.getElementById('licenseKeyInput');
  if (input) input.value = key;
  const roleInput = document.getElementById('staffRoleInput');
  if (roleInput && defaultRole) roleInput.value = defaultRole;
  authenticateClub(key, defaultRole, true);
}

function authenticateClub(key, declaredRole, isFormSubmit) {
  const cleanKey = (key || '').trim().toUpperCase();
  getOrCreateDeviceId();
  getDevicePlatform();

  // 1. Validation immédiate via le Registre Local (Offline First)
  const registry = window.MATCHDAY_LICENSES || {};
  let clubData = registry[cleanKey];

  if (!clubData) {
    showLicenseModal("Clé de licence invalide ou non reconnue. Vérifiez votre saisie.");
    return;
  }

  // Clé valide ! Mémorisation permanente de l'appareil
  try {
    localStorage.setItem('matchday_club_key', cleanKey);
    if (declaredRole) {
      localStorage.setItem('matchday_staff_role', declaredRole);
    }
  } catch (e) {}

  currentStaffRole = declaredRole || localStorage.getItem('matchday_staff_role') || "Membre Staff";
  activeClub = { ...clubData, license_key: cleanKey };
  const isMaster = Boolean(activeClub.is_master || cleanKey === "MD-MASTER-NINO-2026");
  activeClub.is_master = isMaster;

  // Calcul du Code Support Unique (ex: #GN-01, #SC-01, #ROOT-01)
  let savedCode = null;
  try { savedCode = localStorage.getItem('matchday_support_code'); } catch(e) {}
  if (!savedCode) {
    const pfx = isMaster ? "ROOT" : (activeClub.club_code || "STAFF");
    const count = (activeClub.devices ? activeClub.devices.length : 0) + 1;
    savedCode = `#${pfx}-${count < 10 ? '0' + count : count}`;
    try { localStorage.setItem('matchday_support_code', savedCode); } catch(e) {}
  }
  currentSupportCode = savedCode;

  const myCodeEl = document.getElementById('mySupportCodeDisplay');
  if (myCodeEl) myCodeEl.textContent = currentSupportCode;

  // 2. Mise à jour dynamique du Splash Screen (Logo du Club ou Logo Master)
  const splashClubLogo = document.getElementById('splashClubLogo');
  const splashDivider = document.getElementById('splashDivider');
  const splashSub = document.getElementById('splashSubtitle');

  if (splashClubLogo) {
    if (isMaster) {
      splashClubLogo.style.display = 'none';
      if (splashDivider) splashDivider.style.display = 'none';
      if (splashSub) splashSub.textContent = "Super-Admin • Contrôle Global Tous Clubs";
    } else if (activeClub.logo_url) {
      splashClubLogo.src = activeClub.logo_url;
      splashClubLogo.style.display = 'block';
      if (splashDivider) splashDivider.style.display = 'block';
      if (splashSub) splashSub.textContent = `Espace Officiel • ${activeClub.nom}`;
    }
  }

  // 3. Mise à jour du Header Institutionnel (Logo, Sélecteur Master & Blason Club)
  const headerLogo = document.getElementById('headerClubLogo');
  const headerDiv = document.getElementById('headerClubDivider');
  const roleBadge = document.getElementById('appRoleBadge');
  const masterContainer = document.getElementById('masterClubContainer');

  if (isMaster) {
    if (headerLogo) {
      headerLogo.src = './logos/logo_genech.png';
      headerLogo.style.display = 'block';
    }
    if (headerDiv) headerDiv.style.display = 'block';
    if (roleBadge) {
      roleBadge.textContent = 'SUPER ADMIN';
      roleBadge.style.background = '#b45309';
    }
    if (masterContainer) masterContainer.style.display = 'flex';
  } else {
    if (masterContainer) masterContainer.style.display = 'none';
    if (headerLogo && activeClub.logo_url) {
      headerLogo.src = activeClub.logo_url;
      headerLogo.style.display = 'block';
    }
    if (headerDiv) headerDiv.style.display = 'block';
    if (roleBadge) {
      roleBadge.textContent = activeClub.nom.toUpperCase();
      roleBadge.style.background = activeClub.club_code === 'SCLN' ? '#0284c7' : '#15803d';
    }
  }

  // 4. Configuration exclusive du Sélecteur d'équipes (Cloisonnement étanche !)
  const teamSelector = document.getElementById('teamSelector');
  if (teamSelector) {
    teamSelector.innerHTML = '';
    if (isMaster) {
      const defaultGenechTeams = [
        { id: "SENIOR_M1", nom: "Séniors A (R3)" },
        { id: "SENIOR_M3", nom: "Séniors B (D2)" },
        { id: "SENIOR_F2", nom: "Féminines (Interdistrict)" },
        { id: "U18_M1", nom: "U19 / U18 (D1)" }
      ];
      defaultGenechTeams.forEach(eq => {
        const opt = document.createElement('option');
        opt.value = eq.id;
        opt.textContent = eq.nom;
        teamSelector.appendChild(opt);
      });
    } else if (activeClub.equipes_autorisees) {
      activeClub.equipes_autorisees.forEach(eq => {
        const opt = document.createElement('option');
        opt.value = eq.id;
        opt.textContent = eq.nom;
        teamSelector.appendChild(opt);
      });
    }
  }

  // 5. Sélection de l'équipe active
  let targetTeam = activeClub.default_team || activeClub.equipes_autorisees[0].id;
  try {
    const saved = localStorage.getItem('matchday_active_team');
    const isAllowed = activeClub.equipes_autorisees.some(eq => eq.id === saved);
    if (isAllowed && !isFormSubmit) {
      targetTeam = saved;
    } else {
      localStorage.setItem('matchday_active_team', targetTeam);
    }
  } catch (e) {}

  currentTeamId = targetTeam;
  if (teamSelector) teamSelector.value = targetTeam;

  // 6. Chargement et affichage des données de l'équipe
  if (window.MATCHDAY_TEAMS && window.MATCHDAY_TEAMS[targetTeam]) {
    globalData = window.MATCHDAY_TEAMS[targetTeam];
    renderInterface(globalData);
  } else if (window.MATCHDAY_DATA) {
    globalData = window.MATCHDAY_DATA;
    renderInterface(globalData);
  }

  // 7. Mise à jour du compteur d'appareils
  const activeCount = Array.isArray(activeClub.devices) 
    ? activeClub.devices.filter(d => d.statut === 'Actif').length 
    : 1;
  const countBadge = document.getElementById('activeDeviceCountBadge');
  if (countBadge) countBadge.textContent = activeCount;

  // 8. Fermeture de la modale de licence
  hideLicenseModal();

  // 9. Dismiss du Splash Screen après transition fluide
  dismissSplashScreen();

  if (isFormSubmit) {
    const welcomeMsg = isMaster 
      ? "Bienvenue Nino ! Clé Super-Admin activée : accès total à tous les clubs."
      : `Bienvenue ${currentStaffRole} sur l'espace officiel ${activeClub.nom} !`;
    showNotification(welcomeMsg);
  }

  // 10. Synchronisation Asynchrone en arrière-plan avec MongoDB Atlas
  syncDeviceWithBackend(cleanKey, currentStaffRole);
}

function switchMasterClub(clubId) {
  if (!activeClub || !activeClub.is_master) return;
  const teamSelector = document.getElementById('teamSelector');
  const headerLogo = document.getElementById('headerClubLogo');
  const headerDiv = document.getElementById('headerClubDivider');

  if (clubId === '525674') {
    // Mode Super-Admin : Basculement sur Genech
    if (headerLogo) {
      headerLogo.src = './logos/logo_genech.png';
      headerLogo.style.display = 'block';
    }
    if (headerDiv) headerDiv.style.display = 'block';
    if (teamSelector) {
      teamSelector.innerHTML = `
        <option value="SENIOR_M1" selected>Séniors A (R3)</option>
        <option value="U18_M1">U19 / U18 (D1)</option>
        <option value="SENIOR_F2">Féminines (Interdistrict)</option>
        <option value="SENIOR_M3">Séniors B (D2)</option>
      `;
    }
    const roleBadge = document.getElementById('appRoleBadge');
    if (roleBadge) {
      roleBadge.textContent = 'GENECH (ADMIN)';
      roleBadge.style.background = '#b45309';
    }
    changeActiveTeam('SENIOR_M1');
    showNotification("Mode Master : Basculé sur l'espace ES Genech");
  } else if (clubId === '500934') {
    // Mode Super-Admin : Basculement sur Seclin
    if (headerLogo) {
      headerLogo.src = './logos/logo_seclin.jpg';
      headerLogo.style.display = 'block';
    }
    if (headerDiv) headerDiv.style.display = 'block';
    const roleBadge = document.getElementById('appRoleBadge');
    if (roleBadge) {
      roleBadge.textContent = 'SECLIN (ADMIN)';
      roleBadge.style.background = '#0284c7';
    }
    if (teamSelector) {
      teamSelector.innerHTML = `
        <option value="500934_SENIOR_M1" selected>Séniors A (R2)</option>
      `;
    }
    changeActiveTeam('500934_SENIOR_M1');
    showNotification("Mode Master : Basculé sur l'espace FC Seclin");
  }
}

function syncDeviceWithBackend(licenseKey, declaredRole) {
  if (!navigator.onLine) return;
  fetch('/api/validate_license', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      key: licenseKey,
      device_id: currentDeviceId,
      role_titulaire: declaredRole || currentStaffRole,
      support_code: currentSupportCode,
      action: 'validate'
    })
  })
  .then(res => {
    if (!res.ok && res.status === 403) {
      return res.json().then(data => {
        if (data.revoked) {
          alert("🚫 Cet accès a été révoqué par la direction.");
          logoutClub(true);
        }
      });
    }
    return res.json();
  })
  .then(data => {
    if (data && data.valid && data.devices) {
      if (activeClub) {
        activeClub.devices = data.devices;
        const count = data.devices.filter(d => d.statut === 'Actif').length;
        const countBadge = document.getElementById('activeDeviceCountBadge');
        if (countBadge) countBadge.textContent = count;
      }
    }
  })
  .catch(() => {});
}

// --------------------------------------------------------------------------
// GESTION DES MODALES ACCÈS STAFF & QR CODE
// --------------------------------------------------------------------------
function openDeviceModal() {
  if (!activeClub) return;
  const modal = document.getElementById('deviceManagerModal');
  if (!modal) return;

  const isMaster = Boolean(activeClub && (activeClub.is_master || activeClub.plan === 'SUPER_ADMIN'));

  document.getElementById('deviceModalClubTag').textContent = isMaster ? "SUPER ADMIN" : activeClub.nom.toUpperCase();
  document.getElementById('deviceModalKeyDisplay').textContent = activeClub.license_key;
  document.getElementById('deviceModalStatusBadge').textContent = activeClub.statut;

  const myCodeEl = document.getElementById('mySupportCodeDisplay');
  if (myCodeEl) myCodeEl.textContent = currentSupportCode || (isMaster ? "#ADM-01" : "#GN-01");

  const devices = Array.isArray(activeClub.devices) ? activeClub.devices : [];
  const activeCount = devices.filter(d => d.statut === 'Actif').length;
  document.getElementById('deviceModalActiveCount').textContent = activeCount;

  const listContainer = document.getElementById('deviceListContent');
  if (listContainer) {
    let html = '';
    devices.forEach((dev, idx) => {
      const isCurrent = dev.device_id === currentDeviceId;
      const isRevoked = dev.statut === 'Révoqué';
      const supportCode = dev.support_code || (`#${activeClub.club_code || 'STAFF'}-0${idx+1}`);
      const roleName = dev.role_titulaire || dev.alias || `Membre Staff ${supportCode}`;

      html += `
        <div class="device-card-item ${isCurrent ? 'current-device' : ''} ${isRevoked ? 'revoked-device' : ''}">
          <div class="device-left">
            <div class="device-icon-box" style="font-family: var(--font-mono); font-size: 11px; font-weight: 800; color: var(--color-primary);">
              ${supportCode}
            </div>
            <div>
              <div class="device-alias-title">
                <span>${roleName}</span>
                ${isCurrent ? '<span style="font-size: 10px; color: #16a34a; font-weight: 700;">(Votre session)</span>' : ''}
                ${(isCurrent || isMaster) ? `
                  <button type="button" class="btn-edit-alias" onclick="renameDevicePrompt('${dev.device_id}', '${roleName.replace(/'/g, "\\'")}')" title="Modifier le titre / rôle">✏️</button>
                ` : ''}
              </div>
              <div class="device-dates-meta" style="margin-top: 2px;">
                Code Support : <strong>${supportCode}</strong> • Connecté le: ${dev.premiere_connexion || '--'}
              </div>
              <div class="device-dates-meta" style="color: var(--text-muted);">
                Dernière activité : ${dev.derniere_activite || '--'}
              </div>
            </div>
          </div>
          <div class="device-right-actions">
            <span class="device-status-badge ${isRevoked ? 'revoked' : 'active'}">${dev.statut}</span>
            ${(!isRevoked && isMaster) ? `
              <button type="button" class="btn-revoke-device" onclick="revokeDeviceAction('${dev.device_id}')">
                Révoquer
              </button>
            ` : ''}
          </div>
        </div>
      `;
    });

    if (!isMaster) {
      html += `
        <div style="font-size: 11px; color: var(--text-muted); margin-top: 10px; text-align: center; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; padding: 8px;">
          🔒 <strong>Mode Consultation :</strong> La révocation des accès est sous le contrôle exclusif de la Direction & Licence Master Nino.
        </div>
      `;
    }

    listContainer.innerHTML = html;
  }

  modal.classList.remove('hidden');
}

function closeDeviceModal() {
  const modal = document.getElementById('deviceManagerModal');
  if (modal) modal.classList.add('hidden');
}

function handleDeviceModalOverlay(e) {
  if (e.target.id === 'deviceManagerModal') closeDeviceModal();
}

function renameDevicePrompt(deviceId, currentAlias) {
  const isMaster = Boolean(activeClub && (activeClub.is_master || activeClub.plan === 'SUPER_ADMIN'));
  const isSelf = deviceId === currentDeviceId;
  if (!isSelf && !isMaster) {
    alert("Vous ne pouvez renommer que votre propre appareil de session.");
    return;
  }

  const newAlias = prompt("Saisissez le rôle / nom du titulaire de cet accès (ex: Coach Principal, Adjoint, Préparateur...) :", currentAlias);
  if (!newAlias || !newAlias.trim()) return;

  if (activeClub && activeClub.devices) {
    activeClub.devices = activeClub.devices.map(d => {
      if (d.device_id === deviceId) return { ...d, role_titulaire: newAlias.trim(), alias: newAlias.trim() };
      return d;
    });
  }
  openDeviceModal();

  fetch('/api/validate_license', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      key: activeClub.license_key,
      action: 'rename_device',
      target_device_id: deviceId,
      new_alias: newAlias.trim()
    })
  }).catch(() => {});
}

function revokeDeviceAction(deviceId) {
  const isMaster = Boolean(activeClub && (activeClub.is_master || activeClub.plan === 'SUPER_ADMIN'));
  if (!isMaster) {
    alert("Action réservée à la Direction Technique & Licence Master Nino. Les accès club standards sont en mode consultation.");
    return;
  }

  const isSelf = deviceId === currentDeviceId;
  const msg = isSelf 
    ? "⚠️ Attention : vous allez révoquer votre propre accès actuel. Vous serez immédiatement déconnecté. Confirmer ?"
    : "Voulez-vous vraiment révoquer l'accès de ce membre du staff ? Il sera immédiatement déconnecté de l'espace club.";

  if (!confirm(msg)) return;

  if (activeClub && activeClub.devices) {
    activeClub.devices = activeClub.devices.map(d => {
      if (d.device_id === deviceId) return { ...d, statut: 'Révoqué' };
      return d;
    });
  }

  fetch('/api/validate_license', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      key: activeClub.license_key,
      action: 'revoke_device',
      target_device_id: deviceId
    })
  }).catch(() => {});

  if (isSelf) {
    logoutClub(true);
  } else {
    openDeviceModal();
    const countBadge = document.getElementById('activeDeviceCountBadge');
    if (countBadge) {
      const activeCount = activeClub.devices.filter(d => d.statut === 'Actif').length;
      countBadge.textContent = activeCount;
    }
    showNotification("Accès révoqué avec succès.");
  }
}

function confirmLogout() {
  if (confirm("Voulez-vous vraiment vous déconnecter de cet espace club ?")) {
    logoutClub();
  }
}

function logoutClub(silent) {
  try {
    localStorage.removeItem('matchday_club_key');
    localStorage.removeItem('matchday_active_team');
    localStorage.removeItem('matchday_staff_role');
    localStorage.removeItem('matchday_support_code');
  } catch (e) {}

  activeClub = null;
  currentSupportCode = null;
  currentStaffRole = null;
  closeDeviceModal();
  closeQrModal();

  const trialBanner = document.getElementById('trialBanner');
  if (trialBanner) trialBanner.style.display = 'none';

  const headerLogo = document.getElementById('headerClubLogo');
  const headerDiv = document.getElementById('headerClubDivider');
  const roleBadge = document.getElementById('appRoleBadge');
  const masterContainer = document.getElementById('masterClubContainer');

  if (masterContainer) masterContainer.style.display = 'none';
  if (headerLogo) headerLogo.style.display = 'none';
  if (headerDiv) headerDiv.style.display = 'none';
  if (roleBadge) {
    roleBadge.textContent = 'SAAS';
    roleBadge.style.background = '#0a1728';
  }

  showLicenseModal(silent ? "Votre session sur cet appareil a été révoquée." : null);
}

// --------------------------------------------------------------------------
// GESTION DU QR CODE CLUB
// --------------------------------------------------------------------------
function openQrModal() {
  if (!activeClub) return;
  const modal = document.getElementById('qrCodeModal');
  if (!modal) return;

  const qrTag = document.getElementById('qrModalClubTag');
  const qrKey = document.getElementById('qrModalKeyDisplay');
  const qrImg = document.getElementById('qrModalImage');
  const qrUrlInput = document.getElementById('qrModalUrlInput');

  if (qrTag) qrTag.textContent = activeClub.nom.toUpperCase();
  if (qrKey) qrKey.textContent = activeClub.license_key;
  if (qrImg) qrImg.src = `./qr_codes/qr_${activeClub.club_code.toLowerCase()}.png`;
  
  const fullUrl = `https://match-day-app.netlify.app/?key=${activeClub.license_key}`;
  if (qrUrlInput) qrUrlInput.value = fullUrl;

  modal.classList.remove('hidden');
}

function closeQrModal() {
  const modal = document.getElementById('qrCodeModal');
  if (modal) modal.classList.add('hidden');
}

function handleQrModalOverlay(e) {
  if (e.target.id === 'qrCodeModal') closeQrModal();
}

function copyActivationUrl() {
  const input = document.getElementById('qrModalUrlInput');
  const btn = document.getElementById('btnCopyUrl');
  if (input) {
    input.select();
    input.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(input.value).then(() => {
      if (btn) {
        const orig = btn.textContent;
        btn.textContent = "✓ Copié !";
        btn.style.background = "#15803d";
        setTimeout(() => {
          btn.textContent = orig;
          btn.style.background = "";
        }, 2000);
      }
    }).catch(() => {
      document.execCommand('copy');
      if (btn) btn.textContent = "✓ Copié !";
    });
  }
}

// --------------------------------------------------------------------------
// GESTION DE LA MODALE MENTIONS LÉGALES & CONFIDENTIALITÉ (RGPD)
// --------------------------------------------------------------------------
function openLegalModal() {
  const modal = document.getElementById('legalModal');
  if (modal) modal.classList.remove('hidden');
}

function closeLegalModal() {
  const modal = document.getElementById('legalModal');
  if (modal) modal.classList.add('hidden');
}

function handleLegalModalOverlay(e) {
  if (e.target.id === 'legalModal') closeLegalModal();
}

// --------------------------------------------------------------------------
// GESTION DE LA MODALE MATCHDAY PRO (OFFRE B2B & BRIDAGE TRIAL)
// --------------------------------------------------------------------------
function openProModal() {
  const modal = document.getElementById('proUpgradeModal');
  if (modal) modal.classList.remove('hidden');
}

function closeProModal() {
  const modal = document.getElementById('proUpgradeModal');
  if (modal) modal.classList.add('hidden');
}

function handleProModalOverlay(e) {
  if (e.target.id === 'proUpgradeModal') closeProModal();
}

function changeActiveTeam(teamId) {
  if (!window.MATCHDAY_TEAMS || !window.MATCHDAY_TEAMS[teamId]) {
    console.warn(`Équipe ${teamId} non disponible dans le flux local.`);
    return;
  }

  currentTeamId = teamId;
  try {
    localStorage.setItem('matchday_active_team', teamId);
  } catch (e) {}

  const teamData = window.MATCHDAY_TEAMS[teamId];
  globalData = teamData;

  const sel = document.getElementById('teamSelector');
  if (sel && sel.value !== teamId) {
    sel.value = teamId;
  }

  renderInterface(teamData);
  showNotification(`Équipe active : ${teamData.equipe_active.nom_affiche}`);
}

function initApp() {
  getOrCreateDeviceId();
  getDevicePlatform();

  // 1. Détection automatique via QR Code (?key=MD-XXXX-...)
  const urlParams = new URLSearchParams(window.location.search);
  const urlKey = urlParams.get('key');

  if (urlKey) {
    const cleanKey = urlKey.trim().toUpperCase();
    try {
      localStorage.setItem('matchday_club_key', cleanKey);
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (e) {}
  }

  // 2. Lecture de la clé mémorisée
  let storedKey = null;
  try {
    storedKey = localStorage.getItem('matchday_club_key');
  } catch (e) {}

  if (!storedKey) {
    showLicenseModal();
    return;
  }

  // 3. Authentification & Démarrage
  const savedRole = localStorage.getItem('matchday_staff_role') || null;
  authenticateClub(storedKey, savedRole, false);
  updateNotifUI();
}

// 7. Rendu DOM Dynamique Complet
function renderInterface(data) {
  if (!data) return;

  const isTrial = Boolean(activeClub && activeClub.plan === 'TRIAL_BRIDEE');

  // Bandeau Démo Bridée (Uniquement pour les clubs en essai commercial comme Seclin)
  const trialBanner = document.getElementById('trialBanner');
  if (trialBanner) {
    trialBanner.style.display = isTrial ? 'block' : 'none';
  }

  // A. Header
  const currentTeam = data.equipe_active || {};
  const clubNameEl = document.getElementById('activeClubName');
  if (clubNameEl) {
    clubNameEl.textContent = `${currentTeam.nom || 'ES Genech'} (${currentTeam.poule || 'R3'})`;
  }

  // B. Dernier Match Officiel
  const match = data.dernier_match || {};
  const homeEl = document.getElementById('homeTeamName');
  const awayEl = document.getElementById('awayTeamName');
  const scoreEl = document.getElementById('matchScoreDisplay');
  const metaEl = document.getElementById('matchMetaInfo');

  if (homeEl) homeEl.textContent = match.domicile || '--';
  if (awayEl) awayEl.textContent = match.exterieur || '--';
  if (scoreEl && match.score_domicile !== undefined && match.score_exterieur !== undefined) {
    scoreEl.textContent = `${match.score_domicile} - ${match.score_exterieur}`;
  }
  if (metaEl) {
    metaEl.textContent = `${match.competition || ''} • ${match.date_heure || ''}`;
  }

  // C. 4 KPIs de Saison
  const kpis = data.kpis_saison || {};
  const goalsEl = document.getElementById('kpiGoals');
  const csEl = document.getElementById('kpiCleanSheets');
  const minEl = document.getElementById('kpiTotalMinutes');
  const cardsEl = document.getElementById('kpiCardsSummary');

  if (goalsEl) goalsEl.textContent = kpis.buts_marques ?? '--';
  if (csEl) csEl.textContent = kpis.clean_sheets ?? '--';
  if (minEl) minEl.textContent = kpis.minutes_cumulees ? `${kpis.minutes_cumulees.toLocaleString()}m` : '--';
  if (cardsEl) cardsEl.textContent = `${kpis.cartons_jaunes ?? 0} J. / ${kpis.cartons_rouges ?? 0} R.`;

  // D. Chronologie Dernier Match
  const timelineContainer = document.getElementById('matchEventsTimeline');
  const events = data.evenements_dernier_match || [];
  if (timelineContainer) {
    if (events.length > 0) {
      let eventsHtml = '';
      events.forEach(ev => {
        const icon = ev.type === 'BUT' ? '⚽' : (ev.type === 'AVERTISSEMENT' ? '🟨' : (ev.type === 'EXPULSION' ? '🟥' : '🔄'));
        eventsHtml += `
          <div style="display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid var(--border-light); font-size: 12px;">
            <div>
              <strong>${ev.minute}'</strong> ${icon} <span style="font-weight: 600;">${ev.acteur}</span>
              <span style="color: var(--text-light); font-size: 11px;">(${ev.equipe})</span>
            </div>
            <div style="color: var(--text-muted); font-size: 11px;">${ev.detail}</div>
          </div>
        `;
      });
      timelineContainer.innerHTML = eventsHtml;
      timelineContainer.classList.remove('skeleton');
    } else {
      timelineContainer.innerHTML = "<div style='color: var(--text-light); font-size: 11px; text-align: center; padding: 8px;'>Aucun événement officiel renseigné.</div>";
      timelineContainer.classList.remove('skeleton');
    }
  }

  // E. Prochain Match & Arbitre Désigné
  const next = data.prochain_match || {};
  const ref = data.arbitre_prochain_match || {};
  if (next.domicile) {
    document.getElementById('nextMatchFixture').textContent = `${next.domicile} vs ${next.exterieur}`;
    document.getElementById('nextMatchComp').textContent = next.competition;
    document.getElementById('nextMatchDate').textContent = next.date_heure ? (next.date_heure.includes('T') || next.date_heure.includes(':') ? next.date_heure : next.date_heure) : "À programmer";
    document.getElementById('nextMatchLieu').textContent = next.lieu || "Terrain Officiel";
  }
  if (ref.nom_arbitre) {
    document.getElementById('refereeName').textContent = `👨‍⚖️ ${ref.nom_arbitre}`;
    document.getElementById('refereeSeverityBadge').textContent = ref.severite;
    document.getElementById('refereeSeverityBadge').style.background = ref.badge_color ? `${ref.badge_color}22` : '#fee2e2';
    document.getElementById('refereeSeverityBadge').style.color = ref.badge_color || '#b91c1c';
    document.getElementById('refereeCardsAvg').textContent = `${ref.moyenne_jaunes} cartons jaunes / match`;
    document.getElementById('refereeAdvice').textContent = ref.consigne_coach;
  }

  // E bis. Scouting Comparatif Dynamique & Alertes Adversaire
  const compSectionEl = document.getElementById('scoutingComparativeSection');
  if (compSectionEl) {
    const comp = next.comparatif;
    if (comp) {
      compSectionEl.innerHTML = `
        <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px;">
          ${comp.titre || 'Comparatif de Performance'}
        </div>
        <div class="scouting-stat-bar">
          <span>Classement</span>
          <strong><span style="color: #b45309;">${comp.adversaire_nom} (${comp.adversaire_rang})</span> vs <span style="color: var(--color-green);">${comp.club_nom} (${comp.club_rang})</span></strong>
        </div>
        <div class="scouting-stat-bar">
          <span>Points au Compteur</span>
          <strong>${comp.adversaire_pts} pts vs ${comp.club_pts} pts</strong>
        </div>
        <div class="scouting-stat-bar">
          <span>Attaque (Buts marqués)</span>
          <strong>${comp.adversaire_buts_pour} buts vs ${comp.club_buts_pour} buts</strong>
        </div>
        <div class="scouting-stat-bar">
          <span>Défense (Buts encaissés)</span>
          <strong>${comp.adversaire_buts_contre} encaissés vs ${comp.club_buts_contre} encaissés</strong>
        </div>
      `;
      compSectionEl.style.display = 'block';
    } else {
      compSectionEl.innerHTML = '';
      compSectionEl.style.display = 'none';
    }
  }

  const alertsListEl = document.getElementById('opponentAlertsList');
  const alertsSectionEl = document.getElementById('scoutingAlertsSection');
  const scoutAlerts = next.alertes || next.adversaire_alertes || [];
  if (alertsListEl) {
    if (scoutAlerts.length > 0) {
      alertsListEl.innerHTML = scoutAlerts.map(a => `<li>${a}</li>`).join('');
      if (alertsSectionEl) alertsSectionEl.style.display = 'block';
    } else {
      if (alertsSectionEl) alertsSectionEl.style.display = 'none';
    }
  }

  // E ter. Historique Exhaustif des Matchs Passés (Saison 2026-2027)
  const historyContainer = document.getElementById('matchHistoryListContainer');
  const historyList = data.historique_matchs || [];

  // Mise à jour dynamique du bandeau de bilan dans l'onglet Historique
  const histGov = data.gouvernance || {};
  const histBilan = histGov.bilan_global || {};
  const histHeroBox = document.querySelector('#tabHistory .gov-hero-box');
  if (histHeroBox && histBilan.matchs !== undefined) {
    const diffVal = histBilan.difference ?? (histBilan.buts_pour - histBilan.buts_contre);
    const diffStr = diffVal > 0 ? `+${diffVal}` : `${diffVal}`;
    histHeroBox.innerHTML = `
      <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.85; margin-bottom: 4px;">
        Bilan Officiel Saison • ${data.equipe_active.nom_affiche || 'ES Genech'}
      </div>
      <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
        <div style="font-size: 20px; font-weight: 900; font-family: var(--font-mono);">
          ${histBilan.matchs} Matchs <span style="font-size: 13px; font-weight: 600; opacity: 0.85;">(${histBilan.victoires}V - ${histBilan.nuls}N - ${histBilan.defaites}D)</span>
        </div>
        <div class="tactical-role-pill" style="background: rgba(255,255,255,0.2); color: #fff;">
          ${data.kpis_saison ? data.kpis_saison.clean_sheets : 0} Clean Sheets
        </div>
      </div>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; font-size: 11px; text-align: center; background: rgba(0,0,0,0.15); padding: 8px; border-radius: 6px;">
        <div>
          <div style="font-size: 9px; opacity: 0.75; text-transform: uppercase;">Buts Marqués</div>
          <strong style="font-size: 14px; font-family: var(--font-mono); color: #86efac;">${histBilan.buts_pour ?? 0} buts</strong>
        </div>
        <div>
          <div style="font-size: 9px; opacity: 0.75; text-transform: uppercase;">Buts Encaissés</div>
          <strong style="font-size: 14px; font-family: var(--font-mono); color: #fca5a5;">${histBilan.buts_contre ?? 0} buts</strong>
        </div>
        <div>
          <div style="font-size: 9px; opacity: 0.75; text-transform: uppercase;">Différence</div>
          <strong style="font-size: 14px; font-family: var(--font-mono); color: #93c5fd;">${diffStr}</strong>
        </div>
      </div>
    `;
  }

  // Filtres par compétition adaptés à l'équipe
  const filterBar = document.querySelector('.history-filter-bar');
  if (filterBar) {
    if (currentTeamId === 'SENIOR_M1') {
      filterBar.innerHTML = `
        <button class="history-filter-btn active" onclick="filterMatchHistory('ALL', this)">Tous (${historyList.length})</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('R3', this)">Régional 3 (4)</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('CDF', this)">Coupe de France (5)</button>
      `;
    } else if (currentTeamId === 'U18_M1') {
      filterBar.innerHTML = `
        <button class="history-filter-btn active" onclick="filterMatchHistory('ALL', this)">Tous (${historyList.length})</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('CHAMPIONNAT', this)">18 19 D1 (5)</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('GAMBARDELLA', this)">Coupe Gambardella (1)</button>
      `;
    } else if (currentTeamId === 'SENIOR_M3') {
      filterBar.innerHTML = `
        <button class="history-filter-btn active" onclick="filterMatchHistory('ALL', this)">Tous (${historyList.length})</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('CHAMPIONNAT', this)">Seniors D2 (4)</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('COUPE', this)">Coupe des Flandres (2)</button>
      `;
    } else if (currentTeamId === '500934_SENIOR_M1') {
      const champCount = historyList.filter(m => m.comp_type === 'CHAMPIONNAT').length;
      const coupeCount = historyList.filter(m => m.comp_type === 'COUPE').length;
      filterBar.innerHTML = `
        <button class="history-filter-btn active" onclick="filterMatchHistory('ALL', this)">Tous (${historyList.length})</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('CHAMPIONNAT', this)">Régional 2 (${champCount})</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('COUPE', this)">Coupe (${coupeCount})</button>
      `;
    } else {
      filterBar.innerHTML = `
        <button class="history-filter-btn active" onclick="filterMatchHistory('ALL', this)">Tous (${historyList.length})</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('CHAMPIONNAT', this)">Interdistricts (4)</button>
      `;
    }
  }
  if (historyContainer) {
    if (historyList.length > 0) {
      let historyHtml = '';
      const displayMatches = isTrial ? historyList.slice(0, 3) : historyList;
      displayMatches.forEach((m, idx) => {
        let pillClass = 'score-pill-win';
        let tagClass = 'win';
        if (m.resultat === 'N') {
          pillClass = 'score-pill-draw';
          tagClass = 'draw';
        } else if (m.resultat === 'D') {
          pillClass = 'score-pill-loss';
          tagClass = 'loss';
        }

        const clubToken = (activeClub?.club_code === 'SCLN') ? 'SECLIN' : 'GENECH';
        const isHomeClub = m.domicile.toUpperCase().includes(clubToken);
        const isAwayClub = m.exterieur.toUpperCase().includes(clubToken);

        historyHtml += `
          <div class="match-history-card" data-comp-type="${m.comp_type}" onclick="openMatchDetailModal(${idx})">
            <div class="match-history-header">
              <span class="tactical-role-pill" style="font-size: 9px; padding: 1px 6px;">${m.competition}</span>
              <span>${m.date}</span>
            </div>
            <div class="match-history-main">
              <div class="match-history-team home ${isHomeClub ? 'highlight-genech' : ''}">
                ${m.domicile}
              </div>
              <div class="match-history-score-wrapper">
                <span class="score-pill ${pillClass}">${m.score_display}</span>
                <span class="match-history-res-tag ${tagClass}">${m.resultat_label}</span>
              </div>
              <div class="match-history-team away ${isAwayClub ? 'highlight-genech' : ''}">
                ${m.exterieur}
              </div>
            </div>
                ${m.exterieur}
              </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 10px; color: var(--text-light); border-top: 1px dashed var(--border-light); padding-top: 5px; margin-top: 2px;">
              <span>⚡ ${m.evenements ? m.evenements.length : 0} événements</span>
              <span style="font-weight: 700; color: var(--color-primary);">Feuille de match 👉</span>
            </div>
          </div>
        `;
      });

      // Bloc Verrouillé Démo (Affiché si club en version d'essai)
      if (isTrial && historyList.length > 3) {
        const lockedCount = historyList.length - 3;
        historyHtml += `
          <div class="trial-lock-card" onclick="openProModal()">
            <div class="trial-lock-icon">🔒</div>
            <div class="trial-lock-info">
              <div class="trial-lock-title">Historique Matchs Verrouillé (${lockedCount} matchs restants)</div>
              <div class="trial-lock-desc">L'accès à l'intégralité de la saison et aux feuilles de match officielles est réservé à la version Premium.</div>
            </div>
            <button type="button" class="btn-trial-unlock" onclick="event.stopPropagation(); openProModal()">Version Premium →</button>
          </div>
        `;
      }

      historyContainer.innerHTML = historyHtml;
      historyContainer.classList.remove('skeleton');
    } else {
      historyContainer.innerHTML = '<div style="text-align: center; color: var(--text-light); font-size: 11px; padding: 16px;">Aucun match archivé.</div>';
      historyContainer.classList.remove('skeleton');
    }
  }

  // F. Effectif Joueurs & Score ESG (Cliquables vers Modale)
  const playersContainer = document.getElementById('playersListContainer');
  const players = data.effectif_esg || [];
  if (playersContainer) {
    if (players.length > 0) {
      let playersHtml = '';
      const displayPlayers = isTrial ? players.slice(0, 5) : players;
      displayPlayers.forEach((p, idx) => {
        const hasRed = p.cartons_r > 0 ? `<span>🟥 ${p.cartons_r}</span>` : '';
        playersHtml += `
          <div class="player-row" onclick="openPlayerModal(${idx})">
            <div class="player-left">
              <div class="player-rank">${p.rang}</div>
              <div>
                <div class="player-name-text">${p.nom}</div>
                <div class="tactical-role-pill">${p.badge}</div>
                <div class="player-stats-mini">
                  <span>⏱️ ${p.minutes}m</span>
                  <span>⚽ ${p.buts}</span>
                  <span>🛡️ ${p.clean_sheets} CS</span>
                  <span>🟨 ${p.cartons_j}</span>
                  ${hasRed}
                </div>
              </div>
            </div>
            <div class="esg-score-box">
              <span class="esg-number">${p.esg_score}</span>
              <span class="esg-label">Score ESG</span>
            </div>
          </div>
        `;
      });

      // Bloc Verrouillé Démo Effectif (Affiché si club en version d'essai)
      if (isTrial && players.length > 5) {
        const lockedPlayers = players.length - 5;
        playersHtml += `
          <div class="trial-lock-card" onclick="openProModal()">
            <div class="trial-lock-icon">🔒</div>
            <div class="trial-lock-info">
              <div class="trial-lock-title">Effectif Restant Verrouillé (${lockedPlayers} joueurs)</div>
              <div class="trial-lock-desc">Les fiches individuelles, profils physiques et scores d'impact ESG du reste du groupe sont réservés à la version Premium.</div>
            </div>
            <button type="button" class="btn-trial-unlock" onclick="event.stopPropagation(); openProModal()">Version Premium →</button>
          </div>
        `;
      }

      playersContainer.innerHTML = playersHtml;
      playersContainer.classList.remove('skeleton');
    }
  }

  // G. Discipline & Traducteur Financier
  const treso = data.tresorerie_discipline || {};
  const costEl = document.getElementById('treasuryCost');
  const savedEl = document.getElementById('treasurySaved');
  if (costEl) costEl.textContent = `${treso.cout_total_estime || 0} €`;
  if (savedEl) savedEl.textContent = `+${treso.amendes_evitees || 250} €`;

  // G1. Cartons Rouges Détaillés
  const redCardsContainer = document.getElementById('redCardsContainer');
  const redCards = data.cartons_rouges_details || [];
  if (redCardsContainer) {
    if (redCards.length > 0) {
      let redHtml = '';
      redCards.forEach(rc => {
        const badgeCls = rc.est_suspendu ? 'status-active-red' : 'status-purged';
        redHtml += `
          <div style="background: var(--color-red-light); border-left: 4px solid var(--color-red); border-radius: 6px; padding: 9px 12px; margin-bottom: 8px; font-size: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 700; margin-bottom: 2px;">
              <span>🟥 <strong>${rc.joueur}</strong> (${rc.minute}')</span>
              <span style="font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 3px; background: #e2e8f0; color: #475569;">${rc.statut_purge}</span>
            </div>
            <div style="font-size: 11px; color: var(--text-muted);">
              Exclusion lors de : <strong>${rc.match_label}</strong> (le ${rc.date})
            </div>
          </div>
        `;
      });
      redCardsContainer.innerHTML = redHtml;
    } else {
      redCardsContainer.innerHTML = "<div style='font-size: 11px; color: var(--text-light); padding: 6px;'>Aucun carton rouge reçu cette saison.</div>";
    }
  }

  // G2. Sursis
  const sursisContainer = document.getElementById('sursisContainer');
  const sursis = data.sursis_details || [];
  if (sursisContainer) {
    if (sursis.length > 0) {
      let sursisHtml = '';
      sursis.forEach(s => {
        sursisHtml += `
          <div style="background: var(--color-gold-light); border-left: 4px solid var(--color-gold); border-radius: 6px; padding: 9px 12px; margin-bottom: 8px; font-size: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 700; margin-bottom: 2px;">
              <span>⚠️ <strong>${s.joueur}</strong></span>
              <span style="font-size: 10px; color: #92400e; font-weight: 700;">Échéance : ${s.expiration}</span>
            </div>
            <div style="font-size: 11px; color: #78350f;">
              2 cartons reçus (${s.dates}). Prochain jaune = <strong>1 match de suspension ferme</strong>.
            </div>
          </div>
        `;
      });
      sursisContainer.innerHTML = sursisHtml;
    } else {
      sursisContainer.innerHTML = "<div style='font-size: 11px; color: var(--color-green); padding: 6px;'>✅ Aucun joueur sous le coup d'un sursis actuellement.</div>";
    }
  }

  // H. Onglet Gouvernance Exécutive
  const gov = data.gouvernance || {};
  if (gov.ppm_championnat !== undefined) {
    document.getElementById('govPpm').innerHTML = `${gov.ppm_championnat} <span style="font-size: 13px; font-weight: 600;">PPM</span>`;
    document.getElementById('govMonteCarlo').textContent = `${gov.probabilite_montee_pct}%`;
    document.getElementById('govInvincibilite').textContent = `${gov.taux_invincibilite}%`;
    document.getElementById('govCleanSheetRatio').textContent = `${gov.ratio_clean_sheet_pct}%`;
    document.getElementById('govMoyEncaisses').textContent = `${gov.moyenne_buts_encaisses}`;
    document.getElementById('govPointsPrevus').textContent = `${gov.projection_saison.points_prevus} pts`;

    const bilan = gov.bilan_global || {};
    document.getElementById('govVictoires').textContent = bilan.victoires ?? 5;
    document.getElementById('govNuls').textContent = bilan.nuls ?? 2;
    document.getElementById('govDefaites').textContent = bilan.defaites ?? 2;
    const diff = (bilan.buts_pour ?? 10) - (bilan.buts_contre ?? 4);
    document.getElementById('govDiffButs').textContent = diff > 0 ? `+${diff}` : diff;

    // H bis. Matrice des Quarts d'Heure (Temps Forts / Faibles)
    const matrixContainer = document.getElementById('timeMatrixRowsContainer');
    const tranches = gov.matrice_quarts_heure || [];
    if (matrixContainer && tranches.length > 0) {
      let matrixHtml = '';
      const maxGoals = 3;
      tranches.forEach(t => {
        const pctScored = Math.min(100, Math.round((t.marques / maxGoals) * 100));
        const pctConceded = Math.min(100, Math.round((t.encaisses / maxGoals) * 100));

        matrixHtml += `
          <div class="time-matrix-row">
            <div class="time-matrix-label">${t.tranche}</div>
            <div class="time-matrix-bars-wrapper">
              <!-- Ligne Buts Marqués -->
              <div class="matrix-line">
                <div class="matrix-bar-track">
                  <div class="matrix-bar-fill fill-scored" style="width: ${pctScored}%;"></div>
                </div>
                <div class="matrix-count-col ${t.marques > 0 ? 'scored' : 'zero'}">
                  ${t.marques} <span>marqué${t.marques > 1 ? 's' : ''}</span>
                </div>
              </div>
              <!-- Ligne Buts Encaissés -->
              <div class="matrix-line">
                <div class="matrix-bar-track">
                  <div class="matrix-bar-fill fill-conceded" style="width: ${pctConceded}%;"></div>
                </div>
                <div class="matrix-count-col ${t.encaisses > 0 ? 'conceded' : 'zero'}">
                  ${t.encaisses} <span>encaissé${t.encaisses > 1 ? 's' : ''}</span>
                </div>
              </div>
            </div>
          </div>
        `;
      });
      matrixContainer.innerHTML = matrixHtml;
      matrixContainer.classList.remove('skeleton');
    }

    const matrixClubNameEl = document.getElementById('matrixLegendClubName');
    if (matrixClubNameEl) {
      const isSeclin = (activeClub?.code === 'seclin' || activeClub?.club_code === 'SCLN');
      matrixClubNameEl.textContent = `Buts Marqués (${isSeclin ? 'FC Seclin' : 'ES Genech'})`;
    }
  }

  // I. Classement Officiel & Isolation Club
  const isSeclinClub = (activeClub?.code === 'seclin' || activeClub?.club_code === 'SCLN');
  const standingsCardTitleEl = document.getElementById('standingsCardTitle');
  if (standingsCardTitleEl) {
    const currentTeam = (window.MATCHDAY_TEAMS && window.MATCHDAY_TEAMS[currentTeamId]) || {};
    standingsCardTitleEl.textContent = isSeclinClub 
      ? "Régional 2 • Poule B" 
      : (currentTeam.categorie ? `${currentTeam.categorie} • ${currentTeam.poule || 'Poule D'}` : "Seniors R3 • Poule D");
  }

  const standingsContainer = document.getElementById('standingsTableContainer');
  const standings = data.classement || [];
  if (standingsContainer) {
    if (standings.length > 0) {
      let tableHtml = `
        <table class="table-fff">
          <thead>
            <tr>
              <th style="width: 28px;">Pl</th>
              <th>Équipe</th>
              <th style="text-align: right; width: 45px;">Pts</th>
              <th style="text-align: right; width: 35px;">J</th>
            </tr>
          </thead>
          <tbody>
      `;
      standings.forEach(st => {
        const isClub = isSeclinClub 
          ? st.equipe.toUpperCase().includes('SECLIN') 
          : st.equipe.toUpperCase().includes('GENECH');
        tableHtml += `
          <tr class="${isClub ? 'highlight-team' : ''}">
            <td>${st.rang}</td>
            <td>${st.equipe}</td>
            <td style="text-align: right; font-weight: 700;">${st.points}</td>
            <td style="text-align: right; color: var(--text-light);">${st.joues}</td>
          </tr>
        `;
      });
      tableHtml += '</tbody></table>';
      standingsContainer.innerHTML = tableHtml;
      standingsContainer.classList.remove('skeleton');
    } else {
      standingsContainer.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 24px 14px;">
          <div style="font-size: 26px; margin-bottom: 6px;">🏆</div>
          <strong style="color: var(--text-main);">Classement officiel en cours de synchronisation</strong>
          <div style="font-size: 11px; color: var(--text-light); margin-top: 4px; line-height: 1.4;">
            Les classements de cette division sont publiés et actualisés par le District après validation des feuilles de match FFF.
          </div>
        </div>
      `;
      standingsContainer.classList.remove('skeleton');
    }
  }

  // J. Feed de Notifications Dynamique (Isolation 100% selon le club connecté)
  const notifFeedEl = document.getElementById('notifFeedList');
  if (notifFeedEl) {
    if (isSeclinClub) {
      notifFeedEl.innerHTML = `
        <div class="notif-item alert-urgent">
          <div class="notif-item-header">
            <span class="notif-item-tag tag-primary">CHAMPIONNAT R2</span>
            <span class="notif-item-time">Aujourd'hui 10:00</span>
          </div>
          <div class="notif-item-title">Choc au sommet : J-4 vs Croix IC 2</div>
          <div class="notif-item-body">
            Déplacement chez le leader invaincu de Régional 2 Poule B. Rapport tactique & scouting adverse consultable.
          </div>
        </div>
        <div class="notif-item alert-success">
          <div class="notif-item-header">
            <span class="notif-item-tag tag-success">COUPE DES HAUTS-DE-FRANCE</span>
            <span class="notif-item-time">25/10 18:00</span>
          </div>
          <div class="notif-item-title">Arques 2-2 Seclin (TAB 4-5) : Qualification validée !</div>
          <div class="notif-item-body">
            Qualification héroïque aux tirs au but après un match nul 2-2. Bilan consolidé à 22 buts marqués cette saison.
          </div>
        </div>
        <div class="notif-item alert-info">
          <div class="notif-item-header">
            <span class="notif-item-tag tag-danger">VEILLE TECHNIQUE</span>
            <span class="notif-item-time">20/10 14:00</span>
          </div>
          <div class="notif-item-title">Suivi Régional 2 Poule B FFF</div>
          <div class="notif-item-body">
            Plateforme configurée pour l'équipe fanion Senior A du FC Seclin. Consultation exclusive staff technique.
          </div>
        </div>
      `;
    } else {
      notifFeedEl.innerHTML = `
        <div class="notif-item alert-urgent">
          <div class="notif-item-header">
            <span class="notif-item-tag tag-danger">DISCIPLINE FFF</span>
            <span class="notif-item-time">Aujourd'hui 09:30</span>
          </div>
          <div class="notif-item-title">4 joueurs sous sursis (Art. 226 FFF)</div>
          <div class="notif-item-body">
            Mathis L., Antoine B., Julien D. et Paul B. sont à un carton jaune de la suspension automatique. Risque financier évité de 250 €.
          </div>
        </div>
        <div class="notif-item alert-info">
          <div class="notif-item-header">
            <span class="notif-item-tag tag-primary">SCOUTING & CRA</span>
            <span class="notif-item-time">Hier 18:00</span>
          </div>
          <div class="notif-item-title">J-4 : Rapport Aniche SC disponible</div>
          <div class="notif-item-body">
            Consultez les forces adverses et les points vulnérables. Désignation de l'arbitre CRA attendue.
          </div>
        </div>
        <div class="notif-item alert-success">
          <div class="notif-item-header">
            <span class="notif-item-tag tag-success">DÉBRIEFING MATCH</span>
            <span class="notif-item-time">26/10 11:15</span>
          </div>
          <div class="notif-item-title">Tatinghem 0-1 Genech : 5ème Clean Sheet</div>
          <div class="notif-item-body">
            Victoire validée. Solidité défensive confirmée (0.44 but concédé/match). Cadence PPM consolidée à 1.75.
          </div>
        </div>
      `;
    }
  }
}

// 8. Démarrage Synchrone
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

if ('serviceWorker' in navigator && window.location.protocol.startsWith('http')) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  });
}
