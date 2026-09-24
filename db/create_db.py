"""Crates the PostgreSQK  la base PostgreSQL, ses tables, et enregistre la version du modèle.

Usage (depuis la racine du projet) :
    venv/bin/python -m db.create_db           # crée ce qui manque
    venv/bin/python -m db.create_db --reset   # supprime puis recrée les tables
"""

## skeleton: creates base PostgreSQL, ses tables, et enregistre la version du modele

# def main(): 
#     pass # do nothing

# if __name__ == "__main__":
#     main()
## create database if missing
## need table because in PostgreSQL, every connection must point to a specific database
## so to crate ma_base, need to connect to ma_base : 
#create tables with --reset
# save model version
#wire all in main



import argparse

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from db.models import Base, ModelVersion
from db.predictions import obtenir_version_modele
from modele.pred import MODEL_NAME, MODEL_PATH, seuil


def creer_database_si_absente(database_url: str) -> None:
    """CREATE DATABASE"""
    url = make_url(database_url) # point to our base
    nom_db = url.database
    admin_engine = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with admin_engine.connect() as conn:
        existe = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :nom"), {"nom": nom_db}
        )
        if existe:
            print(f"Base '{nom_db}' déjà présente")
        else:
            nom_quote = admin_engine.dialect.identifier_preparer.quote(nom_db)
            conn.execute(text(f"CREATE DATABASE {nom_quote}"))
            print(f"Base '{nom_db}' créée")
    admin_engine.dispose()


def creer_tables(engine: Engine, reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(engine)
        print("Tables supprimées")
    # create_all doesnt remake an existing table
    Base.metadata.create_all(engine)
    print("Tables :", ", ".join(Base.metadata.tables))


def enregistrer_version_modele(session: Session) -> None:
    """Ajoute le modèle actuel dans model_version s'il n'y est pas déjà (même fonction
    que celle utilisée par l'API, donc jamais de doublon)."""
    combien = select(func.count()).select_from(ModelVersion)
    avant = session.scalar(combien)
    version = obtenir_version_modele(session, MODEL_NAME, MODEL_PATH.name, seuil)
    session.commit()
    etat = "enregistrée" if session.scalar(combien) > avant else "déjà enregistrée"
    print(f"Version du modèle {etat} (id={version.id_model_version}, seuil={seuil:.4f})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset", action="store_true", help="supprime et recrée toutes les tables"
    )
    args = parser.parse_args()

    # import ici : db.database exige DATABASE_URL, inutile pour les tests
    from db.database import DATABASE_URL, SessionLocal, engine

    creer_database_si_absente(DATABASE_URL)
    creer_tables(engine, reset=args.reset)
    with SessionLocal() as session:
        enregistrer_version_modele(session)


if __name__ == "__main__":
    main()
