# HippoEdge — application mobile d’analyse hippique indépendante

HippoEdge est un produit complet **mobile + API** conçu pour analyser automatiquement les réunions/courses PMU du jour et du lendemain en appliquant une méthode indépendante des cotes, favoris et pronostics externes.

La version **v6.5.1 — Audit final + Analyse approfondie + Interface mobile 2026** associe l’identité visuelle noir obsidienne/doré champagne à une page d’accueil dédiée aux sélections du jour, des menus mobiles Réunion/Course et un écran Arrivées avec statuts provisoire/officiel. Les titres Cheval du jour et Meilleur placé ne sont plus attribués au simple maximum d’une note brute : tous les chevaux sont comparés selon la profondeur des preuves, la forme, la classe, l’aptitude, la robustesse et l’incertitude, sans exclure automatiquement les jeunes profils peu expérimentés.

## Ce qui est déjà livré

- Application mobile iPhone/Android via **Expo / React Native**.
- API **FastAPI**.
- Base SQLAlchemy : SQLite par défaut, PostgreSQL possible via `DATABASE_URL`.
- Import automatique **jour J + J+1**.
- Accueil « Sélections du jour », menu mobile Réunion → Course et écran dédié aux arrivées provisoires/officielles.
- Programme → réunions → courses → partants → historique chevaux.
- Analyse automatique de chaque course.
- Cinq lectures par cheval :
  - Performance / Victoire
  - Profil Placé / Sécurité
  - Potentiel caché
  - Robustesse au scénario
  - Incertitude / volatilité
- Paramètres spécifiques :
  - galop : poids, valeur, corde, distance, terrain, progression, aptitude piste/distance ;
  - trot attelé : chronos, autostart, position, départ, ferrure, faute, niveau, aptitude ;
  - trot monté : références monté, poids, chronos monté, fautes, parcours, régularité technique ;
  - obstacles : forme, classe, aptitude terrain/distance, poids et régularité.
- Règles méthodologiques renforcées :
  - la performance propre domine les lignes indirectes ;
  - une ligne indirecte ne sert que de confirmation ;
  - comparaison du chrono au niveau réel du lot ;
  - DAI récente = pénalité de sécurité, mais n’efface pas automatiquement la valeur ;
  - régularité sur 2–3 courses plafonnée à cause du faible échantillon ;
  - progression des jeunes chevaux valorisée ;
  - bon numéro autostart seulement modérément valorisé sans preuve de vitesse/d’expérience ;
  - poids/corde/configuration favorables ne remplacent jamais la preuve de niveau ;
  - potentiel caché = ancienne valeur + forme masquée + conditions du jour ;
  - robustesse au scénario et volatilité traitées séparément.
- Snapshot pré-course **verrouillable** et verrouillage automatique avant le départ.
- Résultats post-course + statistiques sans réécriture rétroactive.
- Tests automatiques du scoring et du pare-feu anti-pronostics.

## Pare-feu d’indépendance

Le connecteur de données passe toutes les réponses par `sanitize_objective_payload()`.

Sont supprimés avant stockage/scoring : cotes, favoris, popularité, Note IA, Cote BZH, value bets, pronostics, sélections, avis et classements externes.

Le moteur ne voit donc que la donnée objective autorisée. Le texte affiché par l’app confirme :

> Je confirme que le moteur n'utilise volontairement ni classements, ni pronostics, ni favoris, ni cotes, ni popularité, ni avis éditoriaux. La liste des partants provient de la fiche de course et les scores sont construits uniquement à partir des données objectives de course et de performance disponibles.

## Sources de données

Trois modes sont fournis :

### 1. `demo`
Fonctionne immédiatement, sans compte ni clé. Il permet de tester toute l’application de bout en bout.

### 2. `pmu` — mode recommandé
Connecteur officiel sans clé pour le programme, la fiche exacte de course, les partants, les non-partants et les arrivées. Les chevaux de trot sont enrichis en lecture seule depuis leurs performances publiques LeTROT : date, rang, nombre de partants, chrono, distance/recul, hippodrome, catégorie et spécialité.

La v6.1 ajoute un complément public Geny fondé sur l’identifiant exact du cheval fourni par le programme PMU. Il couvre le galop français ainsi que les réunions étrangères de galop et de trot présentes au programme PMU. Pour le trot, LeTROT reste prioritaire et Geny complète les champs manquants ou les lignes absentes. Pour le galop, Geny sert de solution de repli tant que les fiches France Galop imposent une connexion officielle.

La correspondance ne repose jamais sur le nom seul : l’identifiant numérique PMU/Geny et le nom de la fiche doivent concorder. En cas de doute ou d’homonyme, aucune ligne n’est importée et l’incertitude de l’analyse augmente. Les cotes, rapports, favoris, avis Geny, pronostics, synthèses de presse, classements et notes externes ne sont jamais lus par le parseur et sont également bloqués par le pare-feu avant stockage.

