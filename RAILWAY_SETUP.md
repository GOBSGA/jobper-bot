# 🚀 Railway Setup - Jobper

## ❌ PROBLEMA ACTUAL: 401 Unauthorized en toda la aplicación

### Diagnóstico
Los usuarios están viendo errores 401 en TODAS las peticiones:
- `/api/contracts/matched` → 401
- `/api/auth/refresh` → 401
- `/api/payments/subscription` → 401
- `/api/user/profile` → 401

**Causa**: El `JWT_SECRET` no está configurado correctamente en Railway, o cambió, invalidando todos los tokens de sesión existentes.

---

## ✅ SOLUCIÓN INMEDIATA

### 1. Configurar JWT_SECRET en Railway (CRÍTICO)

```bash
# En Railway Dashboard > Variables:
JWT_SECRET=<generar-con-comando-abajo>
```

**Generar secret seguro:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

⚠️ **IMPORTANTE**:
- NO cambies este valor una vez configurado (invalida todas las sesiones)
- Guarda una copia del secret en tu gestor de contraseñas
- Si necesitas cambiarlo, avisa a todos los usuarios activos

---

### 2. Variables de Entorno OBLIGATORIAS para Producción

```bash
# =============================================================================
# CRÍTICAS (la app NO arrancará sin estas)
# =============================================================================
JWT_SECRET=<tu-secret-de-64-chars>
DATABASE_URL=<postgresql-url-de-railway>
ENV=production

# =============================================================================
# IMPORTANTES (funcionalidad limitada sin estas)
# =============================================================================
RESEND_API_KEY=<tu-resend-key>
ADMIN_EMAIL=<tu-email-admin>
FRONTEND_URL=https://www.jobper.com.co

# =============================================================================
# OPCIONALES (features adicionales)
# =============================================================================
REDIS_URL=<redis-url-si-usas-cache>
OPENAI_API_KEY=<para-onboarding-ai>
ADMIN_TOKEN=<token-acceso-admin-panel>

# Payments (transferencia bancaria)
NEQUI_NUMBER=310 287 2081
BREB_HANDLE=@gabriela5264

# Notificaciones
TELEGRAM_BOT_TOKEN=<si-usas-telegram>
```

---

### 3. Verificar Deployment

Después de configurar las variables:

1. **Trigger nuevo deploy** en Railway
2. **Verificar logs** para asegurarte que arrancó sin errores:
   ```
   ✓ JWT_SECRET configurado
   ✓ Database connection OK
   ✓ Server listening on port 5000
   ```

3. **Probar login** en https://www.jobper.com.co:
   - Registrar nuevo usuario
   - Login con password
   - Verificar que NO sale 401

---

### 4. Si los usuarios siguen con 401

**Los tokens existentes son INVÁLIDOS**. Los usuarios deben:
1. Cerrar sesión (o borrar localStorage)
2. Iniciar sesión de nuevo

**Automatizar esto en el frontend:**
```javascript
// En dashboard/src/lib/api.js - interceptor de respuestas
if (error.response?.status === 401) {
  // Limpiar tokens inválidos
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  // Redirect a login
  window.location.href = '/login';
}
```

---

## 🔍 Diagnóstico de Problemas

### Verificar que JWT_SECRET está configurado

SSH a Railway container y ejecutar:
```bash
python -c "from config import Config; print('JWT_SECRET:', 'CONFIGURADO' if Config.JWT_SECRET else 'NO CONFIGURADO')"
```

### Ver logs en tiempo real
```bash
railway logs --tail
```

### Verificar database tiene datos
```bash
# En Railway > PostgreSQL > Query
SELECT COUNT(*) FROM "user";
SELECT COUNT(*) FROM contract;
```

---

## 🚨 Problemas Comunes

### "Session expired" en cada refresh
- **Causa**: JWT_SECRET cambia en cada deploy
- **Fix**: Configurar JWT_SECRET como variable de entorno permanente

### "No hay contratos"
- **Causa**: Scrapers no están corriendo o DB vacía
- **Fix**: Ejecutar ingestion manualmente o verificar cronjobs

### "El registro no guarda company_name"
- **Causa**: 401 en `/api/user/profile` (PUT) - tokens inválidos
- **Fix**: Configurar JWT_SECRET y hacer login de nuevo

### "Cambiar contraseña no funciona"
- **Causa**: 401 en `/api/user/change-password` - tokens inválidos
- **Fix**: Configurar JWT_SECRET y hacer login de nuevo

---

## 📝 Checklist de Deploy

- [ ] JWT_SECRET configurado (64 chars)
- [ ] DATABASE_URL apunta a PostgreSQL de Railway
- [ ] ENV=production
- [ ] FRONTEND_URL=https://www.jobper.com.co
- [ ] RESEND_API_KEY configurado (para emails)
- [ ] ADMIN_EMAIL configurado (para notificaciones)
- [ ] CORS_ORIGINS incluye frontend URL
- [ ] Deploy exitoso sin errores en logs
- [ ] Login funciona sin 401
- [ ] Profile update funciona
- [ ] Hay contratos en la base de datos

---

## 🔗 URLs Importantes

- **Frontend**: https://www.jobper.com.co
- **Backend API**: https://api-jobper.railway.app (o tu URL de Railway)
- **Railway Dashboard**: https://railway.app/dashboard
- **Admin Panel**: https://www.jobper.com.co/admin

---

## 🆘 Soporte

Si después de seguir esta guía sigues teniendo problemas:
1. Revisa los logs de Railway: `railway logs --tail`
2. Verifica las variables de entorno están configuradas
3. Prueba hacer login con un usuario nuevo
4. Contacta soporte: gabriel.sanmiguel322@gmail.com
