# SchoolDimes admin dashboard

Next.js (App Router) web app for school admins, platform staff, the student
portal and the public contributor page. See the bottom of this file for pages.

## Setup

```bash
# 1. backend (repo root)
docker compose up --build -d
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py simulate_pos   # optional sample sales

# 2. dashboard
cd admin-dashboard
cp .env.example .env.local
npm install
npm run dev            # http://localhost:3000
```

## Environment variables

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Django origin, e.g. `http://localhost:8000` |
| `API_BASE_URL` | optional server-side origin (e.g. `http://web:8000` inside Docker) |
| `NEXT_PUBLIC_SITE_URL` | this dashboard's public URL (contributor links are `<this>/give/<token>`) |
| `COOKIE_SECURE` | `true` behind HTTPS |

## Tests

```bash
npm test         # unit (Vitest)
npm run e2e      # end-to-end (Playwright), needs backend + seed + `npm run dev`
```
