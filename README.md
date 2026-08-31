# HippoEdge — application mobile d’analyse hippique indépendante

HippoEdge est un produit complet **mobile + API** conçu pour analyser automatiquement les réunions/courses PMU à **J+1** en appliquant une méthode indépendante des cotes, favoris et pronostics externes.

## Ce qui est déjà livré

- Application mobile iPhone/Android via **Expo / React Native**.
- API **FastAPI**.
- Base SQLAlchemy : SQLite par défaut, PostgreSQL possible via `DATABASE_URL`.
- Import automatique **jour J + J+1**.
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

Deux modes sont fournis :

### 1. `demo`
Fonctionne immédiatement, sans compte ni clé. Il permet de tester toute l’application de bout en bout.

### 2. `turfbzh`
Connecteur réel déjà implémenté pour : programme, fiche exacte de course, partants, historique cheval et résultats. Il faut votre propre licence/clé API.

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
HIPPOEDGE_PROVIDER=turfbzh
HIPPOEDGE_TURFBZH_API_KEY=VOTRE_CLE
```

Redémarrez l’API. Le scheduler importe automatiquement aujourd’hui et demain, enrichit les historiques, calcule les analyses et verrouille les snapshots juste avant le départ.

## Endpoints principaux

- `GET /health`
- `POST /api/refresh?day=2026-09-01`
- `GET /api/program/2026-09-01`
- `GET /api/tomorrow`
- `GET /api/races/{race_id}/analysis`
- `POST /api/races/{race_id}/lock`
- `GET /api/stats`

## Déploiement

Un `Dockerfile` et `docker-compose.yml` sont fournis. Pour un vrai lancement public :

1. héberger l’API derrière HTTPS ;
2. passer `HIPPOEDGE_PROVIDER=turfbzh` ou brancher des flux licenciés ;
3. utiliser PostgreSQL si le trafic devient important ;
4. construire/sign­er l’app avec Expo EAS pour App Store / Google Play ;
5. respecter les droits de redistribution des données de chaque fournisseur.

## Qualité vérifiée

Tests backend :

```bash
cd backend
PYTHONPATH=. pytest -q
```

État au moment de la livraison : **3 tests passés**.

## Limite honnête

Le code est complet et fonctionnel de bout en bout. Ce qui ne peut pas être inclus dans un ZIP est : votre clé/licence de données, votre domaine/serveur public, et vos certificats/comptes Apple/Google nécessaires à la publication dans les stores. Ces éléments appartiennent au propriétaire de l’application.
