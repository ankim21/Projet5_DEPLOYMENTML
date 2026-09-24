import pandas as pd
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.import_csv import inserer, preparer_donnees
from db.models import Base, Employee, Evaluation, Sondage

# petits DataFrames au format des vrais CSV (les CSV sont hors git)

def faux_csv(ids=(1, 2)):
    sirh = pd.DataFrame(
        {
            "id_employee": list(ids),
            "age": 41,
            "genre": "F",
            "revenu_mensuel": 5993,
            "statut_marital": "Célibataire",
            "departement": "Commercial",
            "poste": "Cadre Commercial",
            "nombre_experiences_precedentes": 8,
            "nombre_heures_travailless": 80,
            "annee_experience_totale": 8,
            "annees_dans_l_entreprise": 6,
            "annees_dans_le_poste_actuel": 4,
        }
    )
    evaluation = pd.DataFrame(
        {
            "satisfaction_employee_environnement": 2,
            "note_evaluation_precedente": 3,
            "niveau_hierarchique_poste": 2,
            "satisfaction_employee_nature_travail": 4,
            "satisfaction_employee_equipe": 1,
            "satisfaction_employee_equilibre_pro_perso": 1,
            "eval_number": [f"E_{i}" for i in ids],
            "note_evaluation_actuelle": 3,
            "heure_supplementaires": "Oui",
            "augementation_salaire_precedente": "11 %",
        }
    )
    sondage = pd.DataFrame(
        {
            "a_quitte_l_entreprise": ["Oui", "Non"][: len(ids)],
            "nombre_participation_pee": 0,
            "nb_formations_suivies": 0,
            "nombre_employee_sous_responsabilite": 1,
            "code_sondage": list(ids),
            "distance_domicile_travail": 1,
            "niveau_education": 2,
            "domaine_etude": "Infra & Cloud",
            "ayant_enfants": "Y",
            "frequence_deplacement": "Occasionnel",
            "annees_depuis_la_derniere_promotion": 0,
            "annes_sous_responsable_actuel": 5,
        }
    )
    return sirh, evaluation, sondage


@pytest.fixture
def session():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def compter(session, modele):
    return session.scalar(select(func.count()).select_from(modele))


def test_conversions():
    _, evaluation, sondage = preparer_donnees(*faux_csv())
    assert list(evaluation["id_employee"]) == [1, 2]
    assert "eval_number" not in evaluation
    assert list(sondage["id_employee"]) == [1, 2]
    assert "code_sondage" not in sondage
    assert evaluation["augementation_salaire_precedente"].tolist() == [11.0, 11.0]
    assert sondage["a_quitte_l_entreprise"].tolist() == [True, False]


def test_identifiants_differents_refuses():
    sirh, evaluation, sondage = faux_csv()
    evaluation["eval_number"] = ["E_1", "E_99"]
    with pytest.raises(ValueError, match="eval ne correspond pas"):
        preparer_donnees(sirh, evaluation, sondage)


def test_cible_inconnue_refusee():
    sirh, evaluation, sondage = faux_csv()
    sondage["a_quitte_l_entreprise"] = ["Oui", "Peut-être"]
    with pytest.raises(ValueError, match="Oui/Non"):
        preparer_donnees(sirh, evaluation, sondage)


def test_insertion(session):
    inserer(session, *preparer_donnees(*faux_csv()))
    assert [compter(session, m) for m in (Employee, Evaluation, Sondage)] == [2, 2, 2]
    employe = session.get(Employee, 2)
    assert employe.evaluation.augementation_salaire_precedente == 11.0
    assert employe.sondage.a_quitte_l_entreprise is False


def test_deuxieme_import_refuse_sans_replace(session):
    donnees = preparer_donnees(*faux_csv())
    inserer(session, *donnees)
    with pytest.raises(RuntimeError, match="--replace"):
        inserer(session, *donnees)


def test_replace_remplace(session):
    inserer(session, *preparer_donnees(*faux_csv(ids=(1, 2))))
    inserer(session, *preparer_donnees(*faux_csv(ids=(7, 8))), replace=True)
    assert session.get(Employee, 1) is None
    assert compter(session, Employee) == 2


def test_tout_ou_rien(session):
    sirh, evaluation, sondage = preparer_donnees(*faux_csv())
    evaluation.loc[1, "satisfaction_employee_equipe"] = 9  # hors 1-4
    with pytest.raises(IntegrityError):
        inserer(session, sirh, evaluation, sondage)
    session.rollback()
    assert compter(session, Employee) == 0
