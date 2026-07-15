# AdsControl IA

Copiloto inteligente de solo lectura para Meta Ads: analiza campañas, anuncios y audiencias
mediante un motor híbrido de reglas + IA, y devuelve diagnósticos y recomendaciones priorizadas.
No ejecuta ni modifica nada en Meta Ads — el usuario aplica los cambios él mismo en Ads Manager.

## Estructura

- `frontend/` — Next.js 14 + TypeScript + TailwindCSS, desplegado en Vercel.
- `backend/` — FastAPI + SQLAlchemy + Alembic, expone la API que consume el frontend.

## Estado actual

### Módulo 1 (Fundación)

- Autenticación con Supabase Auth (frontend) + validación de JWT en el backend.
- Esquema multi-tenant inicial: `orgs`, `org_members`, `ad_accounts` (con RLS).
- Endpoints: `GET /api/v1/health`, `GET /api/v1/me`, `POST /api/v1/orgs`.
- Dashboard: layout con sidebar + placeholder de resumen.

### Módulo 2 (Integración con Meta Ads — solo lectura)

- Permisos de Meta usados: **`ads_read` + `business_management` únicamente**. Nunca se pide ni
  se usa `ads_management`; no existe en el código ninguna llamada de escritura a la Graph API.
- Modelo de datos: `campaigns`, `ad_sets`, `ads`, `insight_snapshots` (snapshot diario por
  anuncio, base para detectar tendencias en el Módulo 3), `sync_jobs` (auditoría de cada sync).
- `access_token` de Meta cifrado en reposo (Fernet) antes de guardarse en `ad_accounts`.
- Endpoints: `GET /api/v1/meta/oauth-url`, `POST /api/v1/meta/callback`, `GET /api/v1/ad-accounts`,
  `POST /api/v1/ad-accounts/{id}/sync` (background task), `GET /api/v1/ad-accounts/{id}/sync-status`.
- Frontend: `/settings/integrations` (conectar cuenta, ver cuentas, sincronizar) y
  `/integrations/meta/callback` (recibe el `code` de Facebook Login).
- Tests con `meta_client` mockeado (`FakeMetaClient`): pipeline completo sin llamar a Meta real,
  y verificación de que el sync no duplica filas al correr dos veces (upsert por índice único).
- **Pendiente de tu lado:** crear la Meta App en developers.facebook.com y poner
  `META_APP_ID`/`META_APP_SECRET`/`TOKEN_ENCRYPTION_KEY` reales en el `.env` del backend para
  probar el flujo contra Meta de verdad.

### Módulo 3 (Motor de reglas)

- Modelo de datos: `rules` (condiciones configurables en JSON, `org_id = null` = regla global del
  sistema), `recommendations` (una por entidad+regla, sin duplicar mientras esté `pending`),
  `campaign_scores` (puntaje 0-100 + estado de salud, recalculado en cada sync).
- Motor de condiciones (`rules_engine/conditions.py`): operadores `gt/lt/gte/lte`,
  `decreased_by_pct` / `increased_by_pct` (compara contra N días atrás) y
  `sustained_above_for_days` / `sustained_below_for_days` (ej. "CPL alto 3 días seguidos").
  Si falta el dato de una métrica, la condición nunca dispara en falso positivo.
- 3 reglas semilla (fatiga de anuncio, CPL sostenido alto, oportunidad de escalar), insertadas
  automáticamente la primera vez que se evalúa una cuenta (`ensure_seed_rules`).
- El motor se dispara automáticamente al final de cada sync exitoso (`sync_service` →
  `evaluate_ad_account`), a nivel de anuncio, y agrega un puntaje por campaña.
- Endpoints: `GET /api/v1/ad-accounts/{id}/recommendations`,
  `POST /api/v1/recommendations/{id}/apply` (el usuario confirma que ya lo hizo él mismo en Ads
  Manager — no ejecuta nada en Meta), `POST /api/v1/recommendations/{id}/dismiss`,
  `GET /api/v1/ad-accounts/{id}/scores`, `GET/POST /api/v1/orgs/{id}/rules`.
- 12/12 tests: condiciones aisladas, evaluador con reglas semilla, e integración completa
  verificando que no se duplican recomendaciones al re-evaluar.

Próximos módulos: capa de IA (Módulo 4), dashboard con datos reales (Módulo 5) — ver el
historial de la conversación de planificación para el detalle de cada uno.

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
