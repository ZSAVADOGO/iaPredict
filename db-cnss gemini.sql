-- Nettoyage de la base de données de test
DROP DATABASE IF EXISTS db_cnss;
CREATE DATABASE db_cnss CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_cnss;

-- 1. Table Employeur (Informations administratives et statut de cotisation)
CREATE TABLE employeur (
    id_employeur INT AUTO_INCREMENT PRIMARY KEY,
    numero_employeur VARCHAR(20) UNIQUE NOT NULL, -- Numéro d'immatriculation CNSS
    raison_sociale VARCHAR(150) NOT NULL,
    dirigeant_legal VARCHAR(100) NOT NULL,
    situation_cotisant VARCHAR(30) NOT NULL COMMENT 'A_JOUR, EN_RETARD, CONTENTIEUX',
    telephone VARCHAR(20),
    ville VARCHAR(50) DEFAULT 'Ouagadougou',
    date_immatriculation DATE NOT NULL
);

-- 2. Table Travailleur (Assuré principal de la CNSS)
CREATE TABLE travailleur (
    numero_assure VARCHAR(13) PRIMARY KEY, -- Contrainte : 12 chiffres + 1 lettre
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE NOT NULL,
	numero_cnib VARCHAR(100) NOT NULL,
    sexe CHAR(1) NOT NULL CHECK (sexe IN ('M', 'F')),
    situation_matrimoniale VARCHAR(20) DEFAULT 'CELIBATAIRE',
    telephone VARCHAR(20),
    date_immatriculation DATE NOT NULL,
    CONSTRAINT chk_numero_assure CHECK (numero_assure REGEXP '^[0-9]{12}[A-Z]$')
);

