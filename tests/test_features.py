"""Tests unitaires du feature engineering : les formules du notebook, sans API ni base."""

import math

import pandas as pd
import pytest

from app.schemas import EXEMPLE_EMPLOYEE, Employee
from modele.features import COLONNES_BRUTES, construire_features
from modele.pred import colonnes


def features(**modifs):
    return construire_features(pd.DataFrame([{**EXEMPLE_EMPLOYEE, **modifs}])).iloc[0]


def test_formules():
    # exemple : 11 ans d'expérience dont 7 dans l'entreprise, 3 postes avant, promo il y a 2 ans
    f = features()
    assert f["augementation_salaire_precedente_num"] == 15
    assert f["proportion_carriere_entreprise"] == pytest.approx(7 / 12)
    assert f["experience_avant_entreprise"] == 4
    assert f["revenu_par_annee_experience"] == pytest.approx(6500 / 12)
    assert f["duree_moyenne_postes_precedents"] == pytest.approx(4 / 4)
    assert f["taux_promotion"] == pytest.approx(2 / 8)
    assert f["stagnation_poste"] == pytest.approx(4 / 8)
    assert f["zone_distance"] == "moyen"
    assert (f["jamais_promu"], f["aucune_formation"], f["aucune_participation_pee"]) == (0, 0, 0)


def test_zeros_sans_division_par_zero():
    f = features(
        annee_experience_totale=0,
        annees_dans_l_entreprise=0,
        nombre_experiences_precedentes=0,
        annees_depuis_la_derniere_promotion=0,
        nb_formations_suivies=0,
        nombre_participation_pee=0,
    )
    for col in ["proportion_carriere_entreprise", "revenu_par_annee_experience",
                "duree_moyenne_postes_precedents", "taux_promotion", "stagnation_poste"]:
        assert math.isfinite(f[col]), col
    assert (f["jamais_promu"], f["aucune_formation"], f["aucune_participation_pee"]) == (1, 1, 1)


@pytest.mark.parametrize(
    "distance, zone",
    [(1, "proche"), (5, "proche"), (5.5, "moyen"), (15, "moyen"), (15.5, "loin"), (30, "loin")],
)
def test_zone_distance_bornes(distance, zone):
    assert features(distance_domicile_travail=distance)["zone_distance"] == zone


@pytest.mark.parametrize("distance", [0, 31])
def test_zone_distance_hors_bornes_vide(distance):
    # comme à l'entraînement (pd.cut) : hors ]0, 30] -> valeur vide
    assert pd.isna(features(distance_domicile_travail=distance)["zone_distance"])


def test_colonnes_du_modele_toutes_produites():
    produites = construire_features(pd.DataFrame([EXEMPLE_EMPLOYEE]))
    assert set(colonnes) <= set(produites.columns)
    assert list(Employee.model_fields) == COLONNES_BRUTES


def test_entree_non_modifiee():
    brut = pd.DataFrame([EXEMPLE_EMPLOYEE])
    avant = brut.copy()
    construire_features(brut)
    pd.testing.assert_frame_equal(brut, avant)