Pour les courses étrangères, la hiérarchie prévue est : source locale officielle lorsqu’elle est publiquement automatisable, puis Geny pour les courses intégrées au programme PMU. Les références de contrôle comprennent notamment Equibase (galop États-Unis), HKJC (Hong Kong), USTA Pathway (trot États-Unis), Svensk Travsport (trot Suède) et Standardbred Canada. Ces services ne sont pas présentés comme automatiquement connectés lorsqu’ils exigent un compte, un CAPTCHA, un abonnement ou une autorisation de réutilisation.

### 3. `turfbzh` — connecteur optionnel historique
Connecteur tiers conservé pour compatibilité, désactivé par défaut.

**Important :** même si le fournisseur expose aussi des cotes ou indicateurs propriétaires, ces champs sont supprimés par le pare-feu HippoEdge et ne participent pas aux scores.

L’architecture `RacingProvider` permet d’ajouter ensuite des connecteurs autorisés/licenciés France Galop, LeTROT ou d’autres bases internationales sans modifier le moteur.

## Démarrage rapide — mode démo

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\\Scripts\\activate
pip install -r requirements.txt
cp ../.env.example ../.env
python run.py
```

API : `http://127.0.0.1:8000`
Swagger : `http://127.0.0.1:8000/docs`

### Mobile

```bash
cd mobile
npm install
npm start
```

Scannez le QR Expo Go sur iPhone/Android.

Sur un téléphone physique, dans l’onglet **Réglages**, remplacez `127.0.0.1` par l’IP locale de l’ordinateur, par exemple :

`http://192.168.1.25:8000`

## Activer les vraies courses

Copiez `.env.example` en `.env` puis :

```env
HIPPOEDGE_PROVIDER=pmu
```

Redémarrez l’API. Le scheduler importe d’abord rapidement aujourd’hui et demain avec les partants et les arrivées, puis récupère les historiques détaillés en arrière-plan. Les analyses sont recalculées dès qu’une ligne objective arrive et les snapshots sont verrouillés juste avant le départ.

## Endpoints principaux

- `GET /health`
- `POST /api/refresh?day=2026-09-01`
- `GET /api/program/2026-09-01`
- `GET /api/tomorrow`
- `GET /api/day/{date}/selections`
- `GET /api/races/{race_id}/analysis`
- `POST /api/races/{race_id}/lock`
- `GET /api/stats`

## Déploiement gratuit — PC éteint

La livraison cloud fournit `render.yaml` pour deux services gratuits :

1. `hippoedge-api` : API FastAPI/Docker sur Render ;
2. `hippoedge-mobile` : version web installable sur l’écran d’accueil de l’iPhone ;
3. une base PostgreSQL externe gratuite, recommandée sur Supabase, afin que les analyses et snapshots survivent aux redémarrages.

Variables obligatoires :

```env
HIPPOEDGE_DATABASE_URL=postgresql://...
EXPO_PUBLIC_API_URL=https://hippoedge-api.onrender.com
```

Le code convertit automatiquement les URL `postgres://` et `postgresql://` vers le pilote Psycopg. En production, `run.py` utilise le port fourni par l’hébergeur et désactive le rechargement de développement.

Limite honnête du niveau gratuit : l’API Render s’endort après une période sans requête. La première ouverture peut donc prendre environ une minute, puis l’application fonctionne normalement. Comme le serveur ne travaille pas pendant son sommeil, utiliser **Actualiser** à l’ouverture pour récupérer le programme et les arrivées récents.

Consultez `CLOUD_DEPLOYMENT.md` pour la procédure complète sans offre payante.

## Qualité vérifiée

La liste de contrôle détaillée est conservée dans `AUDIT_CHECKLIST.md`.

Tests backend :

```bash
cd backend
PYTHONPATH=. pytest -q
```

État au moment de la livraison v6.5.2-cloud : le programme et les arrivées sont importés rapidement, l’enrichissement historique s’exécute séparément, les snapshots post-départ sont exclus des sélections et une arrivée officielle ne peut plus être rétrogradée en provisoire. La suite contient **36 tests backend**, dont les contrôles du faible échantillon, de la musique officielle, du pare-feu, des sources historiques, des fuseaux horaires et du cycle provisoire/officiel. La méthode de calcul reste `2026.09.02-v6.5.1` : la révision cloud ne modifie aucun score ni aucune règle de sélection.

## Limite honnête

Le code est complet et fonctionnel de bout en bout. La version web installable évite les frais Apple et fonctionne sans Expo Go une fois mise en ligne. Une publication native dans l’App Store nécessiterait en revanche les certificats et le compte développeur du propriétaire de l’application.
