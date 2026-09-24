
# SCHEMA  : voir docs/db_schema.md
# Tranforms all my tables in Python to SQL 
## SQLAlchemy is an ORM (Object-Relational Mapper): you write Python 
# — classes, method calls, objects — and it translates that into SQL statements to send to Postgres, 
# then translates the SQL results back into Python objects for you to use.
#Each Python class is one table, and each attribute is one column
# model is a python class that maps to table ; base is shared regsitry 


from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

#every model inherits from it so SQL Alchemy knows what tables exist
class Base(DeclarativeBase):
    pass


# VALEURS AUTORISÉES ===================================================
# mêmes valeurs que les Enum/Literal de app/main.py (celles vues à l'entraînement)

GENRES = ("F", "M")
STATUTS_MARITAUX = ("Célibataire", "Divorcé(e)", "Marié(e)")
DEPARTEMENTS = ("Commercial", "Consulting", "Ressources Humaines")
POSTES = (
    "Assistant de Direction",
    "Cadre Commercial",
    "Consultant",
    "Directeur Technique",
    "Manager",
    "Représentant Commercial",
    "Ressources Humaines",
    "Senior Manager",
    "Tech Lead",
)
DOMAINES_ETUDE = (
    "Autre",
    "Entrepreunariat",
    "Infra & Cloud",
    "Marketing",
    "Ressources Humaines",
    "Transformation Digitale",
)
FREQUENCES_DEPLACEMENT = ("Aucun", "Frequent", "Occasionnel")
OUI_NON = ("Oui", "Non")
STATUTS_PREDICTION = ("success", "error")


def check_in(colonne: str, valeurs: tuple[str, ...]) -> CheckConstraint:
    """CHECK colonne IN (...) : PostgreSQL refuse toute valeur hors liste."""
    liste = ", ".join("'" + v.replace("'", "''") + "'" for v in valeurs)
    return CheckConstraint(f"{colonne} IN ({liste})", name=f"ck_{colonne}")


def check_entre(colonne: str, mini: int, maxi: int) -> CheckConstraint:
    return CheckConstraint(
        f"{colonne} BETWEEN {mini} AND {maxi}", name=f"ck_{colonne}"
    )


def check_positif(*colonnes: str) -> list[CheckConstraint]:
    return [CheckConstraint(f"{c} >= 0", name=f"ck_{c}_positif") for c in colonnes]

#DATASET BRUUUUT

class Employee(Base):
    """extrait_sirh.csv """

    __tablename__ = "employee"
    __table_args__ = (
        check_in("genre", GENRES),
        check_in("statut_marital", STATUTS_MARITAUX),
        check_in("departement", DEPARTEMENTS),
        check_in("poste", POSTES),
        *check_positif(
            "age",
            "revenu_mensuel",
            "nombre_experiences_precedentes",
            "annee_experience_totale",
            "annees_dans_l_entreprise",
            "annees_dans_le_poste_actuel",
        ),
    )

    # id venant des CSV (pas de SERIAL) : c'est la clé qui relie les 3 fichiers
    id_employee: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    age: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(1))
    revenu_mensuel: Mapped[float] = mapped_column(Float)
    statut_marital: Mapped[str] = mapped_column(String(20))
    departement: Mapped[str] = mapped_column(String(50))
    poste: Mapped[str] = mapped_column(String(50))
    nombre_experiences_precedentes: Mapped[int] = mapped_column(Integer)
    nombre_heures_travailless: Mapped[int | None] = mapped_column(Integer)
    annee_experience_totale: Mapped[int] = mapped_column(Integer)
    annees_dans_l_entreprise: Mapped[int] = mapped_column(Integer)
    annees_dans_le_poste_actuel: Mapped[int] = mapped_column(Integer)

    evaluation: Mapped["Evaluation"] = relationship(back_populates="employee")
    sondage: Mapped["Sondage"] = relationship(back_populates="employee")


