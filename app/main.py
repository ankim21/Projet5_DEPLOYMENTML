"""API.py is only the application
app/schemas.py (entrées/sorties), app/service.py (enchaînement),app/dependencies.py (session), 
modele/ (modèle et features), db/ (base de données).
"""

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.dependencies import get_session
from app.schemas import Employee, Prediction
from app.service import predire_et_enregistrer

app = FastAPI(
    title="Futurisys API",
    description="Prédiction du risque de départ d'un employé",
)


@app.get("/")
def root():
    return {"message": "Futurisys API — voir /docs -- sinon pas d'affichage"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=Prediction)
def predict(employe: Employee, session: Session = Depends(get_session)) -> Prediction:
    return predire_et_enregistrer(session, employe)
