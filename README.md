# ES Genech - Cellule Data & Performance Régionale

Projet conçu pour l'analyse de performance sportive du football amateur et semi-professionnel (Régional 3 Hauts-de-France & Coupe de France).

## 1. Architecture des Données

Le projet repose sur un pipeline automatisé en Python :
1. **Scraping Stealth (Playwright)** : Contournement automatique des verrous Akamai de la FFF sans recourir à des exports manuels.
2. **Stockage Relationnel (SQLite)** : `genech_performance.db`.
3. **Moteur d'Analyse (Pandas)** : Calcul des dynamiques par quart d'heure, radars disciplinaires, et métriques de coaching.
4. **Restitution Décisionnelle (Power BI Desktop)** : Modèle en étoile prêt à l'emploi via les fichiers du dossier `exports_powerbi/`.

## 2. Structure de la Base de Données (`genech_performance.db`)

* `competitions` : Identifiants et métadonnées (R3 Poule D, Coupe de France).
* `classement_poule` : Classement actualisé avec points, matchs joués.
* `matchs` : Calendrier, adversaires, scores et statuts.
* `match_events` : Granularité minute par minute (Buts, Cartons Jaunes, Cartons Rouges, Remplacements) avec tag quart d'heure (`01-15'`, `16-30'`, ..., `76-90+'`).
* `match_lineups` : Compositions complètes (Titulaires et remplaçants).

## 3. Données Clés Extraites (Saison en cours)

* **Parcours Coupe de France de l'ES Genech** :
  * Tour 2 : Lys Lez Lannoy 0 - 0 Genech
  * Tour 3 : Sainghin Weppes 0 - 1 Genech
  * Tour 4 : Genech 2 - 0 Dunkerque Malo FC
  * Tour 5 : Genech 1 - 0 US Chantilly (Exploit National 1 - But de Julien Nisse à la 77')
  * Tour 6 (Finale Régionale) : St Martin Tatinghem vs Genech (À venir)
* **Stats défensives Coupe de France** : **0 but concédé en 4 matchs (4 Clean Sheets consécutifs)**.
* **Dynamique offensive** : 75 % des buts de l'ES Genech sont inscrits en seconde période, avec un pic dans le "Money Time" (76-90+').

## 4. Utilisation

1. Pour rafraîchir les données de la semaine :
   ```bash
   python scraper.py
   ```
2. Pour générer les analyses et mettre à jour les exports Power BI :
   ```bash
   python analytics.py
   ```
3. Ouvrir Power BI Desktop et lier le dossier `exports_powerbi/`.
