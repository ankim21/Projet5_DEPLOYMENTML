"""Tests unitaires de la création de la base : tables et version du modèle (sur SQLite)."""

from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from db.create_db import creer_tables, enregistrer_version_modele
from db.models import Base, ModelVersion, PredictionInput
from modele.pred import MODEL_NAME, seuil
from tests.conftest import moteur_sqlite

TABLES_ATTENDUES = {
    "employee",
    "evaluation",
    "sondage",
    "model_version",
    "prediction_input",
    "prediction_output",
}


def test_creer_tables():
    engine = moteur_sqlite(creer_tables=False)
    creer_tables(engine)
    assert set(inspect(engine).get_table_names()) == TABLES_ATTENDUES


def test_creer_tables_relancable():
    engine = moteur_sqlite(creer_tables=False)
    creer_tables(engine)
    with Session(engine) as session:
        session.add(ModelVersion(name="x", file_path="x.joblib", seuil=0.5))
        session.commit()

    creer_tables(engine)  # deuxième passage : ne casse rien, n'efface rien
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ModelVersion)) == 1


def test_reset_vide_les_tables():
    engine = moteur_sqlite(creer_tables=False)
    creer_tables(engine)
    with Session(engine) as session:
        session.add(ModelVersion(name="x", file_path="x.joblib", seuil=0.5))
        session.commit()

    creer_tables(engine, reset=True)
    assert set(inspect(engine).get_table_names()) == TABLES_ATTENDUES
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(ModelVersion)) == 0


def test_enregistrer_version_modele_idempotent(capsys):
    engine = moteur_sqlite()
    with Session(engine) as session:
        enregistrer_version_modele(session)
        assert "enregistrée" in capsys.readouterr().out

        version = session.scalar(select(ModelVersion))
        assert (version.name, version.seuil) == (MODEL_NAME, seuil)
        assert version.file_path == "modele_attrition.joblib"

        enregistrer_version_modele(session)  # deuxième appel
        assert "déjà enregistrée" in capsys.readouterr().out
        assert session.scalar(select(func.count()).select_from(ModelVersion)) == 1


def test_toutes_les_tables_sont_declarees():
    # garde-fou : un modèle ajouté dans db/models.py sans être documenté ici
    assert set(Base.metadata.tables) == TABLES_ATTENDUES
    assert PredictionInput.__tablename__ == "prediction_input"
