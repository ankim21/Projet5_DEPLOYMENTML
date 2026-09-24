"""Tests unitaires du modèle : modele/pred.py, sans API ni base."""

import numpy as np
import pytest

import modele.pred as pred
from app.schemas import EXEMPLE_EMPLOYEE
from modele.pred import MODEL_NAME, colonnes, predire, seuil


def test_artefact_charge():
    assert MODEL_NAME == "modele_attrition"
    assert 0 < seuil < 1
    assert len(colonnes) == 37


def test_predire_exemple():
    probabilite, prediction, label = predire(EXEMPLE_EMPLOYEE)

    assert 0 <= probabilite <= 1
    assert prediction == int(probabilite >= seuil)
    assert label == ("Départ probable" if prediction else "Reste probable")


@pytest.mark.parametrize(
    "proba_simulee, prediction_attendue, label_attendu",
    [(0.9, 1, "Départ probable"), (0.01, 0, "Reste probable")],
)
def test_seuil_decide_la_prediction(monkeypatch, proba_simulee, prediction_attendue, label_attendu):
    """Le seuil de l'artefact (≈0.29), et non 0.5, transforme la probabilité en 0/1."""

    class PipelineSimule:
        def predict_proba(self, X):
            return np.array([[1 - proba_simulee, proba_simulee]])

    monkeypatch.setattr(pred, "pipeline", PipelineSimule())
    probabilite, prediction, label = predire(EXEMPLE_EMPLOYEE)

    assert probabilite == pytest.approx(proba_simulee)
    assert (prediction, label) == (prediction_attendue, label_attendu)


def test_predire_champ_brut_manquant():
    incomplet = {k: v for k, v in EXEMPLE_EMPLOYEE.items() if k != "age"}
    with pytest.raises(KeyError):
        predire(incomplet)


def test_heure_supplementaires_change_le_resultat():
    """Vérifie que le pipeline tient compte d'une modalité catégorielle (non ignorée)."""
    sans = predire({**EXEMPLE_EMPLOYEE, "heure_supplementaires": "Non"})[0]
    avec = predire({**EXEMPLE_EMPLOYEE, "heure_supplementaires": "Oui"})[0]
    assert sans != avec
