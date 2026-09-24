"""Dépendances FastAPI : ce que les routes reçoivent via Depends()."""

from fastapi import HTTPException


def get_session():
    """Une session de base de données par requête (remplacée par une base de test dans les tests)."""
    try:
        # import ici : l'API démarre même sans DATABASE_URL, seule /predict en a besoin
        from db.database import SessionLocal
    except RuntimeError:
        raise HTTPException(503, "Base de données non configurée (DATABASE_URL manquante)")
    with SessionLocal() as session:
        yield session
