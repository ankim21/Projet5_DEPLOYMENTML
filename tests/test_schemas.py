"""Tests unitaires du contrat de l'API : validation Pydantic, sans HTTP."""

import pytest
from pydantic import ValidationError

from app.schemas import EXEMPLE_EMPLOYEE, Employee, Prediction


def test_exemple_valide():
    employe = Employee(**EXEMPLE_EMPLOYEE)
    # model_dump(mode="json") : valeurs simples, prêtes pour la base et pandas
    assert employe.model_dump(mode="json") == EXEMPLE_EMPLOYEE


@pytest.mark.parametrize(
    "champ, valeur",
    [
        ("departement", "Marketing"),          # catégorie jamais vue à l'entraînement
        ("genre", "X"),
        ("poste", "Stagiaire"),
        ("domaine_etude", "Cuisine"),
        ("frequence_deplacement", "Parfois"),
        ("heure_supplementaires", "oui"),      # sensible à la casse
        ("niveau_education", 6),               # échelle 1-5
        ("satisfaction_employee_equipe", 0),   # échelle 1-4
        ("note_evaluation_actuelle", 2),       # le modèle n'a vu que 3 et 4
        ("age", -1),
        ("revenu_mensuel", -100),
        ("distance_domicile_travail", -5),
        ("augementation_salaire_precedente", -1),
    ],
)
def test_valeurs_refusees(champ, valeur):
    with pytest.raises(ValidationError):
        Employee(**{**EXEMPLE_EMPLOYEE, champ: valeur})


def test_champ_manquant_refuse():
    with pytest.raises(ValidationError):
        Employee(**{k: v for k, v in EXEMPLE_EMPLOYEE.items() if k != "age"})


def test_feature_calculee_refusee():
    # extra="forbid" : c'est l'API qui calcule ces colonnes
    for champ in ["taux_promotion", "zone_distance", "augementation_salaire_precedente_num"]:
        with pytest.raises(ValidationError):
            Employee(**{**EXEMPLE_EMPLOYEE, champ: 1})


def test_prediction_sortie():
    sortie = Prediction(
        id_prediction=1, probabilite_depart=0.42, seuil=0.29, prediction=1, label="Départ probable"
    )
    assert sortie.model_dump() == {
        "id_prediction": 1,
        "probabilite_depart": 0.42,
        "seuil": 0.29,
        "prediction": 1,
        "label": "Départ probable",
    }
