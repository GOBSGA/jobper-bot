# 🤖 Jobper Bot v2.0

**Monitor Inteligente de Licitaciones Gubernamentales con WhatsApp Interactivo**

Bot conversacional que ayuda a empresas a encontrar oportunidades de contratación pública en Colombia (SECOP II) y Estados Unidos (SAM.gov).

---

## ✨ Características

### 🎯 Funcionalidades Principales
- **Conversación natural por WhatsApp** - Registro y configuración interactiva
- **Multi-país** - Colombia (SECOP II) y EEUU (SAM.gov)
- **Matching inteligente** - Algoritmo de relevancia personalizado por usuario
- **Reportes semanales** - Resumen de las mejores oportunidades cada lunes
- **Búsqueda bajo demanda** - El usuario puede pedir búsqueda inmediata

### 🔧 Técnicas
- Arquitectura modular y escalable
- Base de datos SQLite con SQLAlchemy
- Webhook Flask para respuestas en tiempo real
- Scheduler para tareas programadas
- Listo para deploy en Railway/Render/Heroku

---

## 📋 Flujo de Usuario

```
Usuario envía "Hola" por WhatsApp
              ↓
      [1] ¿En qué industria trabajas?
         (Tecnología, Construcción, Salud, etc.)
              ↓
      [2] ¿Qué SÍ quieres ver?
         (keywords adicionales)
              ↓
      [3] ¿Qué NO quieres ver?
         (keywords a excluir)
              ↓
      [4] ¿Rango de presupuesto?
              ↓
      [5] ¿Qué país?
         (Colombia / EEUU / Ambos)
              ↓
      ✅ ¡Configuración completa!
              ↓
      📊 Reporte semanal cada lunes 9 AM
```

---

## 🚀 Instalación

### 1. Clonar el proyecto

```bash
git clone <tu-repo>
cd jobper-bot
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 5. Ejecutar localmente

```bash
python app.py
```

El servidor iniciará en `http://localhost:5000`

---

## ⚙️ Configuración de Twilio

### Paso 1: Crear cuenta
1. Ve a [twilio.com](https://www.twilio.com/) y crea una cuenta
2. Verifica tu número de teléfono

### Paso 2: Activar WhatsApp Sandbox
1. En la consola, ve a **Messaging > Try it out > Send a WhatsApp message**
2. Escanea el código QR o envía el mensaje de activación
3. Anota el número del sandbox: `+14155238886`

### Paso 3: Configurar Webhook
1. En Twilio Console, ve a **Messaging > Settings > WhatsApp Sandbox Settings**
2. En "When a message comes in", pon tu URL:
   - Local con ngrok: `https://tu-id.ngrok.io/webhook/whatsapp`
   - Producción: `https://tu-app.railway.app/webhook/whatsapp`

### Paso 4: Obtener credenciales
- **Account SID**: Empieza con "AC..."
- **Auth Token**: Token secreto

---

## 🌐 Deploy en Railway

### Opción A: Desde GitHub
1. Ve a [railway.app](https://railway.app/)
2. Click en "New Project" > "Deploy from GitHub repo"
3. Selecciona tu repositorio
4. Agrega las variables de entorno en Settings > Variables

### Opción B: CLI
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login y deploy
railway login
railway init
railway up
```

### Variables requeridas en Railway:
```
TWILIO_SID=ACxxxxxxxx
TWILIO_TOKEN=xxxxxxxx
TWILIO_FROM=+14155238886
SAM_API_KEY=tu_key (opcional)
ADMIN_TOKEN=un_token_secreto
```

---

## 🔑 API de SAM.gov (EEUU)

Para monitorear licitaciones de Estados Unidos:

1. **Crear cuenta**: Ve a [sam.gov](https://sam.gov/) > Sign In > Create Account
2. **Verificar identidad**: Puede tomar 24-48 horas
3. **Solicitar API Key**:
   - System Account Request
   - Seleccionar "Public API"
   - Describir uso: "Monitoreo de oportunidades de contratación"
4. **Esperar aprobación**: 1-3 días hábiles

Documentación: [open.gsa.gov/api/opportunities-api](https://open.gsa.gov/api/opportunities-api/)

---

## 📁 Estructura del Proyecto

```
jobper-bot/
├── app.py                  # Servidor Flask principal
├── config.py               # Configuración centralizada
├── requirements.txt        # Dependencias Python
├── Procfile               # Config para Heroku/Railway
├── railway.json           # Config específica de Railway
│
├── database/
│   ├── models.py          # Modelos SQLAlchemy (User, Contract)
│   └── manager.py         # Operaciones CRUD
│
├── conversation/
│   ├── handlers.py        # Máquina de estados del chat
│   └── messages.py        # Plantillas de mensajes
│
├── scrapers/
│   ├── base.py            # Clase base abstracta
│   ├── secop.py           # Scraper SECOP II (Colombia)
│   └── sam.py             # Scraper SAM.gov (EEUU)
│
├── matching/
│   └── engine.py          # Motor de relevancia/scoring
│
├── notifications/
│   └── whatsapp.py        # Cliente Twilio WhatsApp
│
└── scheduler/
    └── jobs.py            # Tareas programadas (reportes)
```

---

## 🧪 Testing Local

### Probar el flujo sin WhatsApp

```bash
# Iniciar servidor
python app.py

# En otra terminal, simular mensajes:
curl -X POST http://localhost:5000/test/message \
  -H "Content-Type: application/json" \
  -d '{"phone": "+573001234567", "message": "hola"}'
```

### Usar ngrok para pruebas con WhatsApp real

```bash
# Instalar ngrok
brew install ngrok  # Mac
# o descargar de ngrok.com

# Exponer puerto local
ngrok http 5000

# Copiar la URL https y configurarla en Twilio
```

---

## 📊 Endpoints de API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Health check básico |
| `/health` | GET | Health check con stats |
| `/webhook/whatsapp` | POST | Webhook de Twilio |
| `/admin/stats` | GET | Estadísticas del bot |
| `/admin/send-reports` | POST | Trigger manual de reportes |
| `/test/message` | POST | Simular mensaje (dev) |

---

## 🛡️ Seguridad

- **NUNCA** subas `.env` a Git (ya está en `.gitignore`)
- Usa `ADMIN_TOKEN` fuerte en producción
- Considera rate limiting para endpoints públicos
- Rota credenciales de Twilio periódicamente

---

## 🔮 Roadmap (Ideas Futuras)

- [ ] Integración con más países (México, Perú, Chile)
- [ ] Dashboard web para administración
- [ ] Notificaciones de contratos urgentes (deadline < 3 días)
- [ ] Integración con empresas privadas
- [ ] Analytics de oportunidades ganadas
- [ ] Asistente IA para redactar propuestas

---

## 🐛 Troubleshooting

### "No recibo mensajes de WhatsApp"
- Verifica que enviaste el mensaje de activación al sandbox
- El sandbox de Twilio expira cada 72 horas sin actividad
- Verifica que el webhook esté configurado correctamente

### "Error de conexión a SECOP II"
- La API de Datos Abiertos Colombia puede tener límites de rate
- Espera unos minutos y reintenta

### "SAM.gov no retorna resultados"
- Verifica que tu API key esté activa
- SAM.gov tiene rate limits estrictos

---

## 📄 Licencia

MIT License - Usa este código libremente.

---

**Desarrollado con ❤️ para emprendedores que quieren hacer negocios con el gobierno**

🇨🇴 🇺🇸
