# Audit HippoEdge — v6.5.1

Contrôle effectué avant livraison selon la méthode fusionnée des conversations « Historique complet cheval » et « Reprendre un ancien chat ».

## Contrôle fonctionnel

- [x] Pare-feu indépendant avant stockage et scoring : cotes, favoris, popularité, pronostics, sélections externes, avis, rapports, ratings et variantes anglaises supprimés récursivement.
- [x] Programme, partants, non-partants et résultats normalisés depuis le flux PMU public ; aucun compte n’est requis pour ce flux.
- [x] Historiques trot : LeTROT prioritaire, Geny complémentaire, identité exacte, dédoublonnage et priorité des faits officiels.
- [x] Galop français et étranger : France Galop reste une frontière officielle protégée ; Geny ne complète que lorsque l’identité est vérifiée.
- [x] Galop/trot étrangers : les lignes Geny objectives sont admissibles pour les courses présentes au programme ; aucune source à compte, CAPTCHA ou abonnement n’est aspirée silencieusement.
- [x] Chaque partant actif reçoit cinq notes indépendantes et un paragraphe factuel ; les références objectives visibles sont conservées dans le détail mobile.
- [x] Musique officielle utilisée comme preuve provisoire si l’historique détaillé est encore en récupération ; sans aucune preuve, aucune sélection n’est fabriquée.
- [x] Faible échantillon, progression, fautes, chronos, aptitude, poids/valeur, corde/départ, ferrure, potentiel caché, robustesse et volatilité traités séparément.
- [x] Cheval du jour, meilleur placé, outsider, tocard et cheval de cœur calculés séparément par réunion et sur l’ensemble de la journée ; aucune diversité artificielle.
- [x] Snapshot pré-course identifié et verrouillable ; une arrivée ne recalcule ni ne rétrograde une analyse officielle.
- [x] Arrivées provisoires et officielles affichées, y compris lorsqu’un ordre provisoire est encore vide.
- [x] Navigation mobile : Sélections → Réunions → Courses → Analyse détaillée → Arrivées/Bilan/Réglages.
- [x] Import rapide du programme et des résultats ; récupération historique lente isolée en arrière-plan pour éviter les erreurs réseau pendant l’actualisation.

## Vérifications exécutées

- Suite backend : **36 passed**.
- Compilation Python de tous les modules et tests : OK.
- TypeScript mobile (`tsc --noEmit`) : OK.
- Bundle Android Expo (`expo export --platform android`) : OK.
- Test d’intégration en mode démo : `/health` 200, rafraîchissement 200, 2 réunions, 4 courses, sélections prêtes, analyse avec phase de snapshot explicite.

Les accès privés, clés de licence et mots de passe ne sont pas enregistrés dans le projet.
