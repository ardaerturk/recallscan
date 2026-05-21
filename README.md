# RecallScan

External recall signals. Mapped to your shelves.

RecallScan is an Exa-powered product-safety app for grocery QA teams. It scans public recall and supplier-risk content, extracts the facts, and maps them to a store catalog and inventory model.

The app uses real external sources through Exa. The included catalog and store inventory are seeded demo data because retailer inventory is private.

## Stack

- Next.js, TypeScript, Tailwind CSS
- FastAPI on Vercel
- Neon Postgres
- Exa Search and Contents
- Vercel Cron for scheduled refresh

## Run Locally

Create `.env.local`:

```bash
EXA_API_KEY=
DATABASE_URL=
APP_BASE_URL=http://localhost:3000
CRON_SECRET=
ALLOWED_ORIGINS=http://localhost:3000
FASTAPI_ORIGIN=http://127.0.0.1:8000
```

Then run:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
npm install
npm run dev
```

Open `http://localhost:3000`.

`DATABASE_URL` is required. The app uses Neon/Postgres locally and in production.

## Verify

```bash
npm run lint
npm run build
npm run test:api
```

## Deploy

Set the environment variables in Vercel, connect Neon, and deploy the repo. The API runs migrations on startup and seeds the starter catalog only when the catalog is empty.
