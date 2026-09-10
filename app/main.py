from fastapi import FastAPI
from pathlib import Path
import joblib

MODEL_PATH = Path(__file__).parent / "modele_attrition.joblib"
artefact = joblib.load(MODEL_PATH)

pipeline = artefact["pipeline"]
seuil = artefact["seuil"]
colonnes = artefact["colonnes_attendues"]