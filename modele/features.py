"""Feature engineering : one function used by API

Formules taken that are ID to the notebook 
Si une formule change ici, the model must be retrained with same functions :
sinon l'API calcule des features differentes de celles apprises (training/serving skew).
"""

import pandas as pd

# colonnes brutes attendues en entree (memes qu prediction_input)
COLONNES_BRUTES = [
    "age",
    "genre",
    "revenu_mensuel",
    "statut_marital",
    "departement",
    "poste",
    "nombre_experiences_precedentes",
    "annee_experience_totale",
    "annees_dans_l_entreprise",
    "annees_dans_le_poste_actuel",
    "nombre_participation_pee",
    "nb_formations_suivies",
    "distance_domicile_travail",
    "niveau_education",
    "domaine_etude",
    "frequence_deplacement",
    "annees_depuis_la_derniere_promotion",
    "annes_sous_responsable_actuel",
    "satisfaction_employee_environnement",
    "note_evaluation_precedente",
    "niveau_hierarchique_poste",
    "satisfaction_employee_nature_travail",
    "satisfaction_employee_equipe",
    "satisfaction_employee_equilibre_pro_perso",
    "note_evaluation_actuelle",
    "heure_supplementaires",
    "augementation_salaire_precedente",
]


def construire_features(brut: pd.DataFrame) -> pd.DataFrame:
    """Donnees brutes (une ligne par employe) -> colonnes attendues par le pipeline."""
    df = brut.copy()

    df["augementation_salaire_precedente_num"] = df.pop("augementation_salaire_precedente")

    df["proportion_carriere_entreprise"] = (
        df["annees_dans_l_entreprise"] / (df["annee_experience_totale"] + 1)
    )
    df["experience_avant_entreprise"] = (
        df["annee_experience_totale"] - df["annees_dans_l_entreprise"]
    )
    df["revenu_par_annee_experience"] = (
        df["revenu_mensuel"] / (df["annee_experience_totale"] + 1)
    )
    df["duree_moyenne_postes_precedents"] = (
        df["experience_avant_entreprise"] / (df["nombre_experiences_precedentes"] + 1)
    )
    df["taux_promotion"] = (
        df["annees_depuis_la_derniere_promotion"] / (df["annees_dans_l_entreprise"] + 1)
    )
    df["stagnation_poste"] = (
        df["annees_dans_le_poste_actuel"] / (df["annees_dans_l_entreprise"] + 1)
    )

    df["zone_distance"] = pd.cut(
        df["distance_domicile_travail"],
        bins=[0, 5, 15, 30],
        labels=["proche", "moyen", "loin"],
    )
    
    df["jamais_promu"] = (df["annees_depuis_la_derniere_promotion"] == 0).astype(int)
    df["aucune_formation"] = (df["nb_formations_suivies"] == 0).astype(int)
    df["aucune_participation_pee"] = (df["nombre_participation_pee"] == 0).astype(int)

    return df
