"""Écritures liées au modèle : version du modèle et journal des prédictions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import ModelVersion, PredictionInput, PredictionOutput


def obtenir_version_modele(
    session: Session, name: str, file_path: str, seuil: float
) -> ModelVersion:
    """Renvoie la version du model, making her si elle n'existe pas encore."""
    version = session.scalar(
        select(ModelVersion).where(
            ModelVersion.name == name,
            ModelVersion.file_path == file_path,
            ModelVersion.seuil == seuil,
        )
    )
    if version is None:
        version = ModelVersion(name=name, file_path=file_path, seuil=seuil)
        session.add(version)
        session.flush()  # envoie l'INSERT pour obtenir id_model_version
    return version


def enregistrer_prediction(
    session: Session,
    entree_brute: dict,
    version: ModelVersion,
    *,
    probabilite: float | None = None,
    prediction: int | None = None,
    label: str | None = None,
    erreur: str | None = None,
    source: str = "api",
    id_employee: int | None = None,
) -> PredictionInput:
    """Enregistre l'input ET son output dans une seule transaction (tout ou rien).
    Succès : probabilite + prediction renseignees. echec du modele : erreur renseignee.
    """
    entree = PredictionInput(**entree_brute, source=source, id_employee=id_employee)
    entree.output = PredictionOutput(
        model_version=version,
        probabilite_depart=probabilite,
        prediction=prediction,
        label=label,
        status="error" if erreur else "success",
        error_message=erreur,
    )
    session.add(entree)
    session.commit()  # SQLAlchemy envoie les 2 INSERT : prediction_input and then prediction_output
    return entree
