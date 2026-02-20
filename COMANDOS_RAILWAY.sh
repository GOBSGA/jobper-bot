#!/bin/bash
# ============================================================================
# COMANDOS RAILWAY - Jobper Setup Completo
# ============================================================================

echo "🚀 JOBPER - Setup Completo"
echo "============================================================================"
echo ""

# ============================================================================
# PASO 1: Conectar Railway
# ============================================================================
echo "📍 PASO 1: Conectar Railway"
echo "Ejecuta estos comandos:"
echo ""
echo "  railway login"
echo "  railway link"
echo ""
read -p "¿Ya lo hiciste? (presiona ENTER para continuar)"

# ============================================================================
# PASO 2: Hacer Admin
# ============================================================================
echo ""
echo "============================================================================"
echo "📍 PASO 2: Hacerte Admin"
echo "============================================================================"
echo ""
read -p "Tu email de registro en Jobper: " USER_EMAIL

echo ""
echo "Ejecutando: railway run python scripts/make_admin.py $USER_EMAIL"
echo ""
railway run python scripts/make_admin.py "$USER_EMAIL"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Admin configurado exitosamente"
else
    echo ""
    echo "❌ Error al hacer admin. Verifica que el email sea correcto."
    exit 1
fi

# ============================================================================
# PASO 3: Cargar Contratos
# ============================================================================
echo ""
echo "============================================================================"
echo "📍 PASO 3: Cargar Contratos (esto toma 10-15 minutos)"
echo "============================================================================"
echo ""
read -p "¿Cuántos días quieres cargar? (30 recomendado): " DAYS
DAYS=${DAYS:-30}

echo ""
echo "Ejecutando: railway run python scripts/load_contracts.py --days $DAYS --aggressive"
echo ""
echo "⏱️  ESTO TOMARÁ 10-15 MINUTOS. NO CANCELES."
echo ""
railway run python scripts/load_contracts.py --days "$DAYS" --aggressive

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Contratos cargados exitosamente"
else
    echo ""
    echo "❌ Error al cargar contratos. Ver logs arriba."
fi

# ============================================================================
# PASO 4: Verificar
# ============================================================================
echo ""
echo "============================================================================"
echo "📍 PASO 4: Verificar Sistema"
echo "============================================================================"
echo ""
railway run python scripts/diagnose.py

# ============================================================================
# RESUMEN
# ============================================================================
echo ""
echo "============================================================================"
echo "✅ SETUP COMPLETADO"
echo "============================================================================"
echo ""
echo "Ahora puedes:"
echo "  1. Ir a https://www.jobper.com.co/admin (Panel de Admin)"
echo "  2. Ir a https://www.jobper.com.co/contracts (Búsqueda de Contratos)"
echo "  3. Registrar usuarios de prueba"
echo ""
echo "🎉 Jobper está listo para ser el software más icónico de Colombia 2025! 🇨🇴"
echo ""
