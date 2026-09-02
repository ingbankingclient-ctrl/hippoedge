# HippoEdge — déploiement gratuit, PC éteint

Cette procédure met l’API et l’interface iPhone en ligne sans dépendre du PC familial.

## Architecture

- Render Web Service gratuit : backend FastAPI dans `backend/`.
- Supabase Free : base PostgreSQL persistante.
- Render Static Site gratuit : export web Expo dans `mobile/dist/`.
- Safari iPhone : **Partager → Sur l’écran d’accueil** pour obtenir l’icône HippoEdge.

## 1. Mettre cette livraison sur GitHub

Remplacer le contenu du dépôt `hippoedge` par le contenu de cette archive, sans envoyer `.env`, `.venv`, `node_modules`, `dist`, les caches Python ou `hippoedge.db`.

## 2. Créer la base Supabase

Créer un projet Free, conserver le mot de passe de base uniquement dans le gestionnaire de secrets, puis copier l’URL PostgreSQL fournie par Supabase. Ne jamais publier cette URL dans GitHub.

## 3. Déployer l’API Render

Créer un Web Service depuis le dépôt GitHub :

- Runtime : Docker
- Root Directory : `backend`
- Instance Type : Free
- Health Check Path : `/health`

Variables :

```env
HIPPOEDGE_ENVIRONMENT=production
HIPPOEDGE_PROVIDER=pmu
HIPPOEDGE_DATABASE_URL=<URL PostgreSQL Supabase>
HIPPOEDGE_CORS_ORIGINS=*
```

Après le déploiement, ouvrir `https://<service>.onrender.com/health` et vérifier `"ok": true`.

## 4. Déployer l’interface Render

Créer un Static Site depuis le même dépôt :

- Root Directory : `mobile`
- Build Command : `npm ci && npm run build:web`
- Publish Directory : `dist`
- Instance Type : Free

Variable de compilation :

```env
EXPO_PUBLIC_API_URL=https://<service-api>.onrender.com
```

## 5. Installer sur l’iPhone

Ouvrir l’adresse HTTPS du Static Site dans Safari, toucher **Partager**, puis **Sur l’écran d’accueil** et **Ajouter**. HippoEdge s’ouvre ensuite depuis sa propre icône et ne nécessite plus Expo Go, Metro, PowerShell, Tailscale ou un PC allumé.

## Limites gratuites

- L’API Render se met en veille après une période sans requête ; prévoir jusqu’à environ une minute pour la première ouverture.
- Ouvrir l’app puis toucher **Actualiser** pour déclencher l’import le plus récent après un sommeil du serveur.
- Supabase peut mettre en pause un projet Free longtemps inactif ; une utilisation régulière évite normalement ce cas.
- Ne jamais ajouter de moyen de paiement ni sélectionner une instance payante si l’objectif est de rester à 0 €.
