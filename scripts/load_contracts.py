#!/usr/bin/env python3
"""
📥 Cargar Contratos en la Base de Datos

Este script ejecuta la ingestion de contratos desde SECOP.
IMPORTANTE: Esto puede tomar 5-15 minutos la primera vez.

Uso:
    python scripts/load_contracts.py [--days 7]
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure we're in the right directory
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from services.ingestion import ingest_all, get_contract_count


def main():
    parser = argparse.ArgumentParser(description="Load contracts from SECOP")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days back to fetch (default: 7)",
    )
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Force aggressive mode (load more contracts on first run)",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("📥 JOBPER - Contract Ingestion")
    print("=" * 80)

    # Check current count
    current_count = get_contract_count()
    print(f"\n📊 Contratos actuales en BD: {current_count:,}")

    if current_count == 0:
        print(f"\n⚠️  La base de datos está vacía. Primera carga...")
        print(f"⏱️  Esto tomará 5-15 minutos. Ten paciencia.")
        args.aggressive = True

    print(f"\n🔍 Buscando contratos de los últimos {args.days} días...")
    print(f"🚀 Modo: {'AGRESIVO (primera carga)' if args.aggressive else 'NORMAL'}")
    print(f"\n{'=' * 80}")

    # Run ingestion
    try:
        results = ingest_all(days_back=args.days, force_aggressive=args.aggressive)

        print(f"\n{'=' * 80}")
        print("✅ INGESTION COMPLETADA")
        print(f"{'=' * 80}")

        total_new = sum(r.get("new", 0) for r in results.values())
        total_skipped = sum(r.get("skipped", 0) for r in results.values())
        total_errors = sum(r.get("errors", 0) for r in results.values())

        print(f"\n📊 Resumen:")
        print(f"   ✅ Nuevos contratos: {total_new:,}")
        print(f"   ⏭️  Omitidos (duplicados): {total_skipped:,}")
        print(f"   ❌ Errores: {total_errors:,}")

        # Show per-dataset breakdown
        print(f"\n📁 Por dataset:")
        for dataset, result in results.items():
            new = result.get("new", 0)
            if new > 0:
                print(f"   - {dataset}: {new:,} nuevos")

        # Final count
        final_count = get_contract_count()
        print(f"\n📊 Total en base de datos: {final_count:,} contratos")

        if total_new == 0 and current_count == 0:
            print(f"\n⚠️  WARNING: No se cargaron contratos.")
            print(f"⚠️  Verifica que SECOP esté accesible o intenta de nuevo.")
        elif total_new > 0:
            print(f"\n✅ Los usuarios ahora pueden buscar contratos en:")
            print(f"   https://www.jobper.com.co/contracts")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
