from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

#venv/bin/pip install -r requirements.txt
#venv/bin/uvicorn app.main:app --port 7861

app = FastAPI(
    title="Futurisys API",
    description="Prédiction du risque de départ d'un employé",
)

MODEL_PATH = Path(__file__).resolve().parent.parent / "modele_attrition.joblib"
artefact = joblib.load(MODEL_PATH)

pipeline = artefact["pipeline"]
seuil = artefact["seuil"]
colonnes = artefact["colonnes_attendues"]

EXEMPLE_EMPLOYEE = {
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
    "augementation_salaire_precedente_num": 15,
    "proportion_carriere_entreprise": 0.64,
    "experience_avant_entreprise": 4,
    "revenu_par_annee_experience": 590.9,
    "duree_moyenne_postes_precedents": 1.33,
    "taux_promotion": 0.2,
    "stagnation_poste": 0.5,
    "zone_distance": "moyen",
    "jamais_promu": 0,
    "aucune_formation": 0,
    "aucune_participation_pee": 0,
}


class Employee(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [EXEMPLE_EMPLOYEE]})

    age: int = Field(ge=0)
    genre: Literal["F", "M"]
    revenu_mensuel: float = Field(ge=0)
    statut_marital: Literal["Célibataire", "Divorcé(e)", "Marié(e)"]
    departement: Literal["Commercial", "Consulting", "Ressources Humaines"]
    poste: Literal[
        "Assistant de Direction",
        "Cadre Commercial",
        "Consultant",
        "Directeur Technique",
        "Manager",
        "Représentant Commercial",
        "Ressources Humaines",
        "Senior Manager",
        "Tech Lead",
    ]
    nombre_experiences_precedentes: int = Field(ge=0)
    annee_experience_totale: int = Field(ge=0)
    annees_dans_l_entreprise: int = Field(ge=0)
    annees_dans_le_poste_actuel: int = Field(ge=0)
    nombre_participation_pee: int = Field(ge=0)
    nb_formations_suivies: int = Field(ge=0)
    distance_domicile_travail: float = Field(ge=0)
    niveau_education: Literal[1, 2, 3, 4, 5]
    domaine_etude: Literal[
        "Autre",
        "Entrepreunariat",
        "Infra & Cloud",
        "Marketing",
        "Ressources Humaines",
        "Transformation Digitale",
    ]
    frequence_deplacement: Literal["Aucun", "Frequent", "Occasionnel"]
    annees_depuis_la_derniere_promotion: int = Field(ge=0)
    annes_sous_responsable_actuel: int = Field(ge=0)
    satisfaction_employee_environnement: Literal[1, 2, 3, 4]
    note_evaluation_precedente: Literal[1, 2, 3, 4]
    niveau_hierarchique_poste: Literal[1, 2, 3, 4, 5]
    satisfaction_employee_nature_travail: Literal[1, 2, 3, 4]
    satisfaction_employee_equipe: Literal[1, 2, 3, 4]
    satisfaction_employee_equilibre_pro_perso: Literal[1, 2, 3, 4]
    note_evaluation_actuelle: Literal[3, 4]
    heure_supplementaires: Literal["Non", "Oui"]
    augementation_salaire_precedente_num: float
#FEATURE ENGINEERING
    proportion_carriere_entreprise: float
    experience_avant_entreprise: float
    revenu_par_annee_experience: float
    duree_moyenne_postes_precedents: float
    taux_promotion: float
    stagnation_poste: float
    zone_distance: Literal["proche", "moyen", "loin"]
    jamais_promu: int = Field(ge=0, le=1)
    aucune_formation: int = Field(ge=0, le=1)
    aucune_participation_pee: int = Field(ge=0, le=1)


assert set(Employee.model_fields) == set(colonnes), "Employee schema does not match the model's columns"

# ca veut dire que cette classe la va chercher que ca 
class Prediction(BaseModel):
    probabilite_depart: float
    seuil: float
    prediction: int
    label: str

@app.get("/")
def root():
    return {"message": "Futurisys API — voir /docs -- sinon pas d'affichage"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=Prediction)
def predict(employe: Employee):
    X = pd.DataFrame([employe.model_dump()])[colonnes]
    #employe.model_dump() - takes pydantic obj into python dic - panda dtaframe - then ml pipeline 
    proba = float(pipeline.predict_proba(X)[0, 1])
    prediction = int(proba >= seuil)
    return Prediction(
        probabilite_depart=proba,
        seuil=seuil,
        prediction=prediction,
        label="Départ probable" if prediction else "Reste probable",
    )


## NEXT TIME:
# for each dossier, re-organize par dossier 
# la partie app, data, script, tests
# postsqlgre - data = 
# database - je mets tous pydantic; 
# modele - je mets modele

# etape 4: pour postsqlgre - 
# CD 


## hugging face - look at my application without my help -- no local 
