# Churn Prediction Model Comparison Dashboard

Full-stack MVP for comparing TFT and TabNet churn prediction models for a graduation project.

## Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, lightweight SVG/CSS charts
- Backend: FastAPI, Python, mock JSON data

## Run Everything

From the project root:

```bash
npm.cmd run dev
```

If the frontend ever shows a stale error page during development:

```bash
npm.cmd run stop
npm.cmd run clean-frontend
npm.cmd run dev
```

This starts:

- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`

Press `Ctrl+C` in the terminal to stop both servers.

## Run Optimized Demo Mode

For presentation day, build once and run the production frontend server:

```bash
npm.cmd run prepare-demo
npm.cmd run demo
```

This avoids slow Next.js development-mode route compilation during the demo.

## Dashboard Routes

- `/` - landing page and project workflow
- `/models` - global TFT and TabNet metric comparison
- `/customers` - random customer selection from the demo sample
- `/predictions/[customer_id]` - customer-level prediction comparison
- `/explainability/[customer_id]` - placeholder model explainability views

## Run Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs will be available at:

```text
http://localhost:8000/docs
```

## Run Frontend

```bash
cd frontend
npm install
npm.cmd run dev
```

Open:

```text
http://localhost:3000
```

The frontend reads the API base URL from `NEXT_PUBLIC_API_BASE_URL`. By default it uses `http://localhost:8000`.

## Notes

- The dashboard assumes a demo sample of roughly 1000-5000 customers, not the full 14 GB dataset.
- TFT and TabNet predictions use local model artifacts when available, with validated fallbacks for demo safety.
- For presentations, prefer `npm.cmd run prepare-demo` followed by `npm.cmd run demo` from the project root.
