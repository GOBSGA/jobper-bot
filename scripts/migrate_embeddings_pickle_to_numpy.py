#!/usr/bin/env python3
"""
Script de migración one-time: pickle → numpy para embeddings en DB.

Cuándo correr: ANTES de deployar la versión que elimina pickle de nlp/embeddings.py.
Puede correrse con la app en producción sin downtime (el código es backward-compatible).

Uso:
    # En Railway (via Railway CLI):
    railway run python scripts/migrate_embeddings_pickle_to_numpy.py

    # O localmente contra la DB de prod:
    DATABASE_URL=postgresql://... python scripts/migrate_embeddings_pickle_to_numpy.py
"""

import sys
import os
import pickle
import logging
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

import numpy as np

EMBEDDING_DIMS = 384  # paraphrase-multilingual-MiniLM-L12-v2


def is_pickle(data: bytes) -> bool:
    """Detecta si los bytes son un pickle serializado."""
    return len(data) != EMBEDDING_DIMS * 4  # numpy float32 siempre tiene exactamente 1536 bytes


def pickle_to_numpy(data: bytes) -> bytes:
    """Convierte bytes pickle a bytes numpy."""
    arr = pickle.loads(data)
    return np.array(arr, dtype=np.float32).tobytes()


def migrate():
    from config import Config
    from sqlalchemy import create_engine, text

    db_url = Config.DATABASE_URL
    logger.info(f"Conectando a: {db_url[:30]}...")
    engine = create_engine(db_url)

    migrated_contracts = 0
    migrated_users = 0
    skipped = 0
    errors = 0

    with engine.begin() as conn:
        # --- Contratos ---
        logger.info("Procesando embeddings de contratos...")
        rows = conn.execute(text("SELECT id, embedding FROM contracts WHERE embedding IS NOT NULL")).fetchall()
        logger.info(f"  Contratos con embedding: {len(rows)}")

        for row in rows:
            contract_id, data = row[0], bytes(row[1])
            if not is_pickle(data):
                skipped += 1
                continue
            try:
                new_data = pickle_to_numpy(data)
                conn.execute(
                    text("UPDATE contracts SET embedding = :emb WHERE id = :id"),
                    {"emb": new_data, "id": contract_id},
                )
                migrated_contracts += 1
            except Exception as e:
                logger.error(f"  ERROR en contrato {contract_id}: {e}")
                errors += 1

        # --- Usuarios (profile_embedding si existe) ---
        logger.info("Procesando embeddings de usuarios...")
        try:
            user_rows = conn.execute(
                text("SELECT id, profile_embedding FROM users WHERE profile_embedding IS NOT NULL")
            ).fetchall()
            logger.info(f"  Usuarios con embedding: {len(user_rows)}")

            for row in user_rows:
                user_id, data = row[0], bytes(row[1])
                if not is_pickle(data):
                    skipped += 1
                    continue
                try:
                    new_data = pickle_to_numpy(data)
                    conn.execute(
                        text("UPDATE users SET profile_embedding = :emb WHERE id = :id"),
                        {"emb": new_data, "id": user_id},
                    )
                    migrated_users += 1
                except Exception as e:
                    logger.error(f"  ERROR en usuario {user_id}: {e}")
                    errors += 1
        except Exception:
            logger.info("  Columna profile_embedding no existe en users — saltando")

    logger.info("=" * 50)
    logger.info(f"Migración completa:")
    logger.info(f"  Contratos migrados : {migrated_contracts}")
    logger.info(f"  Usuarios migrados  : {migrated_users}")
    logger.info(f"  Ya en numpy (skip) : {skipped}")
    logger.info(f"  Errores            : {errors}")

    if errors > 0:
        logger.error("Hubo errores — revisar logs antes de deployar")
        sys.exit(1)


if __name__ == "__main__":
    migrate()