class Evaluation(Base):
    """extrait_eval.csv """

    __tablename__ = "evaluation"
    __table_args__ = (
        check_entre("satisfaction_employee_environnement", 1, 4),
        check_entre("note_evaluation_precedente", 1, 4),
        check_entre("niveau_hierarchique_poste", 1, 5),
        check_entre("satisfaction_employee_nature_travail", 1, 4),
        check_entre("satisfaction_employee_equipe", 1, 4),
        check_entre("satisfaction_employee_equilibre_pro_perso", 1, 4),
        check_entre("note_evaluation_actuelle", 1, 4),
        check_in("heure_supplementaires", OUI_NON),
    )

    id_evaluation: Mapped[int] = mapped_column(Integer, primary_key=True)
    # unique=True => un employé a au plus une évaluation (relation 1-1)
    id_employee: Mapped[int] = mapped_column(
        ForeignKey("employee.id_employee", ondelete="CASCADE"), unique=True
    )
    satisfaction_employee_environnement: Mapped[int] = mapped_column(Integer)
    note_evaluation_precedente: Mapped[int] = mapped_column(Integer)
    niveau_hierarchique_poste: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_nature_travail: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equipe: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equilibre_pro_perso: Mapped[int] = mapped_column(Integer)
    note_evaluation_actuelle: Mapped[int] = mapped_column(Integer)
    heure_supplementaires: Mapped[str] = mapped_column(String(3))
    # "11 %" dans le CSV -> 11.0 à l'insertion
    augementation_salaire_precedente: Mapped[float] = mapped_column(Float)

    employee: Mapped[Employee] = relationship(back_populates="evaluation")


class Sondage(Base):
    """extrait_sondage.csv"""

    __tablename__ = "sondage"
    __table_args__ = (
        check_entre("niveau_education", 1, 5),
        check_in("domaine_etude", DOMAINES_ETUDE),
        check_in("frequence_deplacement", FREQUENCES_DEPLACEMENT),
        *check_positif(
            "nombre_participation_pee",
            "nb_formations_suivies",
            "nombre_employee_sous_responsabilite",
            "distance_domicile_travail",
            "annees_depuis_la_derniere_promotion",
            "annes_sous_responsable_actuel",
        ),
    )

    id_sondage: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_employee: Mapped[int] = mapped_column(
        ForeignKey("employee.id_employee", ondelete="CASCADE"), unique=True
    )
    a_quitte_l_entreprise: Mapped[bool] = mapped_column(Boolean)  # CIBLE
    nombre_participation_pee: Mapped[int] = mapped_column(Integer)
    nb_formations_suivies: Mapped[int] = mapped_column(Integer)
    nombre_employee_sous_responsabilite: Mapped[int | None] = mapped_column(Integer)
    distance_domicile_travail: Mapped[float] = mapped_column(Float)
    niveau_education: Mapped[int] = mapped_column(Integer)
    domaine_etude: Mapped[str] = mapped_column(String(50))
    ayant_enfants: Mapped[str | None] = mapped_column(String(3))
    frequence_deplacement: Mapped[str] = mapped_column(String(20))
    annees_depuis_la_derniere_promotion: Mapped[int] = mapped_column(Integer)
    annes_sous_responsable_actuel: Mapped[int] = mapped_column(Integer)

    employee: Mapped[Employee] = relationship(back_populates="sondage")


# TRACABILITE DU MODELE ================================================


class ModelVersion(Base):
    """Quel fichier modele / quel seuil a produit une prediction."""

    __tablename__ = "model_version"

    id_model_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(String(255))
    seuil: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    outputs: Mapped[list["PredictionOutput"]] = relationship(
        back_populates="model_version"
    )


