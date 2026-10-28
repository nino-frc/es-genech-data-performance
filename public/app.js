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
  const title = isWelcome ? 'MatchDay - Notifications Activées 🎉' : 'MatchDay - Alerte Staff ES Genech 🚨';
  const body = isWelcome
    ? 'Vous recevrez les alertes de suspension FFF, briefings et debriefings en direct sur cet appareil.'
    : 'Commission FFF : 4 joueurs sous sursis avant le déplacement à Aniche SC (Art. 226). 250 € préservés.';

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
  const genech = lineups.genech || {};
  const opp = lineups.adversaire || {};
  const lineupContentEl = document.getElementById('detailLineupContent');

  let lineupHtml = `
    <div class="lineup-section-title">
      <span>🟡🔵 ES GENECH (Titulaires)</span>
      <span style="font-family: var(--font-mono);">${genech.titulaires ? genech.titulaires.length : 0} joueurs</span>
    </div>
    <div class="lineup-grid">
  `;

  if (genech.titulaires && genech.titulaires.length > 0) {
    genech.titulaires.forEach(p => {
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
      <span>🟡🔵 ES GENECH (Remplaçants)</span>
      <span style="font-family: var(--font-mono);">${genech.remplacants ? genech.remplacants.length : 0} joueurs</span>
    </div>
    <div class="lineup-grid">
  `;

  if (genech.remplacants && genech.remplacants.length > 0) {
    genech.remplacants.forEach(p => {
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
  const link = document.createElement('a');
  link.href = './rapport_executif_mensuel.pdf';
  link.download = 'MatchDay_Rapport_Executif_ES_Genech.pdf';
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showNotification('Téléchargement du rapport exécutif PDF lancé !');
}

function printExecutiveReport() {
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
  // A. Récupération de l'équipe sélectionnée (Persistance localStorage)
  let savedTeam = 'SENIOR_M1';
  try {
    savedTeam = localStorage.getItem('matchday_active_team') || 'SENIOR_M1';
  } catch (e) {}
  currentTeamId = savedTeam;

  const sel = document.getElementById('teamSelector');
  if (sel) {
    sel.value = savedTeam;
  }

  if (window.MATCHDAY_TEAMS && window.MATCHDAY_TEAMS[savedTeam]) {
    globalData = window.MATCHDAY_TEAMS[savedTeam];
    renderInterface(globalData);
  } else if (window.MATCHDAY_DATA) {
    globalData = window.MATCHDAY_DATA;
    renderInterface(window.MATCHDAY_DATA);
  }

  dismissSplashScreen();
  fetchMatchDayFromApi();
  updateNotifUI();
}

// 7. Rendu DOM Dynamique Complet
function renderInterface(data) {
  if (!data) return;

  // A. Header
  const activeClub = data.equipe_active || {};
  const clubNameEl = document.getElementById('activeClubName');
  if (clubNameEl) {
    clubNameEl.textContent = `${activeClub.nom || 'ES Genech'} (${activeClub.poule || 'R3'})`;
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

  // E bis. Historique Exhaustif des Matchs Passés (Saison 2026-2027)
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
        <button class="history-filter-btn active" onclick="filterMatchHistory('ALL', this)">Tous (9)</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('R3', this)">Régional 3 (4)</button>
        <button class="history-filter-btn" onclick="filterMatchHistory('CDF', this)">Coupe de France (5)</button>
      `;
    } else {
      filterBar.innerHTML = `
        <button class="history-filter-btn active" onclick="filterMatchHistory('ALL', this)">Tous les matchs (${historyList.length})</button>
      `;
    }
  }
  if (historyContainer) {
    if (historyList.length > 0) {
      let historyHtml = '';
      historyList.forEach((m, idx) => {
        let pillClass = 'score-pill-win';
        let tagClass = 'win';
        if (m.resultat === 'N') {
          pillClass = 'score-pill-draw';
          tagClass = 'draw';
        } else if (m.resultat === 'D') {
          pillClass = 'score-pill-loss';
          tagClass = 'loss';
        }

        const isHomeGenech = m.domicile.toUpperCase().includes('GENECH');
        const isAwayGenech = m.exterieur.toUpperCase().includes('GENECH');

        historyHtml += `
          <div class="match-history-card" data-comp-type="${m.comp_type}" onclick="openMatchDetailModal(${idx})">
            <div class="match-history-header">
              <span class="tactical-role-pill" style="font-size: 9px; padding: 1px 6px;">${m.competition}</span>
              <span>${m.date}</span>
            </div>
            <div class="match-history-main">
              <div class="match-history-team home ${isHomeGenech ? 'highlight-genech' : ''}">
                ${m.domicile}
              </div>
              <div class="match-history-score-wrapper">
                <span class="score-pill ${pillClass}">${m.score_display}</span>
                <span class="match-history-res-tag ${tagClass}">${m.resultat_label}</span>
              </div>
              <div class="match-history-team away ${isAwayGenech ? 'highlight-genech' : ''}">
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
      players.forEach((p, idx) => {
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
  }

  // I. Classement Poule D
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
        const isGenech = st.equipe.includes('GENECH');
        tableHtml += `
          <tr class="${isGenech ? 'highlight-team' : ''}">
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
