from fastapi.testclient import TestClient

from app.main import EXEMPLE_EMPLOYEE, app, seuil

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_ok():
    response = client.post("/predict", json=EXEMPLE_EMPLOYEE)
    assert response.status_code == 200

    body = response.json()
    assert 0 <= body["probabilite_depart"] <= 1
    assert body["seuil"] == seuil
    assert body["prediction"] == int(body["probabilite_depart"] >= seuil)


def test_predict_categorie_inconnue():
    payload = {**EXEMPLE_EMPLOYEE, "departement": "Marketing"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_champ_manquant():
    payload = {k: v for k, v in EXEMPLE_EMPLOYEE.items() if k != "age"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_valeur_negative():
    payload = {**EXEMPLE_EMPLOYEE, "revenu_mensuel": -100}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
