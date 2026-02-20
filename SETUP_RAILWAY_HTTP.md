# Setup Jobper via HTTP (Solución al problema de Railway CLI)

## Problema
`railway run` y `railway shell` ejecutan en tu máquina local, no pueden acceder a `postgres.railway.internal`.

## Solución
Endpoint HTTP que puedes llamar desde cualquier lugar: `/api/setup/initialize`

---

## Pasos

### 1. Configurar SETUP_TOKEN en Railway

```bash
# Genera un token aleatorio (ya lo hice por ti):
SETUP_TOKEN="376422707de62edcf45ed7545e65042cac5fab8e827a3704dbe352011f1f19e4"

# Configúralo en Railway:
railway variables set SETUP_TOKEN="376422707de62edcf45ed7545e65042cac5fab8e827a3704dbe352011f1f19e4"
```

### 2. Esperar que Railway termine el deploy

El código ya fue pusheado. Railway está desplegando ahora. Espera 2-3 minutos.

Verifica que el deploy terminó:
```bash
railway logs
```

Cuando veas logs tipo "Application startup complete", continúa.

### 3. Llamar al endpoint de setup

```bash
curl -X POST https://www.jobper.com.co/api/setup/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "setup_token": "376422707de62edcf45ed7545e65042cac5fab8e827a3704dbe352011f1f19e4",
    "email": "gabriel.sanmiguel322@gmail.com",
    "load_contracts": true,
    "days": 30
  }'
```

Esto va a:
1. ✅ Hacer a `gabriel.sanmiguel322@gmail.com` admin
2. ✅ Cargar contratos de los últimos 30 días (toma 10-15 minutos)

### 4. Verificar

```bash
# Revisar que todo esté OK:
curl https://www.jobper.com.co/api/health
```

Deberías ver `"contracts": <número>` con contratos cargados.

---

## Respuesta esperada

```json
{
  "ok": true,
  "message": "Setup completed successfully",
  "results": {
    "admin": {
      "status": "success",
      "message": "gabriel.sanmiguel322@gmail.com is now admin"
    },
    "contracts_before": 0,
    "contracts": {
      "status": "success",
      "initial_count": 0,
      "final_count": 1234,
      "new_contracts": 1234,
      "errors": 0
    }
  }
}
```

---

## Siguiente paso

Una vez que el endpoint retorne éxito:

1. Ve a https://www.jobper.com.co/admin (ya eres admin)
2. Ve a https://www.jobper.com.co/contracts (deberías ver contratos)
3. 🎉 Jobper está funcionando

---

## Troubleshooting

**Error: "SETUP_TOKEN not configured"**
→ Ejecuta: `railway variables set SETUP_TOKEN="376422707de62edcf45ed7545e65042cac5fab8e827a3704dbe352011f1f19e4"`

**Error: "Invalid setup_token"**
→ Verifica que usaste el mismo token en Railway y en el curl

**Error: "User not found"**
→ Primero regístrate en https://www.jobper.com.co/register

**El endpoint tarda mucho**
→ Normal. Cargar contratos toma 10-15 minutos. No canceles.
