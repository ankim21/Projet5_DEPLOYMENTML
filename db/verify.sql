-- VERFICIATION apres db.create_db + db.import_csv
-- Usage : psql "postgresql://<user>:<mot_de_passe>@localhost:5432/futurisys" -f db/verify.sql

\echo '== 1. Tables'
\dt

\echo '== 2. Lignes par table (attendu : 1470 / 1470 / 1470)'
SELECT (SELECT COUNT(*) FROM employee)   AS employee,
       (SELECT COUNT(*) FROM evaluation) AS evaluation,
       (SELECT COUNT(*) FROM sondage)    AS sondage;

\echo '== 3. Jointure des 3 tables = dataset fusionné (attendu : 1470)'
SELECT COUNT(*) AS lignes_jointes
FROM employee e
JOIN evaluation ev USING (id_employee)
JOIN sondage s     USING (id_employee);

\echo '== 4. Aperçu du dataset fusionné'
SELECT e.id_employee, e.age, e.departement, e.poste,
       ev.satisfaction_employee_equipe, ev.augementation_salaire_precedente,
       s.a_quitte_l_entreprise
FROM employee e
JOIN evaluation ev USING (id_employee)
JOIN sondage s     USING (id_employee)
ORDER BY e.id_employee
LIMIT 5;

\echo '== 5. Taux de départ (attendu : 0.161)'
SELECT ROUND(AVG(a_quitte_l_entreprise::int), 3) AS taux_depart FROM sondage;

\echo '== 6. Taux de départ par département'
SELECT e.departement, COUNT(*) AS employes,
       ROUND(AVG(s.a_quitte_l_entreprise::int), 3) AS taux_depart
FROM employee e JOIN sondage s USING (id_employee)
GROUP BY e.departement
ORDER BY taux_depart DESC;

\echo '== 7. Version du modèle enregistrée'
SELECT id_model_version, name, file_path, ROUND(seuil::numeric, 4) AS seuil, created_at
FROM model_version;

\echo '== 8. Les contraintes protègent les données (tentatives annulées)'
DO $$
BEGIN
    UPDATE evaluation SET satisfaction_employee_equipe = 9 WHERE id_employee = 1;
    RAISE EXCEPTION 'PROBLÈME : une note de 9 a été acceptée';
EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'OK : note 9 refusée (CHECK 1-4)';
END $$;

DO $$
BEGIN
    INSERT INTO evaluation (id_employee, satisfaction_employee_environnement,
        note_evaluation_precedente, niveau_hierarchique_poste,
        satisfaction_employee_nature_travail, satisfaction_employee_equipe,
        satisfaction_employee_equilibre_pro_perso, note_evaluation_actuelle,
        heure_supplementaires, augementation_salaire_precedente)
    VALUES (999999, 3, 3, 2, 3, 3, 3, 3, 'Non', 11);
    RAISE EXCEPTION 'PROBLÈME : évaluation acceptée pour un employé inexistant';
EXCEPTION WHEN foreign_key_violation THEN
    RAISE NOTICE 'OK : évaluation d''un employé inexistant refusée (clé étrangère)';
END $$;

DO $$
BEGIN
    INSERT INTO evaluation (id_employee, satisfaction_employee_environnement,
        note_evaluation_precedente, niveau_hierarchique_poste,
        satisfaction_employee_nature_travail, satisfaction_employee_equipe,
        satisfaction_employee_equilibre_pro_perso, note_evaluation_actuelle,
        heure_supplementaires, augementation_salaire_precedente)
    VALUES (1, 3, 3, 2, 3, 3, 3, 3, 'Non', 11);
    RAISE EXCEPTION 'PROBLÈME : deuxième évaluation acceptée pour le même employé';
EXCEPTION WHEN unique_violation THEN
    RAISE NOTICE 'OK : deuxième évaluation du même employé refusée (UNIQUE, relation 1-1)';
END $$;

\echo '== 9. Traçabilité : dernières prédictions (vide tant que /predict n''a pas été appelé)'
SELECT i.id_input, i.created_at, i.source, i.id_employee,
       o.status, ROUND(o.probabilite_depart::numeric, 3) AS proba, o.prediction,
       m.name AS modele, ROUND(m.seuil::numeric, 4) AS seuil
FROM prediction_input i
LEFT JOIN prediction_output o USING (id_input)
LEFT JOIN model_version m USING (id_model_version)
ORDER BY i.created_at DESC
LIMIT 10;
