"""Enchaînement d'une prédiction : base -> modèle -> base. Aucune route ici.

Règle du projet : toute interaction avec le modèle passe par la base. Si la base est
indisponible, on ne prédit pas (503) ; si le modèle échoue, l'échec est enregistré (500).
"""

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas import Employee, Prediction
from db.predictions import enregistrer_prediction, obtenir_version_modele
from modele.pred import MODEL_NAME, MODEL_PATH, predire, seuil


def predire_et_enregistrer(session: Session, employe: Employee) -> Prediction:
    # mode="json" : valeurs simples ("Marié(e)" et non TypeStatutMartial.MARIE)
    entree = employe.model_dump(mode="json")

    # 1. version du modèle : premier accès à la base, donc premier point d'échec possible
    try:
        version = obtenir_version_modele(session, MODEL_NAME, MODEL_PATH.name, seuil)
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "Base de données indisponible : prédiction non effectuée")

    # 2. le modèle ; un échec est enregistré (status="error") avant de répondre
    try:
        probabilite, prediction, label = predire(entree)
    except Exception as exc:
        session.rollback()
        try:
            enregistrer_prediction(
                session, entree, version, erreur=f"{type(exc).__name__}: {exc}"
            )
        except SQLAlchemyError:
            session.rollback()
        raise HTTPException(500, "Erreur du modèle (enregistrée en base)")

    # 3. input + output enregistrés ensemble ; si l'écriture échoue, on ne renvoie rien
    try:
        ligne = enregistrer_prediction(
            session,
            entree,
            version,
            probabilite=probabilite,
            prediction=prediction,
            label=label,
        )
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "Base de données indisponible : prédiction non enregistrée")

    return Prediction(
        id_prediction=ligne.id_input,
        probabilite_depart=probabilite,
        seuil=seuil,
        prediction=prediction,
        label=label,
    )