-- 3. Table Emploi (Historique des postes, salaires et lien avec l'employeur)
CREATE TABLE emploi (
    id_emploi INT AUTO_INCREMENT PRIMARY KEY,
    numero_assure VARCHAR(13) NOT NULL,
    id_employeur INT NOT NULL,
    poste VARCHAR(100) NOT NULL,
    salaire_de_base DECIMAL(12,2) NOT NULL,
    indemnites DECIMAL(12,2) DEFAULT 0.00,
    date_debut DATE NOT NULL,
    date_fin DATE NULL, -- NULL si emploi actuel
    statut_emploi VARCHAR(20) DEFAULT 'ACTIF',
    FOREIGN KEY (numero_assure) REFERENCES travailleur(numero_assure) ON DELETE CASCADE,
    FOREIGN KEY (id_employeur) REFERENCES employeur(id_employeur) ON DELETE RESTRICT
);

-- 4. Table Ayant-Droit (Conjoints et Enfants rattachés pour les prestations)
CREATE TABLE ayant_droit (
    id_ayant_droit INT AUTO_INCREMENT PRIMARY KEY,
    numero_assure VARCHAR(13) NOT NULL,
    type_ayant_droit VARCHAR(10) NOT NULL CHECK (type_ayant_droit IN ('CONJOINT', 'ENFANT')),
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE NOT NULL,
    sexe CHAR(1) NOT NULL CHECK (sexe IN ('M', 'F')),
    date_rattachement DATE NOT NULL,
    FOREIGN KEY (numero_assure) REFERENCES travailleur(numero_assure) ON DELETE CASCADE
);

-- 5. Table Cotisation (Calculée mensuellement sur la base du salaire déclaré)
CREATE TABLE cotisation (
    id_cotisation INT AUTO_INCREMENT PRIMARY KEY,
    id_emploi INT NOT NULL,
    periode_mois_annee VARCHAR(7) NOT NULL, -- Format 'MM-YYYY'
    assiette_cotisable DECIMAL(12,2) NOT NULL, -- Salaire brut plafonné ou non
    part_ouvriere DECIMAL(12,2) NOT NULL, -- Part prélevée sur le salarié
    part_patronale DECIMAL(12,2) NOT NULL, -- Part payée par l'employeur
    date_versement DATE NULL,
    FOREIGN KEY (id_emploi) REFERENCES emploi(id_emploi) ON DELETE CASCADE
);

--Procedure stockée afin de generer des donnees

DELIMITER $$

DROP PROCEDURE IF EXISTS GenererBigDataCNSS$$

CREATE PROCEDURE GenererBigDataCNSS()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE random_sexe CHAR(1);
    DECLARE random_nom VARCHAR(50);
    DECLARE random_prenom VARCHAR(50);
    DECLARE v_numero_assure VARCHAR(13);
    
    -- 1. Désactiver les contraintes pour purger proprement vos 5 tables réelles
    SET FOREIGN_KEY_CHECKS = 0;
    TRUNCATE TABLE cotisation;
    TRUNCATE TABLE ayant_droit;
    TRUNCATE TABLE emploi;
    TRUNCATE TABLE travailleur;
    TRUNCATE TABLE employeur;
    SET FOREIGN_KEY_CHECKS = 1;

    -- =================================================================
    -- 1. INSERTION DE 100 EMPLOYEURS
    -- =================================================================
    SET i = 1;
    WHILE i <= 100 DO
        INSERT INTO employeur (
            numero_employeur, raison_sociale, dirigeant_legal, 
            situation_cotisant, telephone, ville, date_immatriculation
        ) VALUES (
            CONCAT('EMP-', LPAD(i, 4, '0'), '-BF'),
            CONCAT('SOCIETE_EXEMPLE_', i),
            CONCAT('Dirigeant_', i),
            ELT(FLOOR(1 + RAND() * 5), 'A_JOUR', 'A_JOUR', 'A_JOUR', 'EN_RETARD', 'CONTENTIEUX'),
            CONCAT('+22625', LPAD(FLOOR(RAND() * 999999), 6, '0')),
            ELT(FLOOR(1 + RAND() * 4), 'Ouagadougou', 'Bobo-Dioulasso', 'Koudougou', 'Kaya'),
            DATE_SUB('2026-01-01', INTERVAL FLOOR(500 + RAND() * 3000) DAY)
        );
        SET i = i + 1;
    END WHILE;

    -- =================================================================
    -- 2. INSERTION DE 200 TRAVAILLEURS
    -- =================================================================
    SET i = 1;
    WHILE i <= 200 DO
        SET random_sexe = IF(RAND() > 0.4, 'M', 'F'); 
        SET random_nom = ELT(FLOOR(1 + RAND() * 6), 'OUEDRAOGO', 'TRAORE', 'SANON', 'ZOUNDI', 'KABORE', 'SAWADOGO');
        SET random_prenom = IF(random_sexe = 'M', 
            ELT(FLOOR(1 + RAND() * 5), 'Ibrahim', 'Pierre', 'Seydou', 'Adama', 'Ousmane'),
            ELT(FLOOR(1 + RAND() * 5), 'Fatoumata', 'Mariam', 'Clarisse', 'Chantal', 'Awa')
        );
        
        -- Respect strict de la contrainte : 12 chiffres + 1 lettre
        SET v_numero_assure = CONCAT(LPAD(i, 12, '0'), ELT(FLOOR(1 + RAND() * 4), 'A', 'B', 'C', 'D'));

        INSERT INTO travailleur (
            numero_assure, nom, prenom, date_naissance, 
            numero_cnib, sexe, situation_matrimoniale, telephone, date_immatriculation
        ) VALUES (
            v_numero_assure,
            random_nom,
            random_prenom,
            DATE_SUB('2006-01-01', INTERVAL FLOOR(RAND() * 12000) DAY),
            CONCAT('B', LPAD(i, 8, '0')),
            random_sexe,
            ELT(FLOOR(1 + RAND() * 3), 'MARIE', 'CELIBATAIRE', 'DIVORCE'),
            CONCAT('+22670', LPAD(FLOOR(RAND() * 999999), 6, '0')),
            DATE_SUB('2026-01-01', INTERVAL FLOOR(200 + RAND() * 1500) DAY)
        );
        SET i = i + 1;
    END WHILE;

    -- =================================================================
    -- 3. INSERTION DE 200 EMPLOIS
    -- =================================================================
    INSERT INTO emploi (id_emploi, numero_assure, id_employeur, poste, salaire_de_base, indemnites, date_debut, date_fin, statut_emploi)
    SELECT 
        @row_num := @row_num + 1 AS id_emploi,
        t.numero_assure,
        FLOOR(1 + RAND() * 100) AS id_employeur,
        ELT(FLOOR(1 + RAND() * 6), 'Directeur', 'Ingénieur', 'Technicien', 'Comptable', 'Secrétaire', 'Chauffeur'),
        FLOOR(120000 + (RAND() * 680000)),
        FLOOR(30000 + (RAND() * 50000)),
        '2025-01-01',
        NULL,
        'ACTIF'
    FROM travailleur t
    CROSS JOIN (SELECT @row_num := 0) r;

    -- =================================================================
    -- 4. INSERTION DE 600 COTISATIONS (Historique Temporel de 3 mois)
    -- =================================================================
    SET i = 1;
    WHILE i <= 200 DO
        -- Mars 2026
        INSERT INTO cotisation (id_emploi, periode_mois_annee, assiette_cotisable, part_ouvriere, part_patronale, date_versement)
        SELECT id_emploi, '03-2026', (salaire_de_base + indemnites), (salaire_de_base + indemnites) * 0.055, (salaire_de_base + indemnites) * 0.16, '2026-04-05'
        FROM emploi WHERE id_emploi = i;

        -- Avril 2026
        INSERT INTO cotisation (id_emploi, periode_mois_annee, assiette_cotisable, part_ouvriere, part_patronale, date_versement)
        SELECT id_emploi, '04-2026', (salaire_de_base + indemnites), (salaire_de_base + indemnites) * 0.055, (salaire_de_base + indemnites) * 0.16, '2026-05-05'
        FROM emploi WHERE id_emploi = i;

        -- Mai 2026
        INSERT INTO cotisation (id_emploi, periode_mois_annee, assiette_cotisable, part_ouvriere, part_patronale, date_versement)
        SELECT id_emploi, '05-2026', (salaire_de_base + indemnites), (salaire_de_base + indemnites) * 0.055, (salaire_de_base + indemnites) * 0.16, '2026-06-05'
        FROM emploi WHERE id_emploi = i;

        SET i = i + 1;
    END WHILE;

    -- =================================================================
    -- 5. INSERTION DE 600 AYANTS DROIT
    -- =================================================================
    SET i = 1;
    WHILE i <= 600 DO
        INSERT INTO ayant_droit (numero_assure, type_ayant_droit, nom, prenom, date_naissance, sexe, date_rattachement)
        SELECT 
            numero_assure,
            IF(i % 3 = 0, 'CONJOINT', 'ENFANT'),
            nom,
            CONCAT('AyantDroit_', i),
            IF(i % 3 = 0, DATE_SUB(CURRENT_DATE(), INTERVAL FLOOR(20 + RAND() * 15) YEAR), DATE_SUB(CURRENT_DATE(), INTERVAL FLOOR(RAND() * 15) YEAR)),
            IF(RAND() > 0.5, 'M', 'F'),
            DATE_SUB('2026-06-01', INTERVAL FLOOR(RAND() * 300) DAY)
        FROM travailleur
        WHERE numero_assure = CONCAT(LPAD(FLOOR(1 + RAND() * 200), 12, '0'), (SELECT RIGHT(numero_assure, 1) FROM travailleur LIMIT 1 OFFSET 0))
        LIMIT 1;
        
        -- Fallback de secours si l'index aléatoire tape à côté
        IF ROW_COUNT() = 0 THEN
            INSERT INTO ayant_droit (numero_assure, type_ayant_droit, nom, prenom, date_naissance, sexe, date_rattachement)
            SELECT numero_assure, 'ENFANT', nom, CONCAT('AyantDroit_Secours_', i), '2018-05-12', 'F', CURRENT_DATE()
            FROM travailleur LIMIT 1;
        END IF;

        SET i = i + 1;
    END WHILE;

END$$

DELIMITER ;

-- Exécution directe
CALL GenererBigDataCNSS();

-- Nettoyage de la mémoire
DROP PROCEDURE GenererBigDataCNSS;