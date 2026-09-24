"""Tests de l'API : les routes, avec une base de test (tests d'intégration légers)."""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

import modele.pred as pred
from app.dependencies import get_session
from app.main import app
from app.schemas import EXEMPLE_EMPLOYEE
from db.models import ModelVersion, PredictionInput, PredictionOutput
from modele.pred import seuil
from tests.conftest import moteur_sqlite


def compter(db, modele):
    return db.scalar(select(func.count()).select_from(modele))


def test_root(client):
    assert client.get("/").status_code == 200


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_ok(client):
    response = client.post("/predict", json=EXEMPLE_EMPLOYEE)
    assert response.status_code == 200

    body = response.json()
    assert 0 <= body["probabilite_depart"] <= 1
    assert body["seuil"] == seuil
    assert body["prediction"] == int(body["probabilite_depart"] >= seuil)
    assert body["id_prediction"] >= 1


# TRAÇABILITÉ ===========================================================


def test_predict_enregistre_input_et_output(client, db):
    body = client.post("/predict", json=EXEMPLE_EMPLOYEE).json()

    entree = db.get(PredictionInput, body["id_prediction"])
    assert entree is not None
    assert entree.source == "api"
    assert entree.id_employee is None
    assert entree.created_at is not None
    # les données brutes reçues sont stockées telles quelles
    for champ, valeur in EXEMPLE_EMPLOYEE.items():
        assert getattr(entree, champ) == valeur, champ

    sortie = entree.output
    assert sortie.status == "success"
    assert sortie.probabilite_depart == body["probabilite_depart"]
    assert sortie.prediction == body["prediction"]
    assert sortie.label == body["label"]
    assert sortie.model_version.seuil == seuil


def test_chaque_appel_est_trace_meme_version(client, db):
    ids = [client.post("/predict", json=EXEMPLE_EMPLOYEE).json()["id_prediction"] for _ in range(3)]

    assert len(set(ids)) == 3
    assert compter(db, PredictionInput) == 3
    assert compter(db, PredictionOutput) == 3
    assert compter(db, ModelVersion) == 1  # la version est réutilisée, pas dupliquée


def test_erreur_du_modele_enregistree(client, db, monkeypatch):
    class PipelineEnPanne:
        def predict_proba(self, X):
            raise ValueError("pipeline en panne")

    monkeypatch.setattr(pred, "pipeline", PipelineEnPanne())
    response = client.post("/predict", json=EXEMPLE_EMPLOYEE)

    assert response.status_code == 500
    sortie = db.scalar(select(PredictionOutput))
    assert sortie.status == "error"
    assert "pipeline en panne" in sortie.error_message
    assert sortie.probabilite_depart is None
    assert sortie.input.age == EXEMPLE_EMPLOYEE["age"]  # l'input n'est pas perdu


def test_base_indisponible_pas_de_prediction():
    # base sans tables : toute lecture/écriture échoue
    factory = sessionmaker(bind=moteur_sqlite(creer_tables=False))

    def session_cassee():
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = session_cassee
    try:
        response = TestClient(app).post("/predict", json=EXEMPLE_EMPLOYEE)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503


# VALIDATION (rien n'atteint le modèle, donc rien n'est enregistré) =====


def test_predict_categorie_inconnue(client, db):
    payload = {**EXEMPLE_EMPLOYEE, "departement": "Marketing"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert compter(db, PredictionInput) == 0


def test_predict_champ_manquant(client):
    payload = {k: v for k, v in EXEMPLE_EMPLOYEE.items() if k != "age"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_valeur_negative(client):
    payload = {**EXEMPLE_EMPLOYEE, "revenu_mensuel": -100}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_feature_calculee_refusee(client):
    # l'API calcule elle-même taux_promotion : l'envoyer est une erreur
    payload = {**EXEMPLE_EMPLOYEE, "taux_promotion": 0.9}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
