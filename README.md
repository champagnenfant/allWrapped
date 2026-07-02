# Music Wrapped

Suivi continu de l'écoute musicale multi-plateformes (Apple Music, YouTube,
SoundCloud, Spotify, Deezer...) avec stats évolutives tout au long de
l'année, plutôt qu'un récap unique en fin d'année.

## Structure

```
music-wrapped/
├── apps/
│   ├── backend/          FastAPI + Postgres, expose /api/plays et /api/stats/*
│   ├── frontend/          Next.js, dashboard des stats
│   └── sensor-windows/    Script qui capte la musique jouée sur le PC
├── infra/
│   └── docker-compose.yml
└── .env.example
```

## Démarrer en local

1. Copier `.env.example` en `.env` et ajuster si besoin
2. Lancer la DB + le backend :
   ```bash
   cd infra
   docker compose up --build
   ```
3. Vérifier que ça répond : http://localhost:8000/health
4. Lancer le sensor Windows (sur la machine qui écoute la musique, pas
   forcément la même que le serveur) :
   ```bash
   cd apps/sensor-windows
   pip install -r requirements.txt
   set SENSOR_BACKEND_URL=http://localhost:8000/api/plays
   set SENSOR_API_TOKEN=dev-token-change-me
   python music_tracker_sensor.py
   ```
5. Frontend : voir `apps/frontend/README.md` pour le scaffolding initial

## CI/CD

- `.github/workflows/backend-ci.yml` : lint/tests/build Docker à chaque
  changement dans `apps/backend/`
- `.github/workflows/frontend-ci.yml` : lint/build à chaque changement dans
  `apps/frontend/`
- Les deux ne se déclenchent que si le dossier concerné a changé (via
  `paths:` dans le workflow)

## Déploiement (à mettre en place)

Suggestion de plateformes, à connecter une fois le repo poussé sur GitHub :

| Composant | Plateforme suggérée | Notes |
|---|---|---|
| Backend | Railway ou Render | Déploiement via Dockerfile, connecté au repo |
| Frontend | Vercel | Auto-déploiement sur push, natif pour Next.js |
| Base de données | Supabase ou la Postgres managée de Railway | Remplace le Postgres du docker-compose en prod |

Une fois choisi, ajouter un job de déploiement dans les workflows CI
(déclenché uniquement sur `push` vers `main`, après que les tests passent),
ou utiliser le déploiement automatique natif de Vercel/Railway branché
directement sur GitHub (plus simple, pas besoin d'écrire le job toi-même).

## Prochaines étapes

- [ ] Pousser ce repo sur GitHub
- [ ] Connecter Railway/Render (backend) et Vercel (frontend) au repo
- [ ] Scaffolder le frontend (`apps/frontend/README.md`)
- [ ] Générer un vrai `API_TOKEN`/`SENSOR_API_TOKEN` (pas la valeur par défaut)
      et le mettre en secret GitHub Actions + variable d'env sur
      Railway/Vercel
- [ ] Affiner la détection de plateforme pour les onglets navigateur
      (YouTube vs SoundCloud) dans le sensor
