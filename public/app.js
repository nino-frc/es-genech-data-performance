/**
 * MatchDay PWA - Client Script & Alimentation Dynamique
 * Gestion du Splash Screen, Logo et Rendu Détaillé de la Discipline
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

// 2. Gestion du Splash Screen (Écran de chargement)
function dismissSplashScreen() {
  const splash = document.getElementById('splashScreen');
  if (splash) {
    setTimeout(() => {
      splash.classList.add('hidden');
      setTimeout(() => {
        splash.style.display = 'none';
      }, 500);
    }, 900); // 900ms pour apprécier le logo et le nom
  }
}

// 3. Initialisation de l'Application
function initApp() {
  // A. Rendu immédiat des données
  if (window.MATCHDAY_DATA) {
    renderInterface(window.MATCHDAY_DATA);
  }

  // B. Masquer le splash screen
  dismissSplashScreen();

  // C. Actualisation distante en arrière-plan (si hébergé sur Netlify)
  refreshFromRemote();
}

async function refreshFromRemote() {
  if (window.location.protocol === 'file:') return;

  const urlParams = new URLSearchParams(window.location.search);
  const teamToken = urlParams.get('team') || urlParams.get('token');

  try {
    const netlifyRes = await fetch(`/.netlify/functions/get_team_data?team=${teamToken || '525674_SENIOR_M1'}`);
    if (netlifyRes.ok) {
      const data = await netlifyRes.json();
      renderInterface(data);
    }
  } catch (e) {
    // Si la fonction serverless n'est pas configurée, data.js est déjà affiché
  }
}

// 4. Rendu DOM Dynamique
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

  // C. Les 4 Vrais KPIs de Saison Fanion
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
        const hasRed = p.cartons_r > 0 ? `<span>🟥 ${p.cartons_r}</span>` : '';
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

  // F. VEILLE DISCIPLINAIRE DÉTAILLÉE : Cartons Rouges & Sursis
  // F1. Détail Nominatif des Cartons Rouges
  const redCardsContainer = document.getElementById('redCardsContainer');
  const redCards = data.cartons_rouges_details || [];
  if (redCardsContainer) {
    if (redCards.length > 0) {
      let redHtml = '';
      redCards.forEach(rc => {
        const badgeCls = rc.est_suspendu ? 'status-active-red' : 'status-purged';
        redHtml += `
          <div class="discipline-card-detail red-card">
            <div class="discipline-row-header">
              <span>🟥 <strong>${rc.joueur}</strong> (${rc.minute}')</span>
              <span class="discipline-status-badge ${badgeCls}">${rc.statut_purge}</span>
            </div>
            <div class="discipline-subline">
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

  // F2. Détail Nominatif des Sursis (2 Jaunes)
  const sursisContainer = document.getElementById('sursisContainer');
  const sursis = data.sursis_details || [];
  if (sursisContainer) {
    if (sursis.length > 0) {
      let sursisHtml = '';
      sursis.forEach(s => {
        sursisHtml += `
          <div class="discipline-card-detail sursis-card">
            <div class="discipline-row-header">
              <span>⚠️ <strong>${s.joueur}</strong></span>
              <span style="font-size: 10px; color: #92400e; font-weight: 700;">Échéance : ${s.expiration}</span>
            </div>
            <div class="discipline-subline">
              2 cartons reçus (${s.dates}). Prochain avertissement = <strong>1 match ferme de suspension</strong>.
            </div>
          </div>
        `;
      });
      sursisContainer.innerHTML = sursisHtml;
    } else {
      sursisContainer.innerHTML = "<div style='font-size: 11px; color: var(--color-green); padding: 6px;'>✅ Aucun joueur sous le coup d'un sursis actuellement.</div>";
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

// 5. Lancement Synchrone
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
