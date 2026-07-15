# AdsControl IA

Copiloto inteligente de solo lectura para Meta Ads: analiza campañas, anuncios y audiencias
mediante un motor híbrido de reglas + IA, y devuelve diagnósticos y recomendaciones priorizadas.
No ejecuta ni modifica nada en Meta Ads — el usuario aplica los cambios él mismo en Ads Manager.

## Estructura

- `frontend/` — Next.js 14 + TypeScript + TailwindCSS, desplegado en Vercel.
- `backend/` — FastAPI + SQLAlchemy + Alembic, expone la API que consume el frontend.

## Estado actual: Módulo 1 (Fundación)

- Autenticación con Supabase Auth (frontend) + validación de JWT en el backend.
- Esquema multi-tenant inicial: `orgs`, `org_members`, `ad_accounts` (con RLS).
- Endpoints: `GET /api/v1/health`, `GET /api/v1/me`, `POST /api/v1/orgs`.
- Dashboard: layout con sidebar + placeholder de resumen.

Próximos módulos: integración con Meta Ads (Módulo 2), motor de reglas (Módulo 3), capa de IA
(Módulo 4), dashboard con datos reales (Módulo 5) — ver el historial de la conversación de
planificación para el detalle de cada uno.

## Desarrollo local

### Backend

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate  # o source .venv/bin/activate en Unix
pip install -r requirements.txt
cp .env.example .env      # completa con tus credenciales de Supabase
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local  # completa con tus credenciales de Supabase
npm run dev
```
