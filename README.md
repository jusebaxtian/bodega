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

### Módulo 4 (Capa de IA)

- La IA (Claude, vía Anthropic SDK) **nunca recibe las tablas crudas ni recalcula métricas**:
  recibe un resumen ya armado por `summary_builder` (métricas actuales, tendencia vs. 7 días
  atrás, reglas que dispararon, puntaje de campaña) y solo redacta el diagnóstico.
  Ver el prompt exacto en `app/services/ai/prompts.py`.
- Salida validada con Pydantic (`AIExplanationResult`): problema principal, gravedad, diagnóstico,
  acciones inmediatas, acciones a 72h, confianza y explicación en lenguaje simple. Si el modelo
  responde algo no parseable, se reintenta una vez y si vuelve a fallar se degrada a un mensaje
  genérico — el endpoint nunca se rompe por un JSON inválido del LLM.
- Caché simple: si ya existe una explicación de hoy para la entidad, no se vuelve a llamar al LLM.
- Endpoints: `POST /api/v1/ai/explain` (`{entity_type: "ad", entity_id}`, por ahora solo a nivel
  de anuncio), `GET /api/v1/ai/explanations/{entity_type}/{entity_id}`.
- Frontend: `components/AIExplanationCard.tsx`, listo para insertarse en la vista de anuncio del
  Módulo 5 (aún no hay una página de detalle de anuncio con datos reales donde montarlo).
- 19/19 tests: parseo válido, reintento tras JSON inválido, degradación sin excepción, caché del
  endpoint (el LLM fake se llama una sola vez aunque se pida el diagnóstico dos veces el mismo día).
- **Pendiente de tu lado:** poner `ANTHROPIC_API_KEY` real en el `.env` del backend para que las
  llamadas usen Claude de verdad en vez del cliente mockeado de los tests.

### Módulo 5 (Dashboard con datos reales)

- `dashboard_service.py` agrega lo que los módulos anteriores ya calcularon (snapshots más
  recientes por anuncio, `campaign_scores`, `recommendations` pendientes) en dos vistas:
  resumen general de la cuenta y detalle de una campaña. No repite ningún cálculo del motor de
  reglas — solo lee y agrega.
- Endpoints: `GET /api/v1/ad-accounts/{id}/dashboard-summary` (KPIs, ranking de mejores/críticas,
  top 5 alertas) y `GET /api/v1/campaigns/{id}` (anuncios con sus métricas más recientes).
- Frontend: `/` (resumen general con KPIs + ranking + alertas), `/campaigns` (listado con
  puntaje y salud) y `/campaigns/[id]` (anuncios de la campaña + `AIExplanationCard` del
  Módulo 4 al seleccionar uno).
- **Simplificación conocida:** `/campaigns` hoy solo muestra las campañas que ya aparecen en el
  ranking del resumen (mejores + críticas), no *todas* las campañas de la cuenta — para listar
  el 100% haría falta un endpoint paginado dedicado, que queda como mejora natural del Módulo 6.
- 21/21 tests en backend (incluye agregación de KPIs y ranking con datos fabricados a mano).
- **No pude verificar el frontend en un navegador real**: este entorno no tiene Node.js/npm
  instalado, así que el código de Next.js está escrito pero no compilado/ejecutado aquí — la
  primera verificación real ocurre en el build de Vercel.

Próximo módulo natural: alertas en tiempo real / historial de acciones aplicadas (lo que en el
plan original era el Módulo 7), o refinar `/campaigns` para listar todas las campañas.

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
