# 🚀 Guía de Deployment - Jobper v5.0

Esta guía describe cómo desplegar Jobper en producción de forma segura.

## 📋 Pre-requisitos

### Servicios Requeridos

1. **Base de Datos PostgreSQL 15+**
   - Railway, Supabase, o cualquier servicio managed
   - Mínimo 1GB RAM, 10GB storage

2. **Redis (Opcional pero Recomendado)**
   - Para caching y Celery
   - Railway, Upstash, o Redis Cloud

3. **Email Service**
   - [Resend](https://resend.com) (recomendado)
   - API key necesaria para magic links y notificaciones

### Variables de Entorno Críticas

Estas variables **DEBEN** estar configuradas en producción:

```bash
# Requerido
ENV=production
DATABASE_URL=postgresql://user:password@host:5432/jobper
JWT_SECRET=<genera con: python -c "import secrets; print(secrets.token_hex(32))">
RESEND_API_KEY=<tu_api_key>
FRONTEND_URL=https://tu-dominio.com

# Recomendado
REDIS_URL=redis://user:password@host:6379
ADMIN_EMAIL=tu@email.com
CORS_ORIGINS=https://tu-dominio.com

# Pagos (si usas Wompi)
WOMPI_EVENTS_SECRET=<secret_from_wompi>
WOMPI_PUBLIC_KEY=<public_key>
WOMPI_PRIVATE_KEY=<private_key>
```

---

## 🐳 Deployment con Railway

Railway es la opción más simple para deployment.

### Paso 1: Conectar Repositorio

1. Ve a [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. Selecciona tu repositorio `jobper-bot`

### Paso 2: Configurar Servicios

```bash
# Agregar PostgreSQL
railway add postgresql

# Agregar Redis (opcional)
railway add redis
```

Railway automáticamente configurará `DATABASE_URL` y `REDIS_URL`.

### Paso 3: Configurar Variables de Entorno

En Railway Dashboard → Variables:

```bash
ENV=production
JWT_SECRET=<tu_secret_generado>
RESEND_API_KEY=<tu_api_key>
FRONTEND_URL=https://jobper-production.up.railway.app
ADMIN_EMAIL=tu@email.com
```

### Paso 4: Deploy

Railway detecta automáticamente el `Dockerfile` y despliega.

```bash
# Ver logs en tiempo real
railway logs

# Ver status
railway status
```

### Paso 5: Ejecutar Migraciones

Las migraciones se ejecutan automáticamente en startup gracias a `_run_alembic_migrations()`.

Para ejecutar manualmente:

```bash
railway run alembic upgrade head
```

---

## 🏗️ Deployment con Docker

### Build Local

```bash
# Build image
docker build -t jobper:latest .

# Run container
docker run -d \
  --name jobper \
  -p 5001:5001 \
  -e ENV=production \
  -e DATABASE_URL=postgresql://... \
  -e JWT_SECRET=... \
  -e RESEND_API_KEY=... \
  jobper:latest
```

### Docker Compose (Producción)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5001:5001"
    environment:
      ENV: production
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@db:5432/jobper
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
      RESEND_API_KEY: ${RESEND_API_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: jobper
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

Deploy:

```bash
# Set secrets
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
export DB_PASSWORD=$(python -c "import secrets; print(secrets.token_hex(16))")

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## ✅ Post-Deployment Checklist

### 1. Verificar Health Check

```bash
curl https://tu-dominio.com/health
```

Respuesta esperada:

```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"}
  }
}
```

### 2. Verificar Migraciones

```bash
# Ver migraciones aplicadas
railway run alembic current

# Ver historial
railway run alembic history
```

### 3. Crear Usuario Admin

```bash
railway run python -c "
from core.database import UnitOfWork, User
from datetime import datetime, timedelta
import secrets

with UnitOfWork() as uow:
    admin = User(
        email='admin@jobper.co',
        email_verified=True,
        plan='dominador',
        is_admin=True,
        referral_code=f'ADMIN-{secrets.token_hex(4).upper()}',
        trial_ends_at=datetime.utcnow() + timedelta(days=365)
    )
    uow.users.create(admin)
    uow.commit()
    print(f'Admin user created: {admin.email}')
"
```

### 4. Configurar Backups

**Railway** (automático):
- PostgreSQL backups diarios incluidos
- Retención: 7 días en plan Hobby, 30 días en Pro

**Manual** (recomendado para datos críticos):

```bash
# Backup diario con cron
0 3 * * * pg_dump $DATABASE_URL > /backups/jobper_$(date +\%Y\%m\%d).sql
```

### 5. Configurar Monitoring

#### Sentry (Error Tracking)

1. Crea cuenta en [sentry.io](https://sentry.io)
2. Crea proyecto "Jobper"
3. Obtén DSN

Agregar a variables de entorno:

```bash
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

Agregar a `app.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

if Config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=Config.SENTRY_DSN,
        integrations=[FlaskIntegration()],
        environment=Config.ENV,
        traces_sample_rate=0.1  # 10% de requests
    )
```

### 6. Configurar Logs

Railway muestra logs automáticamente. Para logs persistentes:

```bash
# Ver últimos 100 logs
railway logs --lines 100

# Seguir logs en tiempo real
railway logs --follow
```

---

## 🔒 Seguridad en Producción

### Checklist de Seguridad

- [ ] `JWT_SECRET` es único y seguro (min 32 bytes)
- [ ] `ENV=production` está configurado
- [ ] CORS está limitado a tu dominio (no `*`)
- [ ] PostgreSQL tiene contraseña fuerte
- [ ] `.env` NO está en git (verificar `.gitignore`)
- [ ] HTTPS está habilitado (Railway lo hace automáticamente)
- [ ] Backups de BD configurados
- [ ] Monitoring (Sentry) configurado
- [ ] Rate limiting está activo

### Rotar JWT Secret

Si necesitas rotar el secret:

```bash
# 1. Generar nuevo secret
new_secret=$(python -c "import secrets; print(secrets.token_hex(32))")

# 2. Actualizar en Railway
railway variables set JWT_SECRET=$new_secret

# 3. Redeploy
railway up

# ⚠️ Esto invalidará todas las sesiones activas
```

---

## 🚨 Troubleshooting

### Error: "Configuration validation failed"

Causa: Falta alguna variable crítica.

Solución:

```bash
# Ver logs
railway logs

# Verificar variables
railway variables

# Agregar variable faltante
railway variables set VARIABLE=valor
```

### Error: "Database connection failed"

Causa: `DATABASE_URL` incorrecta o BD caída.

Solución:

```bash
# Verificar BD
railway run pg_isready

# Reiniciar BD
railway restart postgresql

# Verificar URL
railway variables | grep DATABASE_URL
```

### Error: "Alembic migrations failed"

Causa: Migración conflictiva.

Solución:

```bash
# Ver estado actual
railway run alembic current

# Ver error específico
railway run alembic upgrade head

# Downgrade si es necesario
railway run alembic downgrade -1
```

### Performance Lento

Solución:

```bash
# 1. Verificar queries lentas
railway run psql $DATABASE_URL -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;"

# 2. Verificar índices
railway run psql $DATABASE_URL -c "
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public';"

# 3. Aumentar workers (Railway)
# En start.sh, cambiar --workers 1 a --workers 2
```

---

## 📊 Monitoring en Producción

### Health Check Automático

Railway verifica `/health` cada 30 segundos. Si falla 3 veces, reinicia el container.

### Métricas Clave

Monitorear:

1. **Response Time** - Debe ser < 500ms para 95% de requests
2. **Error Rate** - Debe ser < 1%
3. **Database Connections** - No debe alcanzar el límite
4. **Memory Usage** - Debe ser < 80%
5. **Disk Usage** - Debe ser < 80%

### Alertas

Configurar alertas en Railway:

- CPU > 80% por 5 minutos
- Memory > 80% por 5 minutos
- Error rate > 5%
- Response time > 1s

---

## 🔄 CI/CD Pipeline

El workflow de GitHub Actions (`.github/workflows/ci.yml`) se ejecuta en cada push:

1. **Lint** - Verifica formato de código
2. **Tests** - Ejecuta tests unitarios
3. **Security** - Escanea vulnerabilidades
4. **Build** - Construye Docker image

Para deploy automático en Railway:

1. Conecta Railway con GitHub
2. Habilita "Auto Deploy"
3. Cada push a `main` despliega automáticamente

---

## 📈 Escalamiento

### Vertical (Railway)

```bash
# Aumentar recursos
railway scale --memory 2GB --cpu 2
```

### Horizontal (múltiples workers)

Editar `start.sh`:

```bash
# De:
--workers 1

# A:
--workers 4  # 2x CPU cores
```

### Caching Agresivo

Habilitar Redis:

```bash
REDIS_URL=redis://...
```

El caching automáticamente se activará para:
- Match scores
- Contract searches
- User profiles

---

## 🎯 Próximos Pasos

Después del primer deployment:

1. ✅ Configurar dominio custom
2. ✅ Configurar SSL/TLS (Railway lo hace automáticamente)
3. ✅ Configurar Sentry para error tracking
4. ✅ Configurar backups automáticos
5. ✅ Configurar alertas de monitoring
6. ✅ Crear usuario admin
7. ✅ Poblar datos iniciales (sectores, keywords)
8. ✅ Ejecutar primer scraping de contratos

---

## 📞 Soporte

- **Documentación**: Este archivo
- **Logs**: `railway logs`
- **Health Check**: `/health`
- **Admin Panel**: `/admin` (requiere token admin)

¡Deployment exitoso! 🎉
