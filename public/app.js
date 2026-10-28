/**
 * MatchDay PWA - Client Script & Alimentation Dynamique
 * Rendu synchrone immédiat (0ms de chargement, fonctionne en local file:// et en ligne)
 */

// 1. Navigation au Pouce (Bottom Nav)
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

// 2. Initialisation Synchrone Immédiate
function initApp() {
  // A. Si les données réelles sont présentes via data.js (Synchrone, 0 délai, marche en file:// et en ligne)
  if (window.MATCHDAY_DATA) {
    renderInterface(window.MATCHDAY_DATA);
  }

  // B. En arrière-plan (si hébergé sur Netlify avec Serverless Function)
  refreshFromRemote();
}

async function refreshFromRemote() {
  const urlParams = new URLSearchParams(window.location.search);
  const teamToken = urlParams.get('team') || urlParams.get('token');

  // Si ouvert en protocole file://, on ne fait pas de fetch pour éviter les erreurs CORS
  if (window.location.protocol === 'file:') {
    return;
  }

  try {
    const netlifyRes = await fetch(`/.netlify/functions/get_team_data?team=${teamToken || '525674_SENIOR_M1'}`);
    if (netlifyRes.ok) {
      const data = await netlifyRes.json();
      renderInterface(data);
    }
  } catch (e) {
    // Si la fonction serverless n'est pas encore déployée, data.js a déjà rendu l'écran
  }
}

// 3. Rendu DOM Dynamique
function renderInterface(data) {
  if (!data) return;

  // A. Header & Identité
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

  // C. Les 4 Vrais KPIs de Saison
  const kpis = data.kpis_saison || {};
  const goalsEl = document.getElementById('kpiGoals');
  const csEl = document.getElementById('kpiCleanSheets');
  const minEl = document.getElementById('kpiTotalMinutes');
  const cardsEl = document.getElementById('kpiCardsSummary');

  if (goalsEl) goalsEl.textContent = kpis.buts_marques ?? '--';
  if (csEl) csEl.textContent = kpis.clean_sheets ?? '--';
  if (minEl) minEl.textContent = kpis.minutes_cumulees ? `${kpis.minutes_cumulees.toLocaleString()}m` : '--';
  if (cardsEl) cardsEl.textContent = `${kpis.cartons_jaunes ?? 0} J. / ${kpis.cartons_rouges ?? 0} R.`;

  // D. Chronologie des Événements
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
      timelineContainer.innerHTML = "<div style='color: var(--text-light); font-size: 11px; text-align: center; padding: 8px;'>Aucun événement officiel renseigné pour ce match.</div>";
      timelineContainer.classList.remove('skeleton');
    }
  }

  // E. Effectif Joueurs & Score ESG (0-100)
  const playersContainer = document.getElementById('playersListContainer');
  const players = data.effectif_esg || [];
  if (playersContainer) {
    if (players.length > 0) {
      let playersHtml = '';
      players.forEach(p => {
        playersHtml += `
          <div class="player-row">
            <div class="player-left">
              <div class="player-rank">${p.rang}</div>
              <div>
                <div class="player-name-text">${p.nom}</div>
                <div class="player-stats-mini">
                  <span>⏱️ ${p.minutes}m</span>
                  <span>⚽ ${p.buts}</span>
                  <span>🛡️ ${p.clean_sheets} CS</span>
                  <span>🟨 ${p.cartons_j}</span>
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

  // F. Alertes Disciplinaires (Art. 226 FFF)
  const discContainer = document.getElementById('disciplineAlertsContainer');
  const alerts = data.alertes_discipline || [];
  if (discContainer) {
    if (alerts.length > 0) {
      let alertsHtml = '';
      alerts.forEach(a => {
        const isDanger = a.includes('Suspendu') || a.includes('3e carton');
        const cls = isDanger ? 'suspendu' : 'sursis';
        const icon = isDanger ? '🚨' : '⚠️';
        alertsHtml += `
          <div class="discipline-row ${cls}">
            <span style="font-size: 16px;">${icon}</span>
            <div>${a.replace('🚨', '').replace('⚠️', '').trim()}</div>
          </div>
        `;
      });
      discContainer.innerHTML = alertsHtml;
      discContainer.classList.remove('skeleton');
    } else {
      discContainer.innerHTML = "<div class='discipline-row sursis' style='background: var(--color-green-light); border-color: #bbf7d0; color: var(--color-green);'>✅ Aucune suspension ni sursis en cours dans l'effectif.</div>";
      discContainer.classList.remove('skeleton');
    }
  }

  // G. Classement Poule D
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
    }
  }
}

// 4. Initialisation Synchrone dès le chargement du DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

// Service Worker (PWA offline)
if ('serviceWorker' in navigator && window.location.protocol.startsWith('http')) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  });
}
