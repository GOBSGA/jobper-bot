#!/usr/bin/env python3
"""
🔐 Hacer un usuario ADMIN

Uso:
    python scripts/make_admin.py usuario@email.com
"""

import sys
import os
from pathlib import Path

# Ensure we're in the right directory
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from core.database import UnitOfWork


def make_admin(email: str):
    """Make a user admin."""
    with UnitOfWork() as uow:
        user = uow.users.get_by_email(email)

        if not user:
            print(f"❌ Usuario no encontrado: {email}")
            print(f"\n💡 Primero regístrate en https://www.jobper.com.co/register")
            sys.exit(1)

        if user.is_admin:
            print(f"✅ {email} ya es admin")
            sys.exit(0)

        user.is_admin = True
        uow.commit()

        print(f"✅ {email} ahora es ADMIN")
        print(f"\n📍 Accede al panel de admin en:")
        print(f"   https://www.jobper.com.co/admin")
        print(f"\n🔑 Tu usuario ahora tiene acceso total al sistema")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python scripts/make_admin.py usuario@email.com")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    make_admin(email)
