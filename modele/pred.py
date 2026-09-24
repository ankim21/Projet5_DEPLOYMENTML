"""Le modèle : chargement de l'artefact et prédiction. Aucune notion d'API ni de base ici."""

from pathlib import Path

import joblib
import pandas as pd

from modele.features import construire_features

MODEL_PATH = Path(__file__).resolve().parent.parent / "modele_attrition.joblib"
MODEL_NAME = MODEL_PATH.stem  # "modele_attrition"

artefact = joblib.load(MODEL_PATH)
pipeline = artefact["pipeline"]          # encodage + scaler + LinearSVC calibré
seuil = artefact["seuil"]                # seuil choisi à l'entraînement (≠ 0.5)
colonnes = artefact["colonnes_attendues"]  # 37 colonnes brutes + calculées, dans l'ordre


def predire(entree_brute: dict) -> tuple[float, int, str]:
    """Données brutes d'un employé -> (probabilité de départ, prédiction 0/1, label)."""
    X = construire_features(pd.DataFrame([entree_brute]))[colonnes]
    probabilite = float(pipeline.predict_proba(X)[0, 1])
    prediction = int(probabilite >= seuil)
    label = "Départ probable" if prediction else "Reste probable"
    return probabilite, prediction, label
