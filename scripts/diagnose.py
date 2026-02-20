#!/usr/bin/env python3
"""
🔍 Jobper System Diagnostic Tool

Verifica el estado del sistema:
- Configuración (JWT_SECRET, DATABASE_URL, etc.)
- Base de datos (usuarios, contratos, scrapers)
- Autenticación (puede generar tokens de prueba)
"""

import sys
import os
from pathlib import Path

# Ensure we're in the right directory
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from config import Config
from core.database import UnitOfWork
from sqlalchemy import text


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_config():
    """Verify critical configuration."""
    print_section("📋 CONFIGURACIÓN")

    checks = {
        "JWT_SECRET": bool(Config.JWT_SECRET),
        "DATABASE_URL": bool(Config.DATABASE_URL),
        "RESEND_API_KEY": bool(Config.RESEND_API_KEY),
        "ADMIN_EMAIL": bool(Config.ADMIN_EMAIL),
        "FRONTEND_URL": bool(Config.FRONTEND_URL),
        "OPENAI_API_KEY": bool(getattr(Config, "OPENAI_API_KEY", None)),
    }

    for key, value in checks.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {'CONFIGURADO' if value else 'NO CONFIGURADO'}")

    # Show ENV
    print(f"\n📍 Environment: {Config.ENV}")
    print(f"📍 Is Production: {Config.IS_PRODUCTION}")

    return all(checks.values())


def check_database():
    """Check database connectivity and data."""
    print_section("💾 BASE DE DATOS")

    try:
        with UnitOfWork() as uow:
            # Users
            total_users = uow.session.execute(text('SELECT COUNT(*) FROM "user"')).scalar()
            verified_users = uow.session.execute(
                text('SELECT COUNT(*) FROM "user" WHERE email_verified = true')
            ).scalar()
            admins = uow.session.execute(text('SELECT COUNT(*) FROM "user" WHERE is_admin = true')).scalar()

            print(f"👥 Total usuarios: {total_users}")
            print(f"   ├─ Verificados: {verified_users}")
            print(f"   └─ Admins: {admins}")

            # Contracts
            total_contracts = uow.session.execute(text("SELECT COUNT(*) FROM contract")).scalar()
            recent_contracts = uow.session.execute(
                text("SELECT COUNT(*) FROM contract WHERE created_at >= NOW() - INTERVAL '7 days'")
            ).scalar()

            print(f"\n📄 Total contratos: {total_contracts}")
            print(f"   └─ Últimos 7 días: {recent_contracts}")

            if total_contracts == 0:
                print("   ⚠️  WARNING: No hay contratos en la base de datos!")
                print("   ⚠️  Ejecuta ingestion manualmente o verifica scrapers")

            # Scrapers
            try:
                scrapers = uow.session.execute(text("SELECT COUNT(*) FROM scraper_source")).scalar()
                enabled_scrapers = uow.session.execute(
                    text("SELECT COUNT(*) FROM scraper_source WHERE enabled = true")
                ).scalar()
                print(f"\n🔍 Scrapers configurados: {scrapers}")
                print(f"   └─ Activos: {enabled_scrapers}")
            except Exception:
                print(f"\n🔍 Scrapers: Tabla no existe (normal si no se usa)")

            # Recent users
            print(f"\n📝 Últimos 5 usuarios:")
            result = uow.session.execute(
                text("""
                SELECT email, plan, company_name, created_at
                FROM "user"
                ORDER BY created_at DESC
                LIMIT 5
            """)
            )
            for row in result:
                email_short = row[0][:30] + "..." if len(row[0]) > 30 else row[0]
                company = row[2] or "(sin nombre)"
                print(f"   - {email_short} | {row[1]} | {company}")

        return True

    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False


def check_auth():
    """Test JWT generation."""
    print_section("🔐 AUTENTICACIÓN")

    try:
        # Try to generate a test token
        from services.auth import _create_access_token
        from core.database import User

        # Create a dummy user for testing
        dummy_user = User(id=999, email="test@test.com", plan="free")
        token = _create_access_token(dummy_user)

        print(f"✅ JWT generation works")
        print(f"   Sample token (first 30 chars): {token[:30]}...")

        # Verify token
        import jwt

        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        print(f"✅ JWT verification works")
        print(f"   Token contains user_id: {payload.get('sub')}")

        return True

    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        return False


def main():
    """Run all diagnostics."""
    print("\n" + "🩺" * 40)
    print("  JOBPER SYSTEM DIAGNOSTIC")
    print("🩺" * 40)

    results = {
        "Configuración": check_config(),
        "Base de datos": check_database(),
        "Autenticación": check_auth(),
    }

    print_section("📊 RESUMEN")
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")

    all_pass = all(results.values())

    if not all_pass:
        print("\n⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("⚠️  Revisa los errores arriba y la guía RAILWAY_SETUP.md")
        sys.exit(1)
    else:
        print("\n✅ TODO OK - El sistema está configurado correctamente")
        sys.exit(0)


if __name__ == "__main__":
    main()
