#!/usr/bin/env python3
"""
Script de inicialización para Jobper Bot v3.0
Ejecutar: python scripts/setup.py
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def check_environment():
    """Verifica que el entorno esté configurado correctamente."""
    print("=" * 60)
    print("JOBPER BOT v3.0 - Setup")
    print("=" * 60)

    # Verificar Python version
    print(f"\n1. Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("   ❌ Se requiere Python 3.8+")
        return False
    print("   ✅ Python OK")

    # Verificar dependencias críticas
    print("\n2. Verificando dependencias...")

    dependencies = [
        ("flask", "Flask"),
        ("sqlalchemy", "SQLAlchemy"),
        ("requests", "Requests"),
        ("dotenv", "python-dotenv"),
        ("bs4", "BeautifulSoup4"),
    ]

    all_ok = True
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - ejecuta: pip install -r requirements.txt")
            all_ok = False

    # Verificar NLP (opcional pero recomendado)
    print("\n3. Verificando NLP (opcional)...")
    try:
        import torch
        import sentence_transformers
        print(f"   ✅ PyTorch {torch.__version__}")
        print(f"   ✅ Sentence Transformers")
    except ImportError as e:
        print(f"   ⚠️  NLP no disponible: {e}")
        print("   El bot funcionará sin matching semántico")

    return all_ok


def check_database():
    """Verifica conexión a la base de datos."""
    print("\n4. Verificando base de datos...")

    from config import Config

    print(f"   URL: {Config.DATABASE_URL[:50]}...")

    try:
        from database.models import init_database, get_session

        # Intentar inicializar
        init_database()

        # Probar conexión
        session = get_session()
        session.execute("SELECT 1")
        session.close()

        print("   ✅ Base de datos conectada")

        if Config.is_postgresql():
            print("   ✅ Usando PostgreSQL (producción)")
        else:
            print("   ⚠️  Usando SQLite (desarrollo)")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n   Solución:")
        print("   - Para SQLite: No requiere configuración adicional")
        print("   - Para PostgreSQL: Verifica DATABASE_URL en .env")
        return False


def check_twilio():
    """Verifica configuración de Twilio."""
    print("\n5. Verificando Twilio/WhatsApp...")

    from config import Config

    if Config.TWILIO_SID and Config.TWILIO_TOKEN:
        print(f"   SID: {Config.TWILIO_SID[:10]}...")
        print(f"   FROM: {Config.TWILIO_FROM}")

        # Intentar inicializar cliente
        try:
            from twilio.rest import Client
            client = Client(Config.TWILIO_SID, Config.TWILIO_TOKEN)
            # No hacemos una llamada real, solo verificamos que el cliente se cree
            print("   ✅ Credenciales configuradas")
            print("   ⚠️  Recuerda configurar el webhook en Twilio Console")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("   ⚠️  Twilio no configurado")
        print("   El bot funcionará en modo TEST (sin WhatsApp real)")


def create_test_user():
    """Crea un usuario de prueba."""
    print("\n6. Creando usuario de prueba...")

    try:
        from database.manager import DatabaseManager

        db = DatabaseManager()

        # Crear usuario de prueba
        test_phone = "+573001234567"
        user = db.get_user(test_phone)

        if user:
            print(f"   ℹ️  Usuario de prueba ya existe: {test_phone}")
        else:
            db.create_user(
                phone=test_phone,
                industry="tecnologia",
                countries="all"
            )
            print(f"   ✅ Usuario de prueba creado: {test_phone}")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def show_next_steps():
    """Muestra los siguientes pasos."""
    print("\n" + "=" * 60)
    print("PRÓXIMOS PASOS")
    print("=" * 60)

    print("""
1. PARA DESARROLLO LOCAL (sin WhatsApp real):

   # Terminal 1 - Servidor Flask
   python app.py

   # Terminal 2 - Probar endpoint
   curl -X POST http://localhost:5000/test/message \\
     -H "Content-Type: application/json" \\
     -d '{"phone": "+573001234567", "message": "hola"}'

2. PARA CONECTAR WHATSAPP (con Twilio):

   # Instalar ngrok
   brew install ngrok

   # Exponer localhost
   ngrok http 5000

   # Copiar la URL https://xxxx.ngrok.io
   # Ir a Twilio Console > WhatsApp Sandbox
   # Configurar webhook: https://xxxx.ngrok.io/webhook/whatsapp

3. PARA PRODUCCIÓN:

   # Desplegar en Railway/Render
   # Configurar variables de entorno
   # Usar el dominio proporcionado como webhook
    """)


def main():
    """Ejecuta el setup completo."""
    env_ok = check_environment()

    if not env_ok:
        print("\n❌ Hay problemas con el entorno. Corrige los errores arriba.")
        return

    db_ok = check_database()
    check_twilio()

    if db_ok:
        create_test_user()

    show_next_steps()

    print("\n✅ Setup completado!")
    print("   Ejecuta: python app.py")


if __name__ == "__main__":
    main()
