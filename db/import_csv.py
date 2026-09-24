"""Importe les 3 CSV bruts dans les tables employee, evaluation et sondage.

Usage (depuis la racine du projet, après db.create_db) :
    venv/bin/python -m db.import_csv # refuse si des données existent déjà
    venv/bin/python -m db.import_csv --replace    # remplace les données existantes
"""

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, func, insert, select
from sqlalchemy.orm import Session

from db.models import Employee, Evaluation, Sondage

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def lire_csv(data_dir: Path = DATA_DIR) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return (
        pd.read_csv(data_dir / "extrait_sirh.csv"),
        pd.read_csv(data_dir / "extrait_eval.csv"),
        pd.read_csv(data_dir / "extrait_sondage.csv"),
    )


def preparer_donnees(
    sirh: pd.DataFrame, evaluation: pd.DataFrame, sondage: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Convertit les formats (pas les valeurs) pour coller au schéma."""
    sirh = sirh.copy()
    evaluation = evaluation.copy()
    sondage = sondage.copy()

    # 3 formats d'identifiant -> un seul id_employee entier
    evaluation["id_employee"] = (
        evaluation.pop("eval_number").str.removeprefix("E_").astype(int)
    )
    sondage["id_employee"] = sondage.pop("code_sondage").astype(int)

    # "11 %" -> 11.0
    evaluation["augementation_salaire_precedente"] = (
        evaluation["augementation_salaire_precedente"]
        .str.replace("%", "", regex=False)
        .str.strip()
        .astype(float)
    )

    # "Oui"/"Non" -> True/False (une valeur inconnue devient NaN et est refusée plus bas)
    sondage["a_quitte_l_entreprise"] = sondage["a_quitte_l_entreprise"].map(
        {"Oui": True, "Non": False}
    )
    if sondage["a_quitte_l_entreprise"].isna().any():
        raise ValueError("a_quitte_l_entreprise contient une valeur autre que Oui/Non")

    verifier_identifiants(sirh, evaluation, sondage)
    return sirh, evaluation, sondage


def verifier_identifiants(
    sirh: pd.DataFrame, evaluation: pd.DataFrame, sondage: pd.DataFrame
) -> None:
    """Les 3 fichiers doivent décrire exactement les mêmes employés, une fois chacun."""
    for nom, df in (("sirh", sirh), ("eval", evaluation), ("sondage", sondage)):
        doublons = df["id_employee"].duplicated().sum()
        if doublons:
            raise ValueError(f"{nom} : {doublons} id_employee en double")

    ids_sirh = set(sirh["id_employee"])
    for nom, df in (("eval", evaluation), ("sondage", sondage)):
        ids = set(df["id_employee"])
        if ids != ids_sirh:
            raise ValueError(
                f"{nom} ne correspond pas à sirh : "
                f"{len(ids - ids_sirh)} id en trop, {len(ids_sirh - ids)} id manquants"
            )


def inserer(
    session: Session,
    sirh: pd.DataFrame,
    evaluation: pd.DataFrame,
    sondage: pd.DataFrame,
    replace: bool = False,
) -> None:
    """Tout ou rien : si une ligne est refusée (CHECK, FK...), rien n'est inséré."""
    deja = session.scalar(select(func.count()).select_from(Employee))
    if deja and not replace:
        raise RuntimeError(
            f"{deja} employés déjà en base : relancer avec --replace pour les remplacer"
        )

    if deja:
        # ordre inverse des clés étrangères ; les prediction_input gardent leur
        # historique (id_employee passe à NULL grâce à ON DELETE SET NULL)
        session.execute(delete(Sondage))
        session.execute(delete(Evaluation))
        session.execute(delete(Employee))

    # employee d'abord : evaluation et sondage y font référence
    session.execute(insert(Employee), sirh.to_dict("records"))
    session.execute(insert(Evaluation), evaluation.to_dict("records"))
    session.execute(insert(Sondage), sondage.to_dict("records"))
    session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace", action="store_true", help="remplace les données déjà importées"
    )
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()

    # import ici : db.database exige DATABASE_URL, inutile pour les tests
    from db.database import SessionLocal

    sirh, evaluation, sondage = preparer_donnees(*lire_csv(args.data_dir))
    with SessionLocal() as session:
        try:
            inserer(session, sirh, evaluation, sondage, replace=args.replace)
        except Exception:
            session.rollback()
            raise
    print(
        f"Importé : {len(sirh)} employee, {len(evaluation)} evaluation, "
        f"{len(sondage)} sondage"
    )


if __name__ == "__main__":
    main()
