# Frontend

Pas encore scaffoldé. À faire une fois côté backend/CI validés :

```bash
cd apps/frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app
```

Conventions à respecter pour que `frontend-ci.yml` fonctionne tel quel :
- Le `package.json` doit avoir un script `lint` et un script `build`
  (générés par défaut par create-next-app, rien à faire normalement)
- Utiliser `NEXT_PUBLIC_API_URL` (voir `.env.example` à la racine) pour
  appeler le backend, jamais une URL en dur

Une fois scaffoldé, supprime ce README ou remplace-le par la doc du frontend.