class PredictionInput(Base):
    __tablename__ = "prediction_input"
    __table_args__ = (
        check_in("genre", GENRES),
        check_in("statut_marital", STATUTS_MARITAUX),
        check_in("departement", DEPARTEMENTS),
        check_in("poste", POSTES),
        check_in("domaine_etude", DOMAINES_ETUDE),
        check_in("frequence_deplacement", FREQUENCES_DEPLACEMENT),
        check_in("heure_supplementaires", OUI_NON),
        check_entre("niveau_education", 1, 5),
        check_entre("satisfaction_employee_environnement", 1, 4),
        check_entre("note_evaluation_precedente", 1, 4),
        check_entre("niveau_hierarchique_poste", 1, 5),
        check_entre("satisfaction_employee_nature_travail", 1, 4),
        check_entre("satisfaction_employee_equipe", 1, 4),
        check_entre("satisfaction_employee_equilibre_pro_perso", 1, 4),
        check_entre("note_evaluation_actuelle", 1, 4),
        *check_positif(
            "age",
            "revenu_mensuel",
            "nombre_experiences_precedentes",
            "annee_experience_totale",
            "annees_dans_l_entreprise",
            "annees_dans_le_poste_actuel",
            "nombre_participation_pee",
            "nb_formations_suivies",
            "distance_domicile_travail",
            "annees_depuis_la_derniere_promotion",
            "annes_sous_responsable_actuel",
        ),
    )

    id_input: Mapped[int] = mapped_column(Integer, primary_key=True)
    # NULL si l'employé est hypothétique (body JSON), rempli si /predict/{id}
    id_employee: Mapped[int | None] = mapped_column(
        ForeignKey("employee.id_employee", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    source: Mapped[str] = mapped_column(String(20), default="api")

    # sirh
    age: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(1))
    revenu_mensuel: Mapped[float] = mapped_column(Float)
    statut_marital: Mapped[str] = mapped_column(String(20))
    departement: Mapped[str] = mapped_column(String(50))
    poste: Mapped[str] = mapped_column(String(50))
    nombre_experiences_precedentes: Mapped[int] = mapped_column(Integer)
    annee_experience_totale: Mapped[int] = mapped_column(Integer)
    annees_dans_l_entreprise: Mapped[int] = mapped_column(Integer)
    annees_dans_le_poste_actuel: Mapped[int] = mapped_column(Integer)
    # sondage
    nombre_participation_pee: Mapped[int] = mapped_column(Integer)
    nb_formations_suivies: Mapped[int] = mapped_column(Integer)
    distance_domicile_travail: Mapped[float] = mapped_column(Float)
    niveau_education: Mapped[int] = mapped_column(Integer)
    domaine_etude: Mapped[str] = mapped_column(String(50))
    frequence_deplacement: Mapped[str] = mapped_column(String(20))
    annees_depuis_la_derniere_promotion: Mapped[int] = mapped_column(Integer)
    annes_sous_responsable_actuel: Mapped[int] = mapped_column(Integer)
    # evaluation
    satisfaction_employee_environnement: Mapped[int] = mapped_column(Integer)
    note_evaluation_precedente: Mapped[int] = mapped_column(Integer)
    niveau_hierarchique_poste: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_nature_travail: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equipe: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equilibre_pro_perso: Mapped[int] = mapped_column(Integer)
    note_evaluation_actuelle: Mapped[int] = mapped_column(Integer)
    heure_supplementaires: Mapped[str] = mapped_column(String(3))
    augementation_salaire_precedente: Mapped[float] = mapped_column(Float)

    output: Mapped["PredictionOutput | None"] = relationship(back_populates="input")


class PredictionOutput(Base):
    """Résultat du modèle pour un input (ou l'erreur rencontrée)."""

    __tablename__ = "prediction_output"
    __table_args__ = (
        check_in("status", STATUTS_PREDICTION),
        CheckConstraint(
            "probabilite_depart IS NULL OR probabilite_depart BETWEEN 0 AND 1",
            name="ck_probabilite_depart",
        ),
        CheckConstraint(
            "prediction IS NULL OR prediction IN (0, 1)", name="ck_prediction"
        ),
        # un succès doit avoir un résultat, une erreur doit avoir un message
        CheckConstraint(
            "(status = 'success' AND probabilite_depart IS NOT NULL"
            " AND prediction IS NOT NULL)"
            " OR (status = 'error' AND error_message IS NOT NULL)",
            name="ck_status_coherent",
        ),
    )

    id_output: Mapped[int] = mapped_column(Integer, primary_key=True)
    # unique=True => exactement un output par input
    id_input: Mapped[int] = mapped_column(
        ForeignKey("prediction_input.id_input", ondelete="CASCADE"), unique=True
    )
    id_model_version: Mapped[int] = mapped_column(
        ForeignKey("model_version.id_model_version"), index=True
    )
    probabilite_depart: Mapped[float | None] = mapped_column(Float)
    prediction: Mapped[int | None] = mapped_column(Integer)
    label: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(10), default="success")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    input: Mapped[PredictionInput] = relationship(back_populates="output")
    model_version: Mapped[ModelVersion] = relationship(back_populates="outputs")
