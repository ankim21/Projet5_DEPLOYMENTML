import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import Base, ModelVersion, PredictionInput, PredictionOutput

# SQLite en mémoire : teste le schéma sans serveur PostgreSQL (CI)

INPUT_BRUT = {
    "age": 37,
    "genre": "M",
    "revenu_mensuel": 6500,
    "statut_marital": "Marié(e)",
    "departement": "Consulting",
    "poste": "Consultant",
    "nombre_experiences_precedentes": 3,
    "annee_experience_totale": 11,
    "annees_dans_l_entreprise": 7,
    "annees_dans_le_poste_actuel": 4,
    "nombre_participation_pee": 1,
    "nb_formations_suivies": 3,
    "distance_domicile_travail": 9,
    "niveau_education": 3,
    "domaine_etude": "Infra & Cloud",
    "frequence_deplacement": "Occasionnel",
    "annees_depuis_la_derniere_promotion": 2,
    "annes_sous_responsable_actuel": 4,
    "satisfaction_employee_environnement": 3,
    "note_evaluation_precedente": 3,
    "niveau_hierarchique_poste": 2,
    "satisfaction_employee_nature_travail": 3,
    "satisfaction_employee_equipe": 3,
    "satisfaction_employee_equilibre_pro_perso": 3,
    "note_evaluation_actuelle": 3,
    "heure_supplementaires": "Non",
    "augementation_salaire_precedente": 15,
}


@pytest.fixture
def session():
    engine = create_engine("sqlite://")

    # SQLite n'applique les clés étrangères que si on l'active
    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def version(session):
    v = ModelVersion(name="modele_attrition", file_path="modele.joblib", seuil=0.29)
    session.add(v)
    session.commit()
    return v


def test_input_et_output_lies(session, version):
    entree = PredictionInput(**INPUT_BRUT)
    entree.output = PredictionOutput(
        model_version=version, probabilite_depart=0.42, prediction=1, label="Départ probable"
    )
    session.add(entree)
    session.commit()

    assert entree.id_employee is None
    assert entree.created_at is not None
    assert entree.output.input is entree
    assert version.outputs == [entree.output]


def test_categorie_inconnue_refusee(session):
    session.add(PredictionInput(**{**INPUT_BRUT, "departement": "Marketing"}))
    with pytest.raises(IntegrityError):
        session.commit()


def test_valeur_negative_refusee(session):
    session.add(PredictionInput(**{**INPUT_BRUT, "revenu_mensuel": -100}))
    with pytest.raises(IntegrityError):
        session.commit()


def test_un_seul_output_par_input(session, version):
    entree = PredictionInput(**INPUT_BRUT)
    session.add(entree)
    session.commit()

    for _ in range(2):
        session.add(
            PredictionOutput(
                id_input=entree.id_input, model_version=version,
                probabilite_depart=0.1, prediction=0,
            )
        )
    with pytest.raises(IntegrityError):
        session.commit()


def test_erreur_sans_message_refusee(session, version):
    entree = PredictionInput(**INPUT_BRUT)
    entree.output = PredictionOutput(model_version=version, status="error")
    session.add(entree)
    with pytest.raises(IntegrityError):
        session.commit()


def test_erreur_avec_message_acceptee(session, version):
    entree = PredictionInput(**INPUT_BRUT)
    entree.output = PredictionOutput(
        model_version=version, status="error", error_message="pipeline a planté"
    )
    session.add(entree)
    session.commit()
    assert entree.output.prediction is None
