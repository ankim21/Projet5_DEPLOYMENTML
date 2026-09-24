"""What the API needs: ce que le client envoie (Employee) et ce qu'il reçoit (Prediction).

Pydantic = validation des échanges HTTP. À ne pas confondre avec db/models.py (SQLAlchemy),
qui décrit les tables.
"""

from enum import Enum
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from modele.features import COLONNES_BRUTES, construire_features
from modele.pred import colonnes

# données BRUTES uniquement : les 10 features calculées le sont par modele/features.py
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
    "augementation_salaire_precedente": 15,
}

# ENUM CLASSES========================================================

class TypeStatutMartial(str, Enum):
    CELIBATAIRE = "Célibataire"
    DIVORCE = "Divorcé(e)"
    MARIE = "Marié(e)"

class TypeDepartment(str, Enum):
    COMMERICIAL = "Commercial"
    CONSULTING = "Consulting"
    HR = "Ressources Humaines"

class TypePost(str, Enum):
    ASSDIRECTION = "Assistant de Direction"
    COMM = "Cadre Commercial"
    CONSULT ="Consultant"
    DIRTECH = "Directeur Technique"
    MANAGER ="Manager"
    COMMREP = "Représentant Commercial"
    HR = "Ressources Humaines"
    SENMANAGER = "Senior Manager"
    TECHLEAD = "Tech Lead"

class TypeEtude (str, Enum):
    AUTRE = "Autre"
    ENTREPRENDRE = "Entrepreunariat"
    INFRA = "Infra & Cloud"
    MARKETING = "Marketing"
    HR = "Ressources Humaines"
    DIGITALE = "Transformation Digitale"
# ========================================================

class Employee(BaseModel):
    """Entrée de /predict : les 27 champs bruts."""

    # extra="forbid" : envoyer une feature calculée (ex. taux_promotion) est refusé,
    # c'est l'API qui la calcule -> pas de valeur contradictoire avec les données brutes
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [EXEMPLE_EMPLOYEE]}
    )

    age: int = Field(ge=0)
    genre: Literal["F", "M"]
    revenu_mensuel: float = Field(ge=0)
    statut_marital: TypeStatutMartial
    departement: TypeDepartment
    poste: TypePost
    nombre_experiences_precedentes: int = Field(ge=0)
    annee_experience_totale: int = Field(ge=0)
    annees_dans_l_entreprise: int = Field(ge=0)
    annees_dans_le_poste_actuel: int = Field(ge=0)
    nombre_participation_pee: int = Field(ge=0)
    nb_formations_suivies: int = Field(ge=0)
    distance_domicile_travail: float = Field(ge=0)
    niveau_education: Literal[1, 2, 3, 4, 5]
    domaine_etude: TypeEtude
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
    augementation_salaire_precedente: float = Field(
        ge=0, description="en %, ex. 15 pour 15 %"
    )


class Prediction(BaseModel):
    """Sortie de /predict."""

    id_prediction: int  # = prediction_input.id_input : retrouver l'échange en base
    probabilite_depart: float
    seuil: float
    prediction: int
    label: str


# sanity check : l'API, les features et le modèle doivent parler des mêmes colonnes
assert list(Employee.model_fields) == COLONNES_BRUTES, \
    "Employee ne correspond pas aux colonnes brutes"
assert set(colonnes) <= set(construire_features(pd.DataFrame([EXEMPLE_EMPLOYEE])).columns), \
    "construire_features ne produit pas toutes les colonnes attendues par le modèle"
