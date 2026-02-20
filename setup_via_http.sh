#!/bin/bash
# ============================================================================
# Jobper Setup via HTTP - Solución al problema de Railway CLI
# ============================================================================

SETUP_TOKEN="376422707de62edcf45ed7545e65042cac5fab8e827a3704dbe352011f1f19e4"
EMAIL="gabriel.sanmiguel322@gmail.com"
API_URL="https://www.jobper.com.co"

echo "🚀 JOBPER - Setup via HTTP"
echo "============================================================================"
echo ""

# ============================================================================
# PASO 1: Configurar SETUP_TOKEN en Railway
# ============================================================================
echo "📍 PASO 1: Configurar SETUP_TOKEN en Railway"
echo ""
echo "Ejecuta este comando:"
echo ""
echo "  railway variables set SETUP_TOKEN=\"$SETUP_TOKEN\""
echo ""
read -p "¿Ya lo ejecutaste? (presiona ENTER para continuar)"

# ============================================================================
# PASO 2: Esperar deploy
# ============================================================================
echo ""
echo "============================================================================"
echo "📍 PASO 2: Verificar que Railway terminó el deploy"
echo "============================================================================"
echo ""
echo "Railway está desplegando el nuevo código..."
echo "Ejecuta: railway logs"
echo ""
echo "Cuando veas 'Application startup complete', presiona ENTER"
echo ""
read -p "¿Deploy completo? (presiona ENTER para continuar)"

# ============================================================================
# PASO 3: Llamar al endpoint
# ============================================================================
echo ""
echo "============================================================================"
echo "📍 PASO 3: Ejecutar setup (esto toma 10-15 minutos)"
echo "============================================================================"
echo ""
echo "Llamando a $API_URL/api/setup/initialize..."
echo ""
echo "⏱️  ESTO TOMARÁ 10-15 MINUTOS. NO CANCELES."
echo ""

curl -X POST "$API_URL/api/setup/initialize" \
  -H "Content-Type: application/json" \
  -d "{
    \"setup_token\": \"$SETUP_TOKEN\",
    \"email\": \"$EMAIL\",
    \"load_contracts\": true,
    \"days\": 30
  }" \
  | python3 -m json.tool

echo ""

# ============================================================================
# PASO 4: Verificar
# ============================================================================
echo ""
echo "============================================================================"
echo "📍 PASO 4: Verificar sistema"
echo "============================================================================"
echo ""

curl -s "$API_URL/api/health" | python3 -m json.tool

echo ""
echo "============================================================================"
echo "✅ SETUP COMPLETADO"
echo "============================================================================"
echo ""
echo "Ahora puedes:"
echo "  1. Ir a $API_URL/admin (Panel de Admin)"
echo "  2. Ir a $API_URL/contracts (Búsqueda de Contratos)"
echo ""
echo "🎉 Jobper está listo!"
echo ""
